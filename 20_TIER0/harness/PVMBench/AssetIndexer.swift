import Foundation
import Photos
import UIKit

/// Per-asset pipeline: L1 signals -> gated OCR -> L2 embedding.
/// C-2: thumbnails only, network access DENIED. Requesting originals on an
/// iCloud-optimised library would measure the user's Wi-Fi instead of the phone
/// and could produce a spurious A1 failure that falsely kills the project.
final class AssetIndexer {

    struct Counters {
        var ocrAttempted = 0
        var ocrGatedOut = 0
        var embedAttempted = 0
        var icloudFetchRequired = 0
        var icloudFetchSkipped = 0
        var failed = 0
        var ocrTotalMS: Double = 0
        var embedTotalMS: Double = 0
    }

    private let store: IndexStore
    private let manager = PHImageManager.default()
    private(set) var counters = Counters()
    private let targetSize = CGSize(width: 256, height: 256)

    init(store: IndexStore) { self.store = store }

    func resetCounters() { counters = Counters() }

    func index(asset: PHAsset, isSynthetic: Bool) {
        var rec = Layer1.metadata(from: asset, isSynthetic: isSynthetic)

        let opts = PHImageRequestOptions()
        opts.isNetworkAccessAllowed = false        // C-2 — non-negotiable
        opts.deliveryMode = .fastFormat
        opts.resizeMode = .exact
        opts.isSynchronous = true

        var image: UIImage?
        var degraded = false
        var cloudOnly = false

        manager.requestImage(for: asset, targetSize: targetSize,
                             contentMode: .aspectFit, options: opts) { img, info in
            image = img
            degraded = (info?[PHImageResultIsDegradedKey] as? Bool) ?? false
            // True when the asset is not available locally and network was denied.
            cloudOnly = (info?[PHImageResultIsInCloudKey] as? Bool) ?? false
        }

        if cloudOnly {
            counters.icloudFetchRequired += 1
            rec.icloudOnly = true
        } else {
            counters.icloudFetchSkipped += 1
        }

        guard let img = image else {
            // Record the miss rather than dropping it silently — the proportion of
            // assets with no usable local thumbnail is itself a headline §6 finding.
            counters.failed += 1
            store.upsert(rec)
            return
        }

        rec.dhash = Layer1.dHash(img)
        let likelihood = Layer1.textLikelihood(img)

        let decision = OCRGate.decide(record: rec, textLikelihood: likelihood)
        if decision.run {
            let t0 = CFAbsoluteTimeGetCurrent()
            rec.ocrText = OCRGate.recognise(img)
            counters.ocrTotalMS += (CFAbsoluteTimeGetCurrent() - t0) * 1000
            rec.ocrRan = true
            counters.ocrAttempted += 1
        } else {
            counters.ocrGatedOut += 1
        }

        let t1 = CFAbsoluteTimeGetCurrent()
        rec.embedding = EmbeddingStage.featurePrint(img)
        counters.embedTotalMS += (CFAbsoluteTimeGetCurrent() - t1) * 1000
        counters.embedAttempted += 1

        _ = degraded
        store.upsert(rec)
    }
}
