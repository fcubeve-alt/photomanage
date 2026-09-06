import XCTest
import UIKit
import ImageIO
import Vision
@testable import PVMBench

/// T0-A SCALE SWEEP — the "how many photos can this thing actually take?" test.
///
/// WHAT THIS IS: the full per-asset indexing pipeline (thumbnail decode -> dHash ->
/// text-likelihood -> OCR gate -> gated OCR -> feature-print embedding -> SQLite
/// upsert with batch checkpoints) run over a growing synthetic corpus, with every
/// stage timed separately, so the cost per asset is known instead of guessed.
/// From a measured cost per asset, the maximum library size that fits a time budget
/// is arithmetic rather than opinion.
///
/// WHAT THIS IS NOT (P-02 / PF-01, and this is not a formality): the iOS Simulator
/// runs on the host Mac's CPU. It has no thermal state, no battery, no Neural Engine
/// and no real photo library. So:
///   - Nothing measured here is an A2 (thermal), A3 (survivability under jetsam) or
///     battery result. Those need hardware.
///   - The A1 throughput number here is an OPTIMISTIC CEILING for a phone, not a
///     phone number. A GitHub Actions macos-15 runner is a desktop-class arm64 part
///     with no thermal ceiling; an iPhone will be slower, and the Vision stages run
///     on the ANE on device and on the CPU here, so the two do not even fail the
///     same way.
///   - It is still the only A-shaped measurement available at $0 while HG-1 is open,
///     and a ceiling that is already too low would be decisive on its own.
///
/// HOW IT IS SELECTED, and why not an environment flag: the first attempt gated the
/// sweep on PVM_SCALE_BENCH=1 passed through TEST_RUNNER_. The run came back green
/// having measured nothing, because neither the gate nor the diagnostic `print` that
/// was supposed to explain it reached the log — stdout from a process inside the
/// Simulator does not appear in xcodebuild's output. So selection is now done with
/// flags xcodebuild is unambiguous about: `ios-build.yml` passes -skip-testing for
/// this class, `t0a-scale.yml` passes -only-testing. No environment variable decides
/// whether the measurement happens.
///
/// And the results are written to a FILE in the app container, which CI finds on the
/// runner's own disk, rather than printed. A measurement that cannot be read back is
/// not a measurement.
final class ScaleBenchmarkTests: XCTestCase {

    // MARK: - knobs

    private static func env(_ k: String) -> String? {
        let v = ProcessInfo.processInfo.environment[k]
        return (v?.isEmpty ?? true) ? nil : v
    }

    /// Corpus sizes to sweep. Small -> large so a timeout still leaves usable data.
    private var sizes: [Int] {
        (Self.env("PVM_SCALE_SIZES") ?? "200,1000,3000")
            .split(separator: ",").compactMap { Int($0.trimmingCharacters(in: .whitespaces)) }
    }

    /// Distinct source images. The pipeline re-decodes from JPEG data every time, so
    /// a modest pool still pays full decode cost per asset while keeping generation
    /// (which is NOT part of indexing and must not be timed) bounded.
    private var poolSize: Int { Int(Self.env("PVM_SCALE_POOL") ?? "48") ?? 48 }

    /// Fraction of the corpus that is text-bearing / screenshot-like. Drives the OCR
    /// gate ratio, which C-1 predicts is what actually decides A1.
    private var screenshotRatio: Double { Double(Self.env("PVM_SCALE_TEXT_RATIO") ?? "0.25") ?? 0.25 }

    /// C-3 checkpoint size.
    private var batchSize: Int { Int(Self.env("PVM_SCALE_BATCH") ?? "200") ?? 200 }

    // MARK: - the sweep

    func testScaleSweep() throws {
        var lines: [String] = []
        lines.append("PVM_SCALE_HOST \(hostDescription())")
        lines.append("PVM_SCALE_CONFIG sizes=\(sizes.map(String.init).joined(separator: "+")) "
                     + "pool=\(poolSize) text_ratio=\(screenshotRatio) batch=\(batchSize)")
        defer { writeResults(lines) }

        let pool = makePool()
        XCTAssertEqual(pool.count, poolSize, "corpus pool did not build")

        for n in sizes {
            let r = runPass(n: n, pool: pool)
            // One machine-readable line per size, appended as we go. The `defer`
            // above flushes whatever exists, so a sweep that dies at n=3000 still
            // leaves the n=200 and n=1000 measurements on disk. That is the whole
            // reason the sizes ascend.
            lines.append("PVM_SCALE_RESULT \(r.json)")
            writeResults(lines)

            // Guard rails, not budgets: these catch a broken measurement (a gate that
            // passes everything, an index that wrote nothing), never a slow phone.
            XCTAssertEqual(r.indexed, n, "not every asset reached the index")
            XCTAssertGreaterThan(r.ocrGatedOut, 0, "OCR gate let everything through — C-1 is not in effect")
            XCTAssertGreaterThan(r.ocrAttempted, 0, "OCR gate blocked everything — the sweep measures nothing")
        }
    }

    // MARK: - one pass

    private struct PassResult {
        var n = 0, indexed = 0, failed = 0
        var wallS = 0.0
        var decodeMS = 0.0, l1MS = 0.0, gateMS = 0.0, ocrMS = 0.0, embedMS = 0.0, storeMS = 0.0
        var ocrAttempted = 0, ocrGatedOut = 0, embedAttempted = 0
        var peakFootprintMB = 0.0, startFootprintMB = 0.0
        var indexBytes: Int64 = 0
        var embedBytes = 0

        var json: String {
            let perAsset = n > 0 ? wallS * 1000 / Double(n) : 0
            let f: (Double) -> String = { String(format: "%.3f", $0) }
            return """
            {"n":\(n),"indexed":\(indexed),"failed":\(failed),\
            "wall_s":\(f(wallS)),"ms_per_asset":\(f(perAsset)),\
            "assets_per_s":\(f(n > 0 && wallS > 0 ? Double(n) / wallS : 0)),\
            "decode_ms_per_asset":\(f(n > 0 ? decodeMS / Double(n) : 0)),\
            "l1_ms_per_asset":\(f(n > 0 ? l1MS / Double(n) : 0)),\
            "gate_ms_per_asset":\(f(n > 0 ? gateMS / Double(n) : 0)),\
            "ocr_ms_per_ocr_asset":\(f(ocrAttempted > 0 ? ocrMS / Double(ocrAttempted) : 0)),\
            "ocr_ms_per_asset":\(f(n > 0 ? ocrMS / Double(n) : 0)),\
            "embed_ms_per_asset":\(f(embedAttempted > 0 ? embedMS / Double(embedAttempted) : 0)),\
            "store_ms_per_asset":\(f(n > 0 ? storeMS / Double(n) : 0)),\
            "ocr_attempted":\(ocrAttempted),"ocr_gated_out":\(ocrGatedOut),\
            "ocr_gate_ratio":\(f(n > 0 ? Double(ocrAttempted) / Double(n) : 0)),\
            "embed_attempted":\(embedAttempted),\
            "start_footprint_mb":\(f(startFootprintMB)),"peak_footprint_mb":\(f(peakFootprintMB)),\
            "index_bytes_total":\(indexBytes),\
            "index_bytes_per_asset":\(f(indexed > 0 ? Double(indexBytes) / Double(indexed) : 0)),\
            "embedding_bytes_per_asset":\(f(embedAttempted > 0 ? Double(embedBytes) / Double(embedAttempted) : 0))}
            """
        }
    }

    private func runPass(n: Int, pool: [(data: Data, textLike: Bool, w: Int, h: Int)]) -> PassResult {
        let store = IndexStore()
        store.reset()

        var r = PassResult()
        r.n = n
        r.startFootprintMB = footprintMB()
        r.peakFootprintMB = r.startFootprintMB

        let t0 = CFAbsoluteTimeGetCurrent()
        store.beginBatch()

        for i in 0..<n {
            let src = pool[i % pool.count]

            var rec = AssetRecord(localID: "scale-\(n)-\(i)")
            rec.createdAt = 1_700_000_000 + Double(i) * 37
            rec.modifiedAt = rec.createdAt
            rec.mediaType = 1
            rec.isScreenshot = src.textLike
            rec.isSynthetic = true
            rec.pxW = src.w
            rec.pxH = src.h
            rec.byteSize = Int64(src.data.count)

            // C-2: a 256 px thumbnail decoded straight from the encoded bytes. This is
            // the closest honest stand-in for PHImageManager's fastFormat thumbnail
            // path without a real photo library. Full-resolution decode is exactly the
            // mistake the spec forbids, so it is not what is measured here.
            var td = CFAbsoluteTimeGetCurrent()
            guard let thumb = thumbnail(from: src.data, maxPixel: 256) else {
                r.failed += 1
                store.upsert(rec)
                continue
            }
            r.decodeMS += (CFAbsoluteTimeGetCurrent() - td) * 1000

            td = CFAbsoluteTimeGetCurrent()
            rec.dhash = Layer1.dHash(thumb)
            let likelihood = Layer1.textLikelihood(thumb)
            r.l1MS += (CFAbsoluteTimeGetCurrent() - td) * 1000

            td = CFAbsoluteTimeGetCurrent()
            let decision = OCRGate.decide(record: rec, textLikelihood: likelihood)
            r.gateMS += (CFAbsoluteTimeGetCurrent() - td) * 1000

            if decision.run {
                td = CFAbsoluteTimeGetCurrent()
                rec.ocrText = OCRGate.recognise(thumb)
                r.ocrMS += (CFAbsoluteTimeGetCurrent() - td) * 1000
                rec.ocrRan = true
                r.ocrAttempted += 1
            } else {
                r.ocrGatedOut += 1
            }

            td = CFAbsoluteTimeGetCurrent()
            rec.embedding = EmbeddingStage.featurePrint(thumb)
            r.embedMS += (CFAbsoluteTimeGetCurrent() - td) * 1000
            r.embedAttempted += 1
            r.embedBytes += rec.embedding?.count ?? 0

            td = CFAbsoluteTimeGetCurrent()
            store.upsert(rec)
            if (i + 1) % batchSize == 0 {
                store.setCursor(rec.localID)
                store.commitBatch()
                store.beginBatch()
            }
            r.storeMS += (CFAbsoluteTimeGetCurrent() - td) * 1000

            if i % 50 == 0 { r.peakFootprintMB = max(r.peakFootprintMB, footprintMB()) }
        }

        store.commitBatch()
        r.wallS = CFAbsoluteTimeGetCurrent() - t0
        r.peakFootprintMB = max(r.peakFootprintMB, footprintMB())
        r.indexed = store.count()
        r.indexBytes = store.sizeOnDisk()
        return r
    }

    // MARK: - corpus

    private func makePool() -> [(data: Data, textLike: Bool, w: Int, h: Int)] {
        var out: [(Data, Bool, Int, Int)] = []
        out.reserveCapacity(poolSize)
        for i in 0..<poolSize {
            let textLike = Double(i % 100) / 100.0 < screenshotRatio
            let img = SyntheticCorpus.makeImage(index: i, textLike: textLike)
            guard let data = img.jpegData(compressionQuality: 0.35) else { continue }
            out.append((data, textLike, Int(img.size.width), Int(img.size.height)))
        }
        return out
    }

    private func thumbnail(from data: Data, maxPixel: Int) -> UIImage? {
        guard let src = CGImageSourceCreateWithData(data as CFData, nil) else { return nil }
        let opts: [CFString: Any] = [
            kCGImageSourceCreateThumbnailFromImageAlways: true,
            kCGImageSourceCreateThumbnailWithTransform: true,
            kCGImageSourceShouldCacheImmediately: true,
            kCGImageSourceThumbnailMaxPixelSize: maxPixel
        ]
        guard let cg = CGImageSourceCreateThumbnailAtIndex(src, 0, opts as CFDictionary) else { return nil }
        return UIImage(cgImage: cg)
    }

    // MARK: - instrumentation

    /// Real footprint, the number jetsam actually looks at. On the Simulator there is
    /// no jetsam, so this is a shape check (does memory grow with N?), not a limit.
    private func footprintMB() -> Double {
        var info = task_vm_info_data_t()
        var count = mach_msg_type_number_t(MemoryLayout<task_vm_info_data_t>.size / MemoryLayout<natural_t>.size)
        let kr = withUnsafeMutablePointer(to: &info) {
            $0.withMemoryRebound(to: integer_t.self, capacity: Int(count)) {
                task_info(mach_task_self_, task_flavor_t(TASK_VM_INFO), $0, &count)
            }
        }
        return kr == KERN_SUCCESS ? Double(info.phys_footprint) / (1024 * 1024) : 0
    }

    /// Written into the host app's Documents directory inside the Simulator, which
    /// lives on the runner's real filesystem under
    /// ~/Library/Developer/CoreSimulator/Devices/<udid>/data/... — CI finds it there.
    private func writeResults(_ lines: [String]) {
        let dir = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let url = dir.appendingPathComponent("pvm_scale_results.txt")
        try? (lines.joined(separator: "\n") + "\n").write(to: url, atomically: true, encoding: .utf8)
    }

    private func hostDescription() -> String {
        let p = ProcessInfo.processInfo
        return "cores=\(p.processorCount) active=\(p.activeProcessorCount) "
             + "ram_gb=\(String(format: "%.1f", Double(p.physicalMemory) / 1_073_741_824)) "
             + "os=\(p.operatingSystemVersionString.replacingOccurrences(of: ",", with: ";"))"
    }
}
