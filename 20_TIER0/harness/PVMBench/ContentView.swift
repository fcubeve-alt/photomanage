import SwiftUI
import Photos
import UIKit

/// Operator console. Deliberately ugly — this is instrumentation, not the product.
/// The Structure First home (Constitution §23) is the T0-B prototype, a separate
/// build; nothing here should be mistaken for product UI.
struct ContentView: View {
    @ObservedObject var runner: BenchmarkRunner

    @State private var authStatus = "unknown"
    @State private var libraryCount = 0
    @State private var storageState = "all-local"
    @State private var chip = ""
    @State private var syntheticTarget = "5000"
    @State private var screenshotRatio = "0.25"
    @State private var log: [String] = []
    @State private var showShare = false

    var body: some View {
        NavigationView {
            Form {
                Section("Device") {
                    LabeledContent("Model", value: MetricsCSV.deviceModel())
                    LabeledContent("iOS", value: UIDevice.current.systemVersion)
                    LabeledContent("RAM", value: "\(MetricsCSV.ramGB()) GB")
                    LabeledContent("Thermal", value: ProcessInfo.processInfo.thermalState.label)
                    LabeledContent("Footprint", value: String(format: "%.0f MB", Telemetry.footprintMB()))
                    LabeledContent("Mem headroom", value: String(format: "%.0f MB", Telemetry.availableMemoryMB()))
                    TextField("Chip (e.g. A15)", text: $chip)
                    Picker("Storage", selection: $storageState) {
                        Text("all-local").tag("all-local")
                        Text("icloud-optimised").tag("icloud-optimised")
                    }
                }

                Section("Library") {
                    LabeledContent("Authorisation", value: authStatus)
                    LabeledContent("Assets visible", value: "\(libraryCount)")
                    LabeledContent("Indexed", value: "\(runner.indexedCount)")
                    LabeledContent("Synthetic tracked", value: "\(runner.storeRef.syntheticCount())")
                    Button("Request access") { requestAccess() }
                    Button("Run PhotoKit probes (V-1…V-5)") { runProbes() }
                }

                Section("Benchmark") {
                    if runner.isRunning {
                        ProgressView(value: runner.progress)
                        Text(runner.statusText).font(.caption.monospaced())
                        Button("Cancel (simulates interruption)", role: .destructive) { runner.cancel() }
                    } else {
                        Text(runner.statusText).font(.caption.monospaced())
                        Button("A1/A2 · Cold full index") { start(resume: false) }
                        Button("A3 · Resume from checkpoint") { start(resume: true) }
                        Button("A4 · Incremental (delta only)") { startIncremental() }
                        // The case the old newest-first walk could never see.
                        Button("A4 · Edit an old asset, then re-run Incremental") { editForA4() }
                        Button("CD-2 · First-screen stall") { stall() }
                    }
                }

                Section("Synthetic corpus (DEC-009)") {
                    Text("Writes to the REAL photo library. Prove insertion AND cleanup on a disposable library first. Cleanup deletes only assets this app created.")
                        .font(.caption).foregroundStyle(.secondary)
                    TextField("Assets to insert", text: $syntheticTarget).keyboardType(.numberPad)
                    TextField("Screenshot ratio 0–1", text: $screenshotRatio).keyboardType(.decimalPad)
                    Button("Insert synthetic assets") { insertSynthetic() }
                    Button("Delete ALL synthetic assets", role: .destructive) { cleanupSynthetic() }
                }

                Section("Export") {
                    Button("Share DEVICE_BENCHMARK_TIER0.csv") { showShare = true }
                    Text(MetricsCSV.url.path).font(.caption2.monospaced()).foregroundStyle(.secondary)
                }

                Section("Log") {
                    ForEach(log.reversed(), id: \.self) { Text($0).font(.caption2.monospaced()) }
                }
            }
            .navigationTitle("PVM Bench · Tier 0-A")
            .onAppear { refresh() }
            .sheet(isPresented: $showShare) { ShareSheet(items: [MetricsCSV.url]) }
        }
    }

    private func note(_ s: String) {
        log.append("\(Date().formatted(date: .omitted, time: .standard))  \(s)")
    }

    private func refresh() {
        let st = PHPhotoLibrary.authorizationStatus(for: .readWrite)
        authStatus = ["notDetermined","restricted","denied","authorized","limited"][min(st.rawValue, 4)]
        libraryCount = PHAsset.fetchAssets(with: nil).count
    }

    private func requestAccess() {
        PHPhotoLibrary.requestAuthorization(for: .readWrite) { _ in
            DispatchQueue.main.async { refresh() }
        }
    }

    private func runProbes() {
        DispatchQueue.global().async {
            let r = PhotoKitProbes.run()
            PhotoKitProbes.write(r)
            DispatchQueue.main.async {
                note("probes: auth=\(r.authorizationStatus) visible=\(r.totalAssetsVisible) cloudOnly=\(r.cloudOnlyAssetsSampled) usableThumb=\(r.cloudOnlyThumbnailUsable)")
                for n in r.notes { note("NOTE " + n) }
            }
        }
    }

    private func start(resume: Bool) {
        runner.storageState = storageState
        runner.chipLabel = chip
        note(resume ? "resume run started" : "cold run started")
        runner.runCold(resume: resume)
    }

    private func startIncremental() {
        runner.storageState = storageState
        runner.chipLabel = chip
        note("incremental run started")
        runner.runIncremental()
    }

    /// A4 sub-test: modify an EXISTING asset and confirm the tracker notices.
    /// A creationDate-ordered walk cannot detect this; the change token must.
    private func editForA4() {
        runner.editOldestSyntheticAssetForA4 { msg in
            note("A4-edit: " + msg)
        }
    }

    private func stall() {
        runner.measureFirstScreenStall { ms in
            note(String(format: "CD-2 first-screen stall: %.0f ms (target <= 3000)", ms))
        }
    }

    private func insertSynthetic() {
        guard let n = Int(syntheticTarget), let ratio = Double(screenshotRatio) else { return }
        note("inserting \(n) synthetic assets…")
        SyntheticCorpus.insert(count: n, screenshotRatio: ratio, store: runner.storeRef,
                               progress: { done in
            if done % 500 == 0 { note("inserted \(done)") }
        }, completion: { total, err in
            note(err == nil ? "inserted \(total) synthetic assets" : "insert FAILED: \(err!)")
            refresh()
        })
    }

    private func cleanupSynthetic() {
        note("deleting tracked synthetic assets…")
        SyntheticCorpus.cleanup(store: runner.storeRef) { n, err in
            note(err == nil ? "deleted \(n) synthetic assets" : "cleanup FAILED: \(err!)")
            note("V-5: now check Photos > Recently Deleted and confirm they are restorable.")
            refresh()
        }
    }
}

struct ShareSheet: UIViewControllerRepresentable {
    let items: [Any]
    func makeUIViewController(context: Context) -> UIActivityViewController {
        UIActivityViewController(activityItems: items, applicationActivities: nil)
    }
    func updateUIViewController(_ vc: UIActivityViewController, context: Context) {}
}
