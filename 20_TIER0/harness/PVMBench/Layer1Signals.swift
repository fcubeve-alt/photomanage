import Foundation
import Photos
import UIKit
import CoreLocation

/// Constitution §25 Layer 1 — cheap signals only. No taxonomy, no entity
/// resolution, no risk scoring (those are Tier 1/2 and are NOT in this harness).
enum Layer1 {

    static func metadata(from asset: PHAsset, isSynthetic: Bool) -> AssetRecord {
        var r = AssetRecord(localID: asset.localIdentifier)
        r.createdAt = asset.creationDate?.timeIntervalSince1970 ?? 0
        r.modifiedAt = asset.modificationDate?.timeIntervalSince1970 ?? 0
        if let loc = asset.location {
            r.lat = loc.coordinate.latitude
            r.lon = loc.coordinate.longitude
            // §11: an inferred location must carry confidence. A GPS fix from the
            // asset itself is direct evidence, so confidence is 1.0 here. Anything
            // inferred from neighbours later must NOT reuse this value.
            r.locConfidence = 1.0
        }
        r.mediaType = asset.mediaType.rawValue
        r.isScreenshot = asset.mediaSubtypes.contains(.photoScreenshot)
        r.isSynthetic = isSynthetic
        r.pxW = asset.pixelWidth
        r.pxH = asset.pixelHeight
        return r
    }

    /// 64-bit difference hash on an 9x8 grayscale reduction.
    /// Cheap, rotation-intolerant, good enough for exact/near-duplicate candidates.
    static func dHash(_ image: UIImage) -> UInt64 {
        let w = 9, h = 8
        guard let cg = image.cgImage else { return 0 }
        var pixels = [UInt8](repeating: 0, count: w * h)
        let cs = CGColorSpaceCreateDeviceGray()
        guard let ctx = CGContext(data: &pixels, width: w, height: h, bitsPerComponent: 8,
                                  bytesPerRow: w, space: cs,
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

    /// Cheap "how texty does this look" proxy, used only by the OCR gate (C-1).
    /// High horizontal edge density + low colour variance is characteristic of
    /// text-bearing screenshots. Deliberately crude: it must cost far less than OCR
    /// or the gate is pointless.
    static func textLikelihood(_ image: UIImage) -> Double {
        let w = 32, h = 32
        guard let cg = image.cgImage else { return 0 }
        var px = [UInt8](repeating: 0, count: w * h)
        let cs = CGColorSpaceCreateDeviceGray()
        guard let ctx = CGContext(data: &px, width: w, height: h, bitsPerComponent: 8,
                                  bytesPerRow: w, space: cs,
                                  bitmapInfo: CGImageAlphaInfo.none.rawValue) else { return 0 }
        ctx.draw(cg, in: CGRect(x: 0, y: 0, width: w, height: h))

        var edges = 0
        for y in 0..<h {
            for x in 0..<(w - 1) {
                if abs(Int(px[y*w+x]) - Int(px[y*w+x+1])) > 40 { edges += 1 }
            }
        }
        let density = Double(edges) / Double(w * (h - 1))

        // Flat-background bonus: screenshots have large uniform regions.
        var hist = [Int](repeating: 0, count: 16)
        for v in px { hist[Int(v) >> 4] += 1 }
        let peak = Double(hist.max() ?? 0) / Double(px.count)

        return min(1.0, density * 1.5 + peak * 0.5)
    }
}
