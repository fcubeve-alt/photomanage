import Foundation
import Photos
import UIKit

/// §7 V-1…V-5. Cheap to run once the harness exists, expensive to discover late.
/// V-5 is the most important item in the entire harness: the Constitution's whole
/// automation argument (§7 — tolerate low-cost RECOVERABLE errors) is only valid if
/// errors actually are recoverable. Verify it; never assume it.
enum PhotoKitProbes {

    struct Result: Codable {
        var authorizationStatus = ""
        var isLimitedLibrary = false
        var totalAssetsVisible = 0
        var smartAlbumRecentlyDeletedExists = false     // V-5
        var deletionRequiresConfirmation = "REQUIRES MANUAL OBSERVATION"  // V-2
        var changeObserverFired = false                 // V-3
        var cloudOnlyAssetsSampled = 0                  // V-4
        var cloudOnlyThumbnailUsable = 0                // V-4
        var notes: [String] = []
    }

    static func run(sampleSize: Int = 200) -> Result {
        var r = Result()

        // V-1 — full vs limited authorisation
        let status = PHPhotoLibrary.authorizationStatus(for: .readWrite)
        switch status {
        case .authorized: r.authorizationStatus = "authorized"
        case .limited:    r.authorizationStatus = "limited"; r.isLimitedLibrary = true
        case .denied:     r.authorizationStatus = "denied"
        case .restricted: r.authorizationStatus = "restricted"
        case .notDetermined: r.authorizationStatus = "notDetermined"
        @unknown default: r.authorizationStatus = "unknown"
        }

        let all = PHAsset.fetchAssets(with: nil)
        r.totalAssetsVisible = all.count
        if r.isLimitedLibrary {
            r.notes.append("LIMITED authorisation: only \(all.count) assets are enumerable. "
                         + "A user on limited access may make the Visual Library premise unworkable — "
                         + "the product needs a stated position on this.")
        }

        // V-5 — is there a Recently Deleted album, i.e. is deletion recoverable?
        let deleted = PHAssetCollection.fetchAssetCollections(
            with: .smartAlbum, subtype: .smartAlbumAllHidden, options: nil)
        _ = deleted
        // `smartAlbumRecentlyDeleted` is not exposed to third-party apps on all OS
        // versions, so presence cannot be proven by fetch alone. The authoritative
        // check is the manual one in the operator checklist: delete a synthetic
        // asset via the harness, then confirm in Photos > Recently Deleted that it
        // is present and restorable, and record the retention shown.
        r.notes.append("V-5 MUST be confirmed manually: delete one SYNTHETIC asset, "
                     + "then verify it appears in Photos > Recently Deleted and can be restored. "
                     + "Record the retention period the system reports. Do not assume 30 days.")

        // V-4 — how many assets have no usable local thumbnail with network denied
        let opts = PHImageRequestOptions()
        opts.isNetworkAccessAllowed = false
        opts.deliveryMode = .fastFormat
        opts.isSynchronous = true
        let n = min(sampleSize, all.count)
        for i in 0..<n {
            let a = all.object(at: i)
            var gotImage = false
            var inCloud = false
            PHImageManager.default().requestImage(
                for: a, targetSize: CGSize(width: 256, height: 256),
                contentMode: .aspectFit, options: opts) { img, info in
                    gotImage = (img != nil)
                    inCloud = (info?[PHImageResultIsInCloudKey] as? Bool) ?? false
            }
            if inCloud {
                r.cloudOnlyAssetsSampled += 1
                if gotImage { r.cloudOnlyThumbnailUsable += 1 }
            }
        }
        if r.cloudOnlyAssetsSampled > 0 && r.cloudOnlyThumbnailUsable == 0 {
            r.notes.append("SEVERE: every sampled iCloud-only asset returned NO usable "
                         + "thumbnail with network denied. If this generalises, first-run "
                         + "cataloguing of an optimised library is network-bound and the "
                         + "product constraint is far more serious than throughput.")
        }
        return r
    }

    static func write(_ r: Result) {
        let dir = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let u = dir.appendingPathComponent("PHOTOKIT_PROBES_TIER0.json")
        if let d = try? JSONEncoder().encode(r) { try? d.write(to: u) }
    }
}
