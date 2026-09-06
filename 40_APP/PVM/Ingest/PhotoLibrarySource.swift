import Foundation
import Photos
import PVMCore

/// PHAsset → AssetSignals.
///
/// The split here is the whole of §24 Gate 3. `breadthSignals` reads the PhotoKit row
/// and **decodes no pixels** — 0.17 ms/asset measured — so a 100k library has its
/// shelves in under thirty seconds. `depthSignals` is the expensive half and is what
/// gets paced.
///
/// C-2 is non-negotiable in both: thumbnails only, `isNetworkAccessAllowed = false`.
/// Requesting originals on an iCloud-optimised library measures the user's Wi-Fi
/// instead of their phone, and would produce a spuriously catastrophic result.
public enum PhotoLibrarySource {

    public static func authorizationStatus() -> PHAuthorizationStatus {
        PHPhotoLibrary.authorizationStatus(for: .readWrite)
    }

    public static func requestAuthorization(_ done: @escaping (PHAuthorizationStatus) -> Void) {
        PHPhotoLibrary.requestAuthorization(for: .readWrite) { status in
            DispatchQueue.main.async { done(status) }
        }
    }

    public static func fetchAll() -> PHFetchResult<PHAsset> {
        let options = PHFetchOptions()
        options.sortDescriptors = [NSSortDescriptor(key: "creationDate", ascending: false)]
        options.includeHiddenAssets = false
        return PHAsset.fetchAssets(with: options)
    }

    /// Tier.metadata only. Nothing here touches a pixel.
    public static func breadthSignals(from asset: PHAsset) -> AssetSignals {
        var s = AssetSignals(assetID: asset.localIdentifier)
        s.createdAt = asset.creationDate
        s.modifiedAt = asset.modificationDate
        s.pixelW = asset.pixelWidth
        s.pixelH = asset.pixelHeight
        s.isVideo = asset.mediaType == .video
        s.durationSeconds = asset.duration
        s.isScreenshot = asset.mediaSubtypes.contains(.photoScreenshot)
        s.isScreenRecording = PhotoLibrarySource.looksLikeScreenRecording(asset)
        s.burstID = asset.burstIdentifier
        if let loc = asset.location {
            s.geo = GeoFix(lat: loc.coordinate.latitude, lon: loc.coordinate.longitude, source: .exif)
        }
        s.source = provenance(of: asset)
        return s
    }

    /// PhotoKit has no screen-recording subtype — `videoScreenRecording` does not
    /// exist, which is what the first build of this file assumed. A screen recording is
    /// just a video, so the only available signal is iOS's own filename prefix. A
    /// filename heuristic, stated as one.
    private static func looksLikeScreenRecording(_ asset: PHAsset) -> Bool {
        guard asset.mediaType == .video else { return false }
        guard let name = PHAssetResource.assetResources(for: asset).first?.originalFilename
        else { return false }
        return name.uppercased().hasPrefix("RPREPLAY")
    }

    /// Where the pixels came from. PhotoKit does not answer this directly.
    ///
    /// Deliberately conservative: `camera` when there is positive evidence, `shared`
    /// and `downloaded` where the source type says so outright, and `unknown`
    /// otherwise. The first version returned "downloaded" for anything without a
    /// camera-style filename, which would have swept every renamed, edited or
    /// third-party-app photo into the Downloads shelf — a mass mis-filing produced by
    /// a guess. `Downloads` therefore stays largely unreachable until a real
    /// provenance signal exists, which is the honest position: the evaluation against
    /// the labelled library found exactly the same gap.
    private static func provenance(of asset: PHAsset) -> String {
        if asset.mediaSubtypes.contains(.photoScreenshot) { return "screenshot" }
        if asset.sourceType.contains(.typeCloudShared) { return "shared" }
        if asset.sourceType.contains(.typeiTunesSynced) { return "downloaded" }
        guard let name = PHAssetResource.assetResources(for: asset).first?.originalFilename
        else { return "unknown" }
        let upper = name.uppercased()
        if upper.hasPrefix("IMG_") || upper.hasPrefix("DSC") || upper.hasPrefix("PXL_") {
            return "camera"
        }
        return "unknown"
    }

    /// Reverse geocoding is a network call and a rate-limited one, so it is done for the
    /// distinct places a library contains rather than per asset — §11 wants Country →
    /// City, and a library has far fewer cities than photos.
    public static func attachPlaceNames(_ signals: inout [AssetSignals],
                                        resolver: (GeoFix) -> PlaceName?) {
        var cache: [String: PlaceName] = [:]
        for i in signals.indices {
            guard let geo = signals[i].geo else { continue }
            let key = String(format: "%.2f,%.2f", geo.lat, geo.lon)
            if let hit = cache[key] {
                signals[i].place = hit
                continue
            }
            guard let name = resolver(geo) else { continue }
            cache[key] = name
            signals[i].place = name
        }
    }
}
