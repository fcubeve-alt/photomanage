import Foundation
import Photos

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
        s.isScreenRecording = asset.mediaSubtypes.contains(.videoScreenRecording)
        s.burstID = asset.burstIdentifier
        if let loc = asset.location {
            s.geo = GeoFix(lat: loc.coordinate.latitude, lon: loc.coordinate.longitude, source: .exif)
        }
        s.source = provenance(of: asset)
        return s
    }

    /// Where the pixels came from. PhotoKit does not answer this directly, so it is
    /// derived from the resource: an asset the camera took has camera metadata and a
    /// filename shaped like IMG_1234; one saved from another app usually has neither.
    /// A wrong answer costs a Downloads assignment, never a deletion.
    private static func provenance(of asset: PHAsset) -> String {
        if asset.mediaSubtypes.contains(.photoScreenshot) { return "screenshot" }
        if asset.sourceType.contains(.typeCloudShared) { return "shared" }
        if asset.sourceType.contains(.typeiTunesSynced) { return "downloaded" }
        let resources = PHAssetResource.assetResources(for: asset)
        guard let name = resources.first?.originalFilename else { return "unknown" }
        let upper = name.uppercased()
        if upper.hasPrefix("IMG_") || upper.hasPrefix("DSC") || upper.hasPrefix("PXL_") {
            return "camera"
        }
        return "downloaded"
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
