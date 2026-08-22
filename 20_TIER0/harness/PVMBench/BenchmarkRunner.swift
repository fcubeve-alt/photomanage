import Foundation
import Photos
import UIKit

/// Orchestrates the A1–A4 runs. Every meaningful number this produces is MEASURED.
/// PF-01: nothing modelled or predicted may be written to the CSV.
final class BenchmarkRunner: NSObject, ObservableObject {

    enum RunType: String { case cold, resume, incremental, background }

    @Published var progress: Double = 0
    @Published var statusText = "idle"
    @Published var isRunning = false

    private let store = IndexStore()
    private lazy var indexer = AssetIndexer(store: store)
    private lazy var changeTracker = LibraryChangeTracker(store: store)
    private let telemetry = Telemetry()
    private var cancelled = false

    /// C-3 — checkpoint every N assets. On resume, reprocessing must be bounded by N.
    /// Anything above one batch means checkpointing is too coarse (E-07).
    static let checkpointEvery = 200

    // Set by the operator before a run so rows are attributable.
    var storageState = "unknown"     // "all-local" | "icloud-optimised"
    var chipLabel = ""

    // MARK: - cold / resume

    func runCold(resume: Bool) {
        guard !isRunning else { return }
        isRunning = true; cancelled = false
        let runType: RunType = resume ? .resume : .cold

        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            guard let self else { return }

            if !resume { self.store.reset() }
            let alreadyIndexed = resume ? self.store.count() : 0

            let opts = PHFetchOptions()
            opts.sortDescriptors = [NSSortDescriptor(key: "creationDate", ascending: true)]
            opts.includeHiddenAssets = false

            // CD-1 — cold-launch to first asset enumerated. Flaky PhotoKit init is a
            // first-impression killer, and a competitor spent three releases on it.
            let tEnum = CFAbsoluteTimeGetCurrent()
            let all = PHAsset.fetchAssets(with: opts)
            let enumMS = (CFAbsoluteTimeGetCurrent() - tEnum) * 1000

            let total = all.count
            let syntheticIDs = Set(self.store.syntheticIDs())

            self.telemetry.start()
            self.indexer.resetCounters()
            let t0 = CFAbsoluteTimeGetCurrent()

            var processed = 0
            var reprocessed = 0
            var batch = 0
            self.store.beginBatch()

            for i in 0..<total {
                if self.cancelled { break }
                let asset = all.object(at: i)

                if resume && self.store.contains(asset.localIdentifier) {
                    // Already durable from a previous run — skip. Counted so the
                    // checkpoint granularity can be judged, not hidden.
                    processed += 1
                    continue
                }
                if resume { reprocessed += 1 }

                autoreleasepool {
                    self.indexer.index(asset: asset,
                                       isSynthetic: syntheticIDs.contains(asset.localIdentifier))
                }
                processed += 1
                batch += 1

                if batch >= BenchmarkRunner.checkpointEvery {
                    self.store.setCursor(asset.localIdentifier)
                    self.store.commitBatch()
                    self.store.beginBatch()
                    batch = 0
                    let p = Double(processed) / Double(max(total, 1))
                    DispatchQueue.main.async {
                        self.progress = p
                        self.statusText = "\(processed)/\(total) · \(Int(Telemetry.footprintMB())) MB · \(ProcessInfo.processInfo.thermalState.label)"
                    }
                }
            }

            self.store.commitBatch()
            let wall = CFAbsoluteTimeGetCurrent() - t0
            self.telemetry.stop()

            var row = BenchmarkRow()
            row.chip = self.chipLabel
            row.library_size = total
            row.storage_state = self.storageState
            row.run_type = runType.rawValue
            row.wall_time_s = wall
            row.assets_indexed = processed
            row.assets_failed = self.indexer.counters.failed
            row.throughput_assets_per_s = wall > 0 ? Double(processed) / wall : 0
            row.peak_mem_mb = self.telemetry.snap.peakFootprintMB
            row.avg_cpu_pct = self.telemetry.avgCPU
            row.thermal_nominal_s = self.telemetry.dwell(.nominal)
            row.thermal_fair_s = self.telemetry.dwell(.fair)
            row.thermal_serious_s = self.telemetry.dwell(.serious)
            row.thermal_critical_s = self.telemetry.dwell(.critical)
            row.battery_start_pct = Double(self.telemetry.snap.batteryStart) * 100
            row.battery_end_pct = Double(self.telemetry.snap.batteryEnd) * 100
            let drained = row.battery_start_pct - row.battery_end_pct
            row.battery_drain_pct_per_10k = processed > 0 ? drained / Double(processed) * 10_000 : 0
            row.index_bytes_total = self.store.sizeOnDisk()
            row.index_bytes_per_asset = processed > 0 ? Double(row.index_bytes_total) / Double(processed) : 0
            row.resumed_ok = resume
            row.assets_reprocessed_after_resume = resume ? reprocessed : 0
            row.ocr_attempted = self.indexer.counters.ocrAttempted
            row.ocr_gated_out = self.indexer.counters.ocrGatedOut
            row.embed_attempted = self.indexer.counters.embedAttempted
            row.icloud_fetch_required_count = self.indexer.counters.icloudFetchRequired
            row.icloud_fetch_skipped_count = self.indexer.counters.icloudFetchSkipped
            row.synthetic_asset_count = syntheticIDs.count
            row.real_asset_count = max(0, total - syntheticIDs.count)
            row.cold_launch_to_first_asset_ms = enumMS
            row.bg_expiration_events = self.telemetry.snap.expirationEvents
            row.memory_warnings = self.telemetry.snap.memoryWarnings
            row.ocr_ms_per_asset = self.indexer.counters.ocrAttempted > 0
                ? self.indexer.counters.ocrTotalMS / Double(self.indexer.counters.ocrAttempted) : 0
            row.embed_ms_per_asset = self.indexer.counters.embedAttempted > 0
                ? self.indexer.counters.embedTotalMS / Double(self.indexer.counters.embedAttempted) : 0
            row.index_state_recovered_after_kill = self.store.meta("cursor") != nil && resume
            row.notes = self.cancelled ? "cancelled-by-operator" : ""

            MetricsCSV.append(row)

            DispatchQueue.main.async {
                self.isRunning = false
                self.progress = 1
                self.statusText = String(format: "done · %.0fs · %.1f assets/s", wall, row.throughput_assets_per_s)
            }
        }
    }

    func cancel() { cancelled = true }

    // MARK: - A4 incremental (C-5)

    /// A4 is falsified the moment finding deltas needs a full enumeration.
    ///
    /// Uses `LibraryChangeTracker`: the persistent change token for everything that
    /// happened while the app was closed, plus the live observer while it runs.
    /// The earlier newest-first walk is gone — it could not see **edits to old
    /// assets**, so it would have reported "0 new" while the index went stale, and
    /// A4 would have passed a test that never exercised its own failure case.
    func runIncremental() {
        guard !isRunning else { return }
        isRunning = true; cancelled = false

        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            guard let self else { return }
            self.telemetry.start()
            self.indexer.resetCounters()
            let t0 = CFAbsoluteTimeGetCurrent()

            let delta = self.changeTracker.catchUpSinceLastLaunch()
            let tDelta = CFAbsoluteTimeGetCurrent() - t0

            // Only the changed identifiers are fetched. No full enumeration.
            let touched = Array(Set(delta.inserted + delta.updated))
            var processed = 0

            if !touched.isEmpty {
                let fetched = PHAsset.fetchAssets(withLocalIdentifiers: touched, options: nil)
                self.store.beginBatch()
                fetched.enumerateObjects { asset, _, _ in
                    autoreleasepool { self.indexer.index(asset: asset, isSynthetic: false) }
                    processed += 1
                }
                self.store.commitBatch()
            }
            for gone in delta.deleted { self.store.remove(gone) }

            let wall = CFAbsoluteTimeGetCurrent() - t0
            self.telemetry.stop()

            var row = BenchmarkRow()
            row.chip = self.chipLabel
            row.library_size = self.store.count()
            row.storage_state = self.storageState
            row.run_type = RunType.incremental.rawValue
            row.wall_time_s = wall
            row.assets_indexed = processed
            row.throughput_assets_per_s = wall > 0 ? Double(processed) / wall : 0
            row.peak_mem_mb = self.telemetry.snap.peakFootprintMB
            row.avg_cpu_pct = self.telemetry.avgCPU
            row.index_bytes_total = self.store.sizeOnDisk()
            row.ocr_attempted = self.indexer.counters.ocrAttempted
            row.ocr_gated_out = self.indexer.counters.ocrGatedOut
            row.embed_attempted = self.indexer.counters.embedAttempted
            row.delta_source = delta.source
            row.delta_inserted = delta.inserted.count
            row.delta_updated = delta.updated.count
            row.delta_deleted = delta.deleted.count
            row.delta_discovery_s = tDelta
            // The A4 verdict hinges on this: a full rescan here means the product
            // cannot maintain an index without periodically re-reading the library.
            row.required_full_rescan = (delta.source == "token-expired-full-rescan")
            row.notes = "delta via \(delta.source); no full enumeration"
            MetricsCSV.append(row)

            DispatchQueue.main.async {
                self.isRunning = false
                self.statusText = String(
                    format: "incremental (%@): +%d ~%d -%d in %.1fs",
                    delta.source, delta.inserted.count, delta.updated.count,
                    delta.deleted.count, wall)
            }
        }
    }

    /// A4 sub-test that the old implementation could not perform at all:
    /// modify an EXISTING asset and confirm the tracker sees it.
    /// Uses a synthetic asset only — never touches anything pre-existing (DEC-009).
    func editOldestSyntheticAssetForA4(completion: @escaping (String) -> Void) {
        let ids = store.syntheticIDs()
        guard let victim = ids.first else {
            completion("no synthetic asset available; insert some first"); return
        }
        let fetched = PHAsset.fetchAssets(withLocalIdentifiers: [victim], options: nil)
        guard let asset = fetched.firstObject else {
            completion("synthetic asset not found in library"); return
        }
        PHPhotoLibrary.shared().performChanges({
            let req = PHAssetChangeRequest(for: asset)
            // A favourite toggle is a metadata edit: it bumps modificationDate
            // without altering pixels, which is exactly the case a creationDate
            // ordered walk cannot detect.
            req.isFavorite = !asset.isFavorite
        }, completionHandler: { ok, err in
            DispatchQueue.main.async {
                completion(ok
                    ? "edited \(victim) — now run Incremental; it MUST report updated >= 1"
                    : "edit failed: \(String(describing: err))")
            }
        })
    }

    // MARK: - CD-2 first-screen stall

    /// Time from request to a rendered grid of thumbnails on a large library.
    /// Invisible in a throughput number, and the place real users noticed a
    /// competitor failing. Target §8: <= 3 s.
    func measureFirstScreenStall(count: Int = 60, completion: @escaping (Double) -> Void) {
        DispatchQueue.global(qos: .userInitiated).async {
            let t0 = CFAbsoluteTimeGetCurrent()
            let opts = PHFetchOptions()
            opts.sortDescriptors = [NSSortDescriptor(key: "creationDate", ascending: false)]
            opts.fetchLimit = count
            let assets = PHAsset.fetchAssets(with: opts)
            let req = PHImageRequestOptions()
            req.isNetworkAccessAllowed = false
            req.deliveryMode = .fastFormat
            req.isSynchronous = true
            for i in 0..<assets.count {
                autoreleasepool {
                    PHImageManager.default().requestImage(
                        for: assets.object(at: i),
                        targetSize: CGSize(width: 120, height: 120),
                        contentMode: .aspectFill, options: req) { _, _ in }
                }
            }
            let ms = (CFAbsoluteTimeGetCurrent() - t0) * 1000
            DispatchQueue.main.async { completion(ms) }
        }
    }

    /// Live observation, so edits arriving while the app is open are seen too.
    func startLiveObservation() {
        changeTracker.onLiveDelta = { [weak self] d in
            guard let self, d.count > 0 else { return }
            self.statusText = "live change: +\(d.inserted.count) ~\(d.updated.count) -\(d.deleted.count)"
        }
        changeTracker.startObserving()
    }

    var indexedCount: Int { store.count() }
    var storeRef: IndexStore { store }
    var telemetryRef: Telemetry { telemetry }
}
