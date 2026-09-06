import Foundation
import Photos
#if canImport(Combine)
import Combine
#endif

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

    public let catalog: Catalog?
    private var assets: [AssetSignals] = []
    private var phAssets: [String: PHAsset] = [:]

    public init(catalog: Catalog? = IngestionCoordinator.defaultCatalog()) {
        self.catalog = catalog
    }

    public static func defaultCatalog() -> Catalog? {
        let dir = FileManager.default.urls(for: .applicationSupportDirectory,
                                           in: .userDomainMask)[0]
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        return Catalog(path: dir.appendingPathComponent("pvm_catalog.sqlite").path)
    }

    // MARK: - entry points

    public func start() {
        switch PhotoLibrarySource.authorizationStatus() {
        case .authorized, .limited:
            runBreadthPass()
        case .notDetermined:
            phase = .needsPermission
        default:
            phase = .needsPermission
        }
    }

    public func requestPermission() {
        PhotoLibrarySource.requestAuthorization { [weak self] status in
            guard let self else { return }
            if status == .authorized || status == .limited {
                self.runBreadthPass()
            } else {
                self.phase = .failed("Without access to your photos there is nothing to catalogue.")
            }
        }
    }

    /// Seed the coordinator directly. Used by tests and by the Simulator screenshot run,
    /// where there is no real photo library to read.
    public func loadFixture(_ signals: [AssetSignals]) {
        assets = signals
        classify(budget: .text, phaseLabel: .breadth(done: 0, total: signals.count))
    }

    // MARK: - phases

    private func runBreadthPass() {
        guard let catalog else {
            phase = .failed("The catalogue could not be opened.")
            return
        }
        let started = Date()
        let fetch = PhotoLibrarySource.fetchAll()
        var collected: [AssetSignals] = []
        collected.reserveCapacity(fetch.count)
        phAssets.removeAll()
        fetch.enumerateObjects { asset, _, _ in
            collected.append(PhotoLibrarySource.breadthSignals(from: asset))
            self.phAssets[asset.localIdentifier] = asset
        }
        assets = collected
        phase = .breadth(done: 0, total: collected.count)

        // Metadata only — no pixel is decoded, which is why this is seconds and not days.
        let stats = Pipeline.run(assets: collected, catalog: catalog, budget: .metadata)
        self.stats = stats
        ttfuvSeconds = Date().timeIntervalSince(started)
        plan = IngestionPlanner.plan(librarySize: collected.count)
        refreshCounts()
        phase = .ready
    }

    /// The paced half. `limit` is what the chosen option allows in one go, so a plan of
    /// "2,000 a day" is honoured by calling this with 2,000 and stopping.
    public func runDepthPass(limit: Int? = nil) {
        guard let catalog else { return }
        let pending = assets.filter { catalog.needsClassification($0) }
        let slice = limit.map { Array(pending.prefix($0)) } ?? pending
        guard !slice.isEmpty else {
            phase = .complete
            return
        }
        phase = .depth(done: 0, total: slice.count)

        var enriched: [AssetSignals] = []
        enriched.reserveCapacity(slice.count)
        for base in slice {
            var s = base
            #if canImport(UIKit)
            if let ph = phAssets[base.assetID] {
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
        let stats = Pipeline.run(assets: enriched, catalog: catalog, budget: .text,
                                 reconcileDeletions: false)
        self.stats = stats
        refreshCounts()
        phase = pending.count == slice.count ? .complete : .ready
    }

    private func classify(budget: Tier, phaseLabel: Phase) {
        guard let catalog else { return }
        phase = phaseLabel
        let started = Date()
        stats = Pipeline.run(assets: assets, catalog: catalog, budget: budget)
        ttfuvSeconds = Date().timeIntervalSince(started)
        plan = IngestionPlanner.plan(librarySize: assets.count)
        refreshCounts()
        phase = .ready
    }

    public func refreshCounts() {
        rolledCounts = catalog?.rolledCounts() ?? [:]
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
