import CoreGraphics
import Foundation
#if canImport(UIKit)
import UIKit
#endif
import Photos
import Vision

/// The depth pass: thumbnail → hash → gated OCR → scene labels → faces.
///
/// **C-1: OCR is gated, not universal.** Running text recognition over 100k assets is
/// the single most likely cause of an A1 failure. The gate keys on cheap signals only
/// and must never itself decode a full-resolution image.
///
/// **C-2: index from thumbnails, never originals,** with network access denied. On an
/// iCloud-optimised library, requesting an original measures the user's Wi-Fi.
///
/// The T0-A scale sweep measured this path at 105–154 ms/asset on a Simulator with no
/// Neural Engine, where the embedding dominated at 84% and OCR cost 6%. That inverts
/// C-1's prediction and is recorded as IN DOUBT rather than settled: the embedding is
/// exactly the stage an ANE would accelerate.
public enum VisionSignals {

    public static let thumbnailSize = CGSize(width: 256, height: 256)

    public struct Result {
        public var dhash: UInt64?
        public var ocrRan = false
        public var ocrText = ""
        public var sceneLabels: [SceneLabel] = []
        public var faceCount = 0
        public var failed = false
        public var iCloudOnly = false
    }

    #if canImport(UIKit)
    public static func enrich(asset: PHAsset, base: AssetSignals) -> Result {
        var result = Result()
        let options = PHImageRequestOptions()
        options.isNetworkAccessAllowed = false      // C-2 — non-negotiable
        options.deliveryMode = .fastFormat
        options.resizeMode = .exact
        options.isSynchronous = true

        var image: UIImage?
        PHImageManager.default().requestImage(for: asset, targetSize: thumbnailSize,
                                              contentMode: .aspectFit, options: options) { img, info in
            image = img
            result.iCloudOnly = (info?[PHImageResultIsInCloudKey] as? Bool) ?? false
        }
        guard let thumb = image, let cg = thumb.cgImage else {
            // Record the miss rather than dropping it: the proportion of assets with no
            // usable local thumbnail is itself a headline §6 finding.
            result.failed = true
            return result
        }

        result.dhash = ImageSignals.dHash(cg)
        let likelihood = ImageSignals.textLikelihood(cg)

        if shouldRunOCR(base: base, textLikelihood: likelihood) {
            result.ocrRan = true
            result.ocrText = recogniseText(cg)
        }
        result.sceneLabels = classifyScene(cg)
        result.faceCount = countFaces(cg)
        return result
    }
    #endif

    /// C-1. Cheap signals only — this must never itself decode a full-resolution image.
    public static func shouldRunOCR(base: AssetSignals, textLikelihood: Double) -> Bool {
        if base.isScreenshot { return true }
        if base.pixelW > 0, base.pixelH > 0 {
            let ar = Double(base.pixelH) / Double(base.pixelW)
            if ar > 1.6, ar < 2.4 { return true }     // screen-shaped
        }
        return textLikelihood > 0.55
    }

    /// `.fast` is deliberate: throughput feasibility is the question, and the accuracy
    /// of recognised text is a Tier 1 concern.
    public static func recogniseText(_ cg: CGImage) -> String {
        let request = VNRecognizeTextRequest()
        request.recognitionLevel = .fast
        request.usesLanguageCorrection = false
        let handler = VNImageRequestHandler(cgImage: cg, options: [:])
        do {
            try handler.perform([request])
            guard let observations = request.results else { return "" }
            return observations.compactMap { $0.topCandidates(1).first?.string }
                .joined(separator: " ")
        } catch {
            return ""
        }
    }

    /// Apple-native scene classification: bundles no model and adds zero bytes to the
    /// binary, which is the route L1-B §6 says to test first.
    public static func classifyScene(_ cg: CGImage, limit: Int = 6) -> [SceneLabel] {
        let request = VNClassifyImageRequest()
        let handler = VNImageRequestHandler(cgImage: cg, options: [:])
        do {
            try handler.perform([request])
            guard let observations = request.results else { return [] }
            return observations
                .filter { $0.confidence >= Float(Rules.sceneFloor) }
                .prefix(limit)
                .map { SceneLabel(identifier: $0.identifier, confidence: Double($0.confidence)) }
        } catch {
            return []
        }
    }

    /// Face *detection* only. Clustering and naming are the user's, and an unnamed
    /// cluster is still enough to stop treating a photo as disposable.
    public static func countFaces(_ cg: CGImage) -> Int {
        let request = VNDetectFaceRectanglesRequest()
        let handler = VNImageRequestHandler(cgImage: cg, options: [:])
        do {
            try handler.perform([request])
            return request.results?.count ?? 0
        } catch {
            return 0
        }
    }
}

/// The cheap pixel signals, kept apart from Vision so they can be unit-tested without
/// a photo library.
public enum ImageSignals {

    /// 64-bit difference hash on a 9x8 grayscale reduction.
    ///
    /// FC-1a lives here: this returns 0 both for an image with no bright-to-dark
    /// horizontal step *and* whenever the context cannot be made. Callers must treat 0
    /// as a miss, never as a value — `AssetSignals.hasUsableDHash` is that guard.
    public static func dHash(_ cg: CGImage) -> UInt64 {
        let w = 9, h = 8
        var pixels = [UInt8](repeating: 0, count: w * h)
        let space = CGColorSpaceCreateDeviceGray()
        guard let ctx = CGContext(data: &pixels, width: w, height: h, bitsPerComponent: 8,
                                  bytesPerRow: w, space: space,
                                  bitmapInfo: CGImageAlphaInfo.none.rawValue) else { return 0 }
        ctx.draw(cg, in: CGRect(x: 0, y: 0, width: w, height: h))
        var hash: UInt64 = 0
        var bit = 0
        for y in 0..<h {
            for x in 0..<(w - 1) {
                if pixels[y * w + x] > pixels[y * w + x + 1] { hash |= (1 << UInt64(bit)) }
                bit += 1
            }
        }
        return hash
    }

    /// "How texty does this look" — used only by the OCR gate. High horizontal edge
    /// density plus a flat background is characteristic of text-bearing screenshots.
    /// Deliberately crude: it must cost far less than OCR or the gate is pointless.
    public static func textLikelihood(_ cg: CGImage) -> Double {
        let w = 32, h = 32
        var px = [UInt8](repeating: 0, count: w * h)
        let space = CGColorSpaceCreateDeviceGray()
        guard let ctx = CGContext(data: &px, width: w, height: h, bitsPerComponent: 8,
                                  bytesPerRow: w, space: space,
                                  bitmapInfo: CGImageAlphaInfo.none.rawValue) else { return 0 }
        ctx.draw(cg, in: CGRect(x: 0, y: 0, width: w, height: h))

        var edges = 0
        for y in 0..<h {
            for x in 0..<(w - 1) {
                if abs(Int(px[y * w + x]) - Int(px[y * w + x + 1])) > 40 { edges += 1 }
            }
        }
        let density = Double(edges) / Double(w * (h - 1))
        var histogram = [Int](repeating: 0, count: 16)
        for v in px { histogram[Int(v) >> 4] += 1 }
        let peak = Double(histogram.max() ?? 0) / Double(px.count)
        return min(1.0, density * 1.5 + peak * 0.5)
    }
}
