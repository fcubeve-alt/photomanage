import Foundation
import Photos
import PVMCore
#if canImport(Combine)
import Combine
#endif

/// Whether the last block handed to `offMain` actually ran off the main thread.
/// Written by `offMain`, read by `IngestionThreadingTests`; nothing in the product
/// branches on it.
var offMainLastRanOnMainThread = true

/// What start-up's migration did, for the support report. File-scope rather than a
/// static on the coordinator because `defaultCatalog()` is `nonisolated` — it is
/// evaluated as a default argument — and a nonisolated function cannot write to a
/// main-actor-isolated static.
/// What `protectOnDisk` could not apply, for the support report. Empty is the expected
/// state; anything in it is a security control that did not take effect.
var protectionFailures: [String] = []

var lastMigration: CatalogMigration.Outcome?
var lastQuarantine: String?

/// Drives the two passes and owns the app's view of them.
///
/// §12: a new user should not see a screen of tool buttons — they should see that the
/// system has already started working. So the breadth pass runs immediately on
/// permission, the home fills in within seconds, and the depth pass is paced from there.
@MainActor
public final class IngestionCoordinator: ObservableObject {

    public enum Phase: Equatable {
        case idle
        case needsPermission
        case breadth(done: Int, total: Int)
        case ready                       // shelves are up; depth may still be running
        case depth(done: Int, total: Int)
        case complete
        case failed(String)
    }

    @Published public private(set) var phase: Phase = .idle
    @Published public private(set) var rolledCounts: [String: Int] = [:]
    @Published public private(set) var stats: RunStats?
    @Published public private(set) var plan: IngestionPlan?
    @Published public private(set) var ttfuvSeconds: Double?
    /// §2 Remember. Read once per refresh rather than per row: the list is short and
    /// the alternative is a query inside a SwiftUI body, which runs on every redraw.
    @Published public private(set) var memoryEntities: [Catalog.EntityRow] = []

    public let catalog: Catalog?
    private var assets: [AssetSignals] = []
    private var phAssets: [String: PHAsset] = [:]

    public init(catalog: Catalog? = IngestionCoordinator.defaultCatalog()) {
        self.catalog = catalog
    }

    /// `nonisolated` because it is used as a default argument, and a default argument
    /// expression cannot call into the main actor.
    ///
    /// **The catalogue is more sensitive than the photographs it describes.** A third-
    /// party audit made this point on 2026-09-11 and it is correct: a photo of a
    /// passport is one image among thousands; the catalogue holds its OCR text, the
    /// places someone has been with dates, who appears in their life and how often, and
    /// it is all indexed and searchable. It was being written with the iOS default
    /// protection class and included in iCloud backup, and neither had been decided —
    /// they were just what you get for not choosing.
    ///
    /// Both are chosen now:
    ///
    /// * `.completeUntilFirstUserAuthentication` — unreadable until the phone has been
    ///   unlocked once after boot, which defeats offline extraction from a powered-down
    ///   device. Not `.complete`, which would be stronger and would also stop
    ///   `BGProcessingTask` dead, since that runs while the phone is locked. That is a
    ///   real trade and this is the side of it the product needs.
    /// * Excluded from iCloud backup — the catalogue is entirely derivable from the
    ///   photo library, so backing it up buys nothing and would put OCR'd document text
    ///   into iCloud, which is exactly the thing the product promises not to do.
    public nonisolated static func defaultCatalog() -> Catalog? {
        let dir = FileManager.default.urls(for: .applicationSupportDirectory,
                                           in: .userDomainMask)[0]
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        let url = dir.appendingPathComponent("pvm_catalog.sqlite")
        var catalog = Catalog(path: url.path)
        guard let opened = catalog else { return nil }
        protectionFailures = protectOnDisk(url)

        // Migration runs here, on the launch that opens the file, before anything
        // queries it. See `50_LAUNCH/DATA_MIGRATION.md` — the short version is that
        // almost every row is derived from the photo library and can be recomputed,
        // and the two tables that are not (`decisions`, `entity_review`) are the ones
        // the user wrote, so they are preserved rather than migrated.
        if opened.isFromANewerBuild {
            // A downgrade. This build cannot read the newer shape, so the file is set
            // aside — not deleted, it belongs to a version the user may go back to —
            // and a fresh one is opened in its place.
            lastQuarantine = Catalog.quarantine(path: url.path)
            catalog = Catalog(path: url.path)
            guard let replacement = catalog else { return nil }
            protectionFailures = protectOnDisk(url)
            lastMigration = replacement.migrate()
            protectionFailures += protectOnDisk(url)
            return replacement
        }
        lastMigration = opened.migrate()
        // Applied a second time on purpose. The first call ran before SQLite had
        // written anything, so `-wal` and `-shm` did not exist yet and were skipped —
        // and the WAL is the file holding the most recent writes in full. By here the
        // migration has forced them into existence.
        protectionFailures += protectOnDisk(url)
        return opened
    }


    /// Applied to the database and to its write-ahead log and shared-memory siblings.
    ///
    /// The WAL is the one that gets forgotten, and it is not a lesser file: it holds
    /// the most recent writes in full. Protecting `pvm_catalog.sqlite` and leaving
    /// `pvm_catalog.sqlite-wal` at the default would protect the history and expose
    /// today.
    /// Returns what it could not do. An earlier version was `try?` throughout and
    /// therefore could not tell "protected" from "silently failed to protect" — a
    /// second audit's P2, and the worst failure mode available to a security control,
    /// because it fails into the appearance of success. Two things follow from the
    /// return value: `protectionFailures` is shown in the support report, so a user
    /// who cares can see it, and the caller re-applies after the database has written,
    /// which is when the WAL and SHM siblings actually come into existence.
    @discardableResult
    nonisolated static func protectOnDisk(_ url: URL) -> [String] {
        var failures: [String] = []
        #if canImport(UIKit)
        let manager = FileManager.default
        for suffix in ["", "-wal", "-shm"] {
            let sibling = URL(fileURLWithPath: url.path + suffix)
            // A sibling that does not exist yet is not a failure: SQLite creates the
            // WAL on the first write, and the re-application below is what covers it.
            guard manager.fileExists(atPath: sibling.path) else { continue }
            do {
                try manager.setAttributes(
                    [.protectionKey: FileProtectionType.completeUntilFirstUserAuthentication],
                    ofItemAtPath: sibling.path)
            } catch {
                failures.append("protection\(suffix.isEmpty ? "" : suffix)")
            }
            do {
                var excluded = sibling
                var values = URLResourceValues()
                values.isExcludedFromBackup = true
                try excluded.setResourceValues(values)
            } catch {
                failures.append("backup-exclusion\(suffix.isEmpty ? "" : suffix)")
            }
        }
        // Read the protection back rather than trusting the write. `setAttributes`
        // succeeding is not the same as the file having the class — a distinction that
        // matters on a device with no passcode, where iOS downgrades it.
        if let actual = try? manager.attributesOfItem(atPath: url.path)[.protectionKey]
            as? FileProtectionType,
           actual != .completeUntilFirstUserAuthentication && actual != .complete {
            failures.append("protection-not-applied(\(actual.rawValue))")
        }
        #endif
        return failures
    }



    // MARK: - entry points

    /// Indexing runs off the main thread. This is not a nicety: the depth pass is
    /// 105–154 ms per asset measured, so a paced slice of 2,000 assets is five minutes.
    /// On the main actor that is five minutes of frozen UI, which would make the paced
    /// design — whose entire point is not to take the phone away — do exactly that.
    private static let work = DispatchQueue(label: "com.pvm.app.indexing", qos: .utility)

    /// No `Sendable` constraint, deliberately. `PHAsset` is a class and cannot be
    /// Sendable, and the values crossing here are either value types or the catalogue,
    /// whose thread-safety comes from `SQLITE_OPEN_FULLMUTEX` and is documented on the
    /// type. Claiming a constraint the code cannot honour would be worse than stating
    /// the reason it is safe.
    private static func offMain<T>(_ body: @escaping () -> T) async -> T {
        await withCheckedContinuation { continuation in
            work.async {
                // Recorded so a test can assert the property about the PRODUCTION
                // call path instead of about a function it dispatched itself — the
                // difference the second audit asked for, and the difference between
                // "this function can run off the main thread" and "the app runs it
                // off the main thread".
                offMainLastRanOnMainThread = Thread.isMainThread
                continuation.resume(returning: body())
            }
        }
    }

    public func start() {
        switch PhotoLibrarySource.authorizationStatus() {
        case .authorized, .limited:
            Task { await runBreadthPass() }
        case .notDetermined:
            phase = .needsPermission
        default:
            phase = .needsPermission
        }
    }

    public func requestPermission() {
        PhotoLibrarySource.requestAuthorization { [weak self] status in
            Task { @MainActor in
                guard let self else { return }
                if status == .authorized || status == .limited {
                    await self.runBreadthPass()
                } else {
                    self.phase = .failed(
                        "Without access to your photos there is nothing to catalogue.")
                }
            }
        }
    }

    /// Seed the coordinator directly. Used by tests and by the Simulator screenshot run,
    /// where there is no real photo library to read.
    public func loadFixture(_ signals: [AssetSignals]) {
        assets = signals
        Task { await classify(budget: .text, phaseLabel: .breadth(done: 0, total: signals.count)) }
    }

    // MARK: - phases

    private func runBreadthPass() async {
        guard let catalog else {
            phase = .failed("The catalogue could not be opened.")
            return
        }
        let started = Date()
        let fetch = PhotoLibrarySource.fetchAll()
        var collected: [AssetSignals] = []
        collected.reserveCapacity(fetch.count)
        var index: [String: PHAsset] = [:]
        fetch.enumerateObjects { asset, _, _ in
            collected.append(PhotoLibrarySource.breadthSignals(from: asset))
            index[asset.localIdentifier] = asset
        }
        phAssets = index
        assets = collected
        phase = .breadth(done: 0, total: collected.count)

        // Metadata only — no pixel is decoded, which is why this is seconds and not days.
        let snapshot = collected
        let result = await Self.offMain {
            Pipeline.run(assets: snapshot, catalog: catalog, budget: .metadata)
        }
        stats = result
        ttfuvSeconds = Date().timeIntervalSince(started)
        plan = IngestionPlanner.plan(librarySize: collected.count)
        refreshCounts()
        phase = .ready
    }

    /// How many assets are enriched and classified before the UI hears about it.
    ///
    /// Small enough that progress moves visibly and a cancellation lands within about a
    /// second; large enough that the actor hop and the catalogue transaction are not
    /// paid per asset. `Catalog.batchSize` is 200 for the same reason and this is
    /// deliberately smaller — that one bounds data loss on a kill, this one bounds how
    /// long the user stares at a number that is not moving.
    private static let depthBatch = 25

    /// The in-flight depth pass, so a second call replaces it rather than racing it.
    private var depthTask: Task<Void, Never>?

    /// Which pass is allowed to write progress.
    ///
    /// Cancelling a `Task` does not stop the batch already in flight — it finishes,
    /// comes back, and then writes `stats` and `phase`. With only `depthTask` to go on,
    /// that write lands on top of the pass that replaced it, so the UI jumps back to
    /// the old pass's numbers for one batch. Second audit, P2, and correct. Each pass
    /// takes a generation number and writes nothing once it is no longer the current one.
    private var depthGeneration = 0

    /// Stop the paced pass. The batch in flight finishes; nothing after it starts.
    public func cancelDepthPass() {
        depthTask?.cancel()
        depthTask = nil
    }

    /// The paced half. `limit` is what the chosen option allows in one go, so a plan of
    /// "2,000 a day" is honoured by calling this with 2,000 and stopping.
    ///
    /// **Everything expensive here runs off the main actor, and that is not a nicety.**
    /// Until 2026-09-11 this was a synchronous method on a `@MainActor` class that
    /// looped `VisionSignals.enrich` — an image decode plus Vision, measured at
    /// 105–154 ms per asset — and then `Pipeline.run`, without ever calling the
    /// `offMain` helper defined sixty lines above it. A 2,000-asset slice was therefore
    /// about four and a half minutes of completely frozen UI, which is past the point
    /// where the iOS watchdog kills the app, and the paced design whose entire purpose
    /// is not to take the phone away would have taken the phone away.
    ///
    /// The comment on `offMain` described this correctly the whole time. The code did
    /// the opposite. A third-party audit found it; no test could have, because there
    /// was no test that asserted where the work runs — there is one now
    /// (`IngestionThreadingTests`).
    public func runDepthPass(limit: Int? = nil) {
        depthTask?.cancel()
        depthGeneration += 1
        let generation = depthGeneration
        depthTask = Task { [weak self] in
            await self?.performDepthPass(limit: limit, generation: generation)
        }
    }

    private func performDepthPass(limit: Int?, generation: Int) async {
        guard let catalog else { return }
        let pending = assets.filter { catalog.needsClassification($0) }
        let slice = limit.map { Array(pending.prefix($0)) } ?? pending
        guard !slice.isEmpty else {
            if generation == depthGeneration { phase = .complete }
            return
        }
        phase = .depth(done: 0, total: slice.count)

        // Snapshotted on the main actor, once, so the background work never reads
        // actor state. `PHAsset` is a class and not Sendable; see `offMain`.
        let index = phAssets
        var done = 0

        for start in stride(from: 0, to: slice.count, by: Self.depthBatch) {
            if Task.isCancelled {
                // Everything already classified is committed — the pass is resumable
                // because `needsClassification` is the only thing that decides what is
                // pending, and it reads the catalogue rather than a cursor in memory.
                if generation == depthGeneration { phase = .ready }
                return
            }
            let batch = Array(slice[start..<min(start + Self.depthBatch, slice.count)])
            let result = await Self.offMain {
                let enriched = Self.enrich(batch, using: index)
                return Pipeline.run(assets: enriched, catalog: catalog, budget: .text,
                                    reconcileDeletions: false)
            }
            // Back on the main actor after an await that may have taken a second. A
            // newer pass may have started in the meantime, and the loser of that race
            // must not narrate over the winner.
            guard generation == depthGeneration else { return }
            self.stats = result
            done += batch.count
            phase = .depth(done: done, total: slice.count)
        }

        guard generation == depthGeneration else { return }
        refreshCounts()
        phase = pending.count == slice.count ? .complete : .ready
        depthTask = nil
    }

    /// The expensive per-asset work.
    ///
    /// **`nonisolated` does less than an earlier version of this comment claimed**, and
    /// a second audit was right to say so. It does not make calling this from the main
    /// actor a compile error — a nonisolated function is callable from anywhere,
    /// including the main thread. What it does guarantee is the other direction: this
    /// function cannot be moved back ONTO the coordinator's actor without breaking
    /// every non-isolated caller, which is what `IngestionThreadingTests` pins.
    ///
    /// What keeps the main thread free is not the keyword, it is that the only caller
    /// is `performDepthPass`, which goes through `offMain`. `testTheProductionDepthPass
    /// RunsItsWorkOffTheMainThread` exercises that caller rather than this function, so
    /// a future edit that calls `enrich` directly from the actor is caught by a test
    /// failing rather than by a user's phone freezing.
    ///
    /// Serial within the batch on purpose: Vision already parallelises internally, and
    /// a second layer of concurrency on top of it raises peak memory on exactly the
    /// old devices where jetsam is the thing being guarded against (A3).
    nonisolated static func enrich(_ batch: [AssetSignals],
                                   using index: [String: PHAsset]) -> [AssetSignals] {
        var enriched: [AssetSignals] = []
        enriched.reserveCapacity(batch.count)
        for base in batch {
            var s = base
            #if canImport(UIKit)
            if let ph = index[base.assetID] {
                let vision = VisionSignals.enrich(asset: ph, base: base)
                s.dhash = vision.dhash
                s.ocrRan = vision.ocrRan
                s.ocrText = vision.ocrText
                s.sceneLabels = vision.sceneLabels
                if vision.faceCount > 0 {
                    s.faceClusters = (0..<vision.faceCount).map {
                        FaceCluster(clusterID: "unnamed-\(base.assetID)-\($0)")
                    }
                }
            }
            #endif
            enriched.append(s)
        }
        return enriched
    }

    private func classify(budget: Tier, phaseLabel: Phase) async {
        guard let catalog else { return }
        phase = phaseLabel
        let started = Date()
        let snapshot = assets
        let result = await Self.offMain {
            Pipeline.run(assets: snapshot, catalog: catalog, budget: budget)
        }
        stats = result
        ttfuvSeconds = Date().timeIntervalSince(started)
        plan = IngestionPlanner.plan(librarySize: snapshot.count)
        refreshCounts()
        phase = .ready
    }

    public func refreshCounts() {
        rolledCounts = catalog?.rolledCounts() ?? [:]
        memoryEntities = catalog?.entities(limit: 500) ?? []
        sightingCounts = [:]
    }

    /// Cached because a SwiftUI list body is re-evaluated freely and a SQL count per
    /// row per redraw is how a catalogue browser starts to feel slow.
    private var sightingCounts: [String: Int] = [:]

    public func sightingCount(of entityID: String) -> Int {
        if let n = sightingCounts[entityID] { return n }
        let n = sightings(of: entityID).count
        sightingCounts[entityID] = n
        return n
    }

    /// §14: what the user just did, written down.
    ///
    /// Recorded at the moment of the decision rather than inferred later from the
    /// catalogue's state, because "this asset is gone" and "the user chose to remove
    /// it" are different facts and only one of them is feedback.
    public func record(_ verb: UserDecision.Verb, assetID: String, path: String) {
        catalog?.recordDecision(assetID: assetID, path: path, verb: verb)
        refreshCounts()
    }

    public var personalPolicy: PersonalPolicy {
        catalog?.personalPolicy() ?? PersonalPolicy()
    }

    public func sightings(of entityID: String) -> [Catalog.SightingRow] {
        catalog?.sightings(of: entityID) ?? []
    }

    // MARK: - derived

    public var libraryCount: Int { assets.count }

    public var reviewCount: Int {
        catalog?.scalar("SELECT COUNT(*) FROM assets WHERE needs_review=1") ?? 0
    }

    /// §23: the first level of the home, in the tree's own order, with the ones this
    /// library has nothing in left out rather than shown empty.
    public var topLevel: [(path: String, count: Int)] {
        Taxonomy.roots.compactMap { root in
            let n = rolledCounts[root] ?? 0
            return n > 0 ? (path: root, count: n) : nil
        }
    }
}
