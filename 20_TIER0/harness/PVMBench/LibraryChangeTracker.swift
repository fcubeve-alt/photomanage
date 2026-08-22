import Foundation
import Photos

/// C-5 — change observation, not rescanning. A4 is falsified the moment finding
/// deltas requires a full enumeration.
///
/// WHY THIS FILE EXISTS. The first incremental implementation walked the library
/// newest-first and stopped at the first already-known asset. That is correct for
/// **new captures** and silently wrong for **edits to existing assets**: editing a
/// photo from 2023 changes its `modificationDate` but not its position in a
/// creationDate-ordered list, so the walk would stop long before reaching it and
/// report "0 new" while the index quietly went stale. A4 would have passed on a
/// test that never exercised the failing case.
///
/// Two mechanisms, because they cover different situations:
///
///   1. `PHPhotoLibraryChangeObserver` — live, while the app is running.
///   2. `PHPersistentChangeToken` (iOS 16+) — catches up on everything that changed
///      **while the app was not running**, which is the normal case for a photo
///      manager. Without this, an app that is opened once a week can only learn
///      about changes by rescanning, and A4 is unachievable in principle.
///
/// The token can expire. That is not an error to swallow — how long it survives
/// determines whether the product can ever avoid periodic full rescans, so an
/// expiry is recorded as a first-class benchmark result.
final class LibraryChangeTracker: NSObject, PHPhotoLibraryChangeObserver {

    struct Delta {
        var inserted: [String] = []
        var updated:  [String] = []
        var deleted:  [String] = []
        /// "observer" · "persistent-token" · "token-expired-full-rescan" · "no-token-first-run"
        var source: String = ""
        var count: Int { inserted.count + updated.count + deleted.count }
    }

    private let store: IndexStore
    private var observing = false
    private var liveFetch: PHFetchResult<PHAsset>?

    /// Called on the main queue whenever a live change arrives.
    var onLiveDelta: ((Delta) -> Void)?

    init(store: IndexStore) {
        self.store = store
        super.init()
    }

    deinit {
        if observing { PHPhotoLibrary.shared().unregisterChangeObserver(self) }
    }

    // MARK: - Live observation (app in foreground / background)

    func startObserving() {
        guard !observing else { return }
        liveFetch = PHAsset.fetchAssets(with: nil)
        PHPhotoLibrary.shared().register(self)
        observing = true
    }

    func stopObserving() {
        guard observing else { return }
        PHPhotoLibrary.shared().unregisterChangeObserver(self)
        observing = false
    }

    func photoLibraryDidChange(_ changeInstance: PHChange) {
        guard let previous = liveFetch,
              let details = changeInstance.changeDetails(for: previous) else { return }

        liveFetch = details.fetchResultAfterChanges

        var delta = Delta()
        delta.source = "observer"
        delta.inserted = details.insertedObjects.map { $0.localIdentifier }
        delta.deleted  = details.removedObjects.map { $0.localIdentifier }
        // `changedObjects` is the case the newest-first walk could never see.
        delta.updated  = details.changedObjects.map { $0.localIdentifier }

        // Persist the token immediately: if the app dies right after this, the next
        // launch must not re-see the same changes, and must not miss the next ones.
        saveCurrentToken()

        DispatchQueue.main.async { [weak self] in
            self?.onLiveDelta?(delta)
        }
    }

    // MARK: - Cold-start catch-up (what changed while we were not running)

    /// The normal case for a photo manager: the app has been closed for days.
    func catchUpSinceLastLaunch() -> Delta {
        var delta = Delta()

        guard let token = loadToken() else {
            delta.source = "no-token-first-run"
            saveCurrentToken()
            return delta
        }

        do {
            let changes = try PHPhotoLibrary.shared().fetchPersistentChanges(since: token)
            delta.source = "persistent-token"
            for change in changes {
                guard let d = try? change.changeDetails(for: .asset) else { continue }
                delta.inserted.append(contentsOf: d.insertedLocalIdentifiers)
                delta.updated.append(contentsOf: d.updatedLocalIdentifiers)
                delta.deleted.append(contentsOf: d.deletedLocalIdentifiers)
            }
            saveCurrentToken()
        } catch {
            // Expiry is a RESULT, not a failure to hide. If the token expires
            // quickly in practice, periodic full rescans become unavoidable and A4
            // is capped — the benchmark must say so rather than quietly rescanning.
            delta.source = "token-expired-full-rescan"
            store.setMeta("lastTokenError", "\(error)")
            store.setMeta("tokenExpiredAt", ISO8601DateFormatter().string(from: Date()))
            saveCurrentToken()
        }
        return delta
    }

    // MARK: - Token persistence

    private func loadToken() -> PHPersistentChangeToken? {
        guard let b64 = store.meta("changeToken"),
              let data = Data(base64Encoded: b64) else { return nil }
        return try? NSKeyedUnarchiver.unarchivedObject(
            ofClass: PHPersistentChangeToken.self, from: data)
    }

    private func saveCurrentToken() {
        let token = PHPhotoLibrary.shared().currentChangeToken
        guard let data = try? NSKeyedArchiver.archivedData(
            withRootObject: token, requiringSecureCoding: true) else { return }
        store.setMeta("changeToken", data.base64EncodedString())
        store.setMeta("changeTokenSavedAt", ISO8601DateFormatter().string(from: Date()))
    }

    /// Age of the stored token, for the A4 report.
    var tokenAgeSeconds: TimeInterval? {
        guard let s = store.meta("changeTokenSavedAt"),
              let d = ISO8601DateFormatter().date(from: s) else { return nil }
        return Date().timeIntervalSince(d)
    }

    var lastTokenExpiry: String? { store.meta("tokenExpiredAt") }
}
