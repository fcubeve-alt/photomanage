# PVM Bench — Tier 0-A device benchmark harness

**Status: WRITTEN ON WINDOWS, NEVER COMPILED.** No Mac, no Xcode, no device.
Expect compile errors on first build — that is the point: fixing them on the cloud Mac
is minutes, writing this from scratch there would have been hours.

Implements `../T0A_DEVICE_BENCHMARK_HARNESS_SPEC.md`:
§4 CSV schema · §5 C-1…C-5 design constraints · §7 V-1…V-5 PhotoKit probes · §7A CD-1…CD-5.

**PF-01: this harness produces measured values only.** No prediction or model output
may ever be written into `DEVICE_BENCHMARK_TIER0.csv`.

## Files

| File | Role | Spec |
|---|---|---|
| `Telemetry.swift` | thermal **dwell time**, footprint, CPU, battery, expirations | §4 |
| `MetricsCSV.swift` | the exact §4 column order, append-only | §4 |
| `IndexStore.swift` | raw SQLite3, WAL, checkpoint cursor, synthetic tracking | C-3, DEC-009 |
| `Layer1Signals.swift` | metadata, dHash, text-likelihood proxy | §25 L1 |
| `OCRGate.swift` | gated OCR — the likely A1 decider | **C-1** |
| `EmbeddingStage.swift` | Apple-native feature print, **zero bundled model** | §25 L2, P-04 |
| `AssetIndexer.swift` | per-asset pipeline, thumbnails only, network denied | **C-2** |
| `BenchmarkRunner.swift` | cold / resume / incremental / first-screen stall | A1–A4, CD-2 |
| `SyntheticCorpus.swift` | insert + cleanup, tracked ids only | **DEC-009** |
| `BackgroundIndexing.swift` | BGProcessingTask with expiration logging | **C-4** |
| `PhotoKitProbes.swift` | V-1…V-5 | §7 |
| `PVMBenchApp.swift`, `ContentView.swift` | operator console | — |

## Deliberate choices worth not undoing

- **`isNetworkAccessAllowed = false`** everywhere (C-2). Requesting originals on an
  iCloud-optimised library measures the user's Wi-Fi, not the phone, and could
  produce a spurious A1 failure that falsely kills the project.
- **Apple-native `VNGenerateImageFeaturePrintRequest`** for L2 — no bundled model,
  zero binary growth. P-04 says test native first; a heavy model must now beat a
  shipped 262 MB baseline, not merely work.
- **Raw SQLite3, no SPM dependency** — the cloud-Mac block is not spent resolving packages.
- **Realistic pixel dimensions (4032×3024) with heavy JPEG compression** for synthetic
  assets. Decode cost tracks pixel count; generating small images would flatter the result.
- **Thermal measured as dwell time**, not spot readings.
- **Footprint, not resident size** — Jetsam kills are footprint-driven.

## Setting up on the cloud Mac (~10 minutes)

There is no `.xcodeproj` here — a hand-written `pbxproj` is fragile and would waste
more time than it saves.

1. Xcode → **File ▸ New ▸ Project ▸ iOS ▸ App**. Product name `PVMBench`, interface
   **SwiftUI**, language **Swift**.
2. Delete the generated `ContentView.swift` and `PVMBenchApp.swift`.
3. Drag every `.swift` file from `PVMBench/` into the target ("Copy items if needed" on).
4. **Signing & Capabilities** → add **Background Modes** → tick **Background processing**.
5. **Info.plist** keys:
   - `NSPhotoLibraryUsageDescription` = `Tier 0-A benchmark: reads the photo library to measure indexing performance.`
   - `NSPhotoLibraryAddUsageDescription` = `Adds temporary synthetic test assets, which the app deletes again.`
   - `BGTaskSchedulerPermittedIdentifiers` = array containing `com.pvm.bench.index`
6. Deployment target **iOS 16.0** (matches the TestFlight floor; iPhone 7 is out of
   scope on verified evidence — see the environment plan Part 2).
7. **Build and run in the Simulator.** No signing identity is needed for this, which
   is exactly what makes the pre-payment check in DEC-015 possible.
8. **STOP and report build success.** Only then does the Owner enrol and pay the $99;
   archive + TestFlight upload happen afterwards.

## Run order on device (spec §5.4)

Cheapest information first — a flagship-first run proves the least.

1. Owner's daily driver, real library as-is → answers the **fatal** A3/A4.
2. Oldest TestFlight-capable device → where A1/A2 will break if anywhere.
3. Fill in the rest of the gradient.
4. Scale up with synthetic padding where storage allows.

Per device: cold index → **cancel mid-run** → resume → incremental → CD-2 stall →
probes. Then share the CSV out.

## Safety before touching a primary device

The synthetic corpus writes to a real photo library.

- Prove **insert and cleanup** on a secondary device with a disposable library first.
- Cleanup deletes only ids in the `synthetic` table. It never enumerates the library
  to guess what to remove.
- After the first cleanup, **verify V-5 by hand**: open Photos ▸ Recently Deleted,
  confirm the assets are there and restorable, and record the retention the system
  reports. **Do not assume 30 days.** The Constitution's entire automation argument
  (§7 — tolerate low-cost *recoverable* errors) is only valid if errors really are
  recoverable.

## Known gaps (honest list)

- Never compiled. API signatures, especially the mach/`task_info` bridging in
  `Telemetry.swift`, are the most likely to need adjustment.
- `chip` is entered by the operator; there is no model-identifier lookup table yet.
- Location inference from neighbouring assets (§11) is not implemented — Layer 1 only
  records a direct GPS fix with confidence 1.0. Inferred location belongs to Tier 1-D.
- The incremental path assumes newest-first ordering makes the first known asset a
  safe stopping point. That holds for newly captured assets but **not** for edits to
  old ones; `PHPhotoLibraryChangeObserver` is registered for that case but change-set
  handling is not wired in yet. Worth finishing before the A4 verdict is taken as final.
