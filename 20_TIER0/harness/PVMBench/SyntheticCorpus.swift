import Foundation
import Photos
import UIKit

/// DEC-009 — reaching 30k/100k without transferring 50–200 GB to a phone.
///
/// SAFETY, and this is not boilerplate: this code writes to a REAL photo library.
/// Cleanup deletes ONLY assets this harness created, tracked by localIdentifier in
/// its own table. It can never touch anything pre-existing. Prove insertion AND
/// cleanup on a secondary device with a disposable library before any primary
/// device is used. This is the project's own no-silent-deletion red line (P-03)
/// applied to its own tooling.
enum SyntheticCorpus {

    static let albumName = "PVMBench Synthetic (safe to delete)"

    /// Realistic PIXEL DIMENSIONS with heavy compression: decode cost tracks pixel
    /// count, so throughput stays honest, while storage stays ~500 KB/asset.
    /// Generating small images would flatter the benchmark.
    static func makeImage(index: Int, textLike: Bool) -> UIImage {
        let size = CGSize(width: 4032, height: 3024)
        let fmt = UIGraphicsImageRendererFormat.default()
        fmt.scale = 1
        let renderer = UIGraphicsImageRenderer(size: size, format: fmt)
        return renderer.image { ctx in
            let c = ctx.cgContext
            if textLike {
                // Screenshot-like: flat background plus text rows, so the OCR gate
                // sees a realistic proportion of text-bearing assets (C-1).
                c.setFillColor(UIColor.white.cgColor)
                c.fill(CGRect(origin: .zero, size: size))
                let attrs: [NSAttributedString.Key: Any] = [
                    .font: UIFont.systemFont(ofSize: 64),
                    .foregroundColor: UIColor.black
                ]
                for row in 0..<22 {
                    let s = "Item \(index)-\(row)  code \(1000 + (index * 7 + row) % 8999)  status ok"
                    s.draw(at: CGPoint(x: 120, y: 140 + row * 120), withAttributes: attrs)
                }
            } else {
                // Photo-like: gradient plus noise blocks, giving non-trivial dHash
                // and feature-print work rather than a flat image the encoder skips.
                let colors = [UIColor(hue: CGFloat(index % 100) / 100.0, saturation: 0.6,
                                      brightness: 0.9, alpha: 1).cgColor,
                              UIColor(hue: CGFloat((index * 3) % 100) / 100.0, saturation: 0.5,
                                      brightness: 0.4, alpha: 1).cgColor]
                if let g = CGGradient(colorsSpace: CGColorSpaceCreateDeviceRGB(),
                                      colors: colors as CFArray, locations: [0, 1]) {
                    c.drawLinearGradient(g, start: .zero,
                                         end: CGPoint(x: size.width, y: size.height), options: [])
                }
                var seed = UInt64(index &* 2654435761)
                for _ in 0..<400 {
                    seed = seed &* 6364136223846793005 &+ 1442695040888963407
                    let x = CGFloat((seed >> 16) % UInt64(size.width))
                    let y = CGFloat((seed >> 32) % UInt64(size.height))
                    c.setFillColor(UIColor(white: CGFloat((seed >> 8) % 255) / 255.0, alpha: 0.35).cgColor)
                    c.fill(CGRect(x: x, y: y, width: 90, height: 90))
                }
            }
        }
    }

    /// `screenshotRatio` should approximate the device's real library so the OCR
    /// gate ratio is not artificially flattered.
    static func insert(count: Int, screenshotRatio: Double, store: IndexStore,
                       progress: @escaping (Int) -> Void,
                       completion: @escaping (Int, Error?) -> Void) {
        var inserted = 0
        let batchSize = 50

        func writeBatch(_ start: Int) {
            guard start < count else { completion(inserted, nil); return }
            let end = min(start + batchSize, count)
            var newIDs: [String] = []

            PHPhotoLibrary.shared().performChanges({
                for i in start..<end {
                    let textLike = Double(i % 100) / 100.0 < screenshotRatio
                    let img = makeImage(index: i, textLike: textLike)
                    guard let data = img.jpegData(compressionQuality: 0.35) else { continue }
                    let req = PHAssetCreationRequest.forAsset()
                    req.addResource(with: .photo, data: data, options: nil)
                    if let ph = req.placeholderForCreatedAsset {
                        newIDs.append(ph.localIdentifier)
                    }
                }
            }, completionHandler: { ok, err in
                if ok {
                    // Track BEFORE anything else can run, so an interruption can
                    // never orphan an asset we created but cannot identify later.
                    for id in newIDs { store.recordSynthetic(id) }
                    inserted += newIDs.count
                    DispatchQueue.main.async { progress(inserted) }
                    writeBatch(end)
                } else {
                    completion(inserted, err)
                }
            })
        }
        writeBatch(0)
    }

    /// Deletes ONLY tracked synthetic assets. Never enumerates the library to guess.
    /// iOS shows the user a confirmation sheet for deletions — that is expected and
    /// is itself a V-2 observation worth recording.
    static func cleanup(store: IndexStore, completion: @escaping (Int, Error?) -> Void) {
        let ids = store.syntheticIDs()
        guard !ids.isEmpty else { completion(0, nil); return }

        let fetched = PHAsset.fetchAssets(withLocalIdentifiers: ids, options: nil)
        var toDelete: [PHAsset] = []
        fetched.enumerateObjects { a, _, _ in toDelete.append(a) }
        guard !toDelete.isEmpty else { store.forgetSynthetic(ids); completion(0, nil); return }

        PHPhotoLibrary.shared().performChanges({
            PHAssetChangeRequest.deleteAssets(toDelete as NSArray)
        }, completionHandler: { ok, err in
            if ok { store.forgetSynthetic(ids) }
            DispatchQueue.main.async { completion(ok ? toDelete.count : 0, err) }
        })
    }
}
