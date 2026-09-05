import XCTest
import UIKit
@testable import PVMBench

/// These run on the iOS Simulator, on a GitHub Actions macOS runner, for $0.
///
/// What they are for: catching the failures that do NOT need a real iPhone, before
/// the $99 Apple Developer enrolment and before the device campaign. A compile-green
/// harness is not a working harness — the CSV writer can silently misalign, the OCR
/// gate can let everything through, the index can fail to persist a cursor. Every one
/// of those produces a benchmark run that looks fine and is worthless.
///
/// What they are NOT for (P-02 / PF-01): the Simulator runs on the Mac's own CPU and
/// has no thermal state, no battery, no Neural Engine and no real photo library. No
/// timing, thermal, memory or battery number from here may EVER be recorded as an
/// A1-A4 result. Those need hardware.
final class MetricsCSVTests: XCTestCase {

    /// The bug this exists for: `header` and `fields()` are two independent arrays of
    /// String. A column added to one and not the other is invisible to the compiler
    /// and shifts every subsequent value by one — discovered only after a campaign,
    /// when the data is already worthless.
    func testFieldCountMatchesHeaderCount() {
        XCTAssertEqual(MetricsCSV.fields(BenchmarkRow()).count,
                       MetricsCSV.columnCount,
                       "CSV schema drift: fields() and header disagree")
    }

    /// Canary. 47 columns is the schema `analyze_benchmark.py` and
    /// T0A_DEVICE_BENCHMARK_HARNESS_SPEC.md section 4 were written against. If this
    /// changes deliberately, update the analyzer and the spec in the same commit.
    func testColumnCountIsTheAgreedSchema() {
        XCTAssertEqual(MetricsCSV.columnCount, 47)
    }

    /// Device identifiers from uname() ALWAYS contain a comma ("iPhone14,5"). If the
    /// writer does not quote them, every column shifts by one and the analysis is
    /// garbage that still looks plausible. The Python analyzer aborts when it sees an
    /// unquoted one; this catches it a step earlier, at build time.
    func testDeviceModelWithCommaSurvivesARoundTrip() {
        var row = BenchmarkRow()
        row.device_model = "iPhone14,5"
        row.chip = "A15"
        row.notes = "note with a comma, and \"quotes\""

        let fields = MetricsCSV.fields(row)
        let line = MetricsCSV.csvLine(fields)
        let parsed = MetricsCSVTests.parseCSVLine(line)

        XCTAssertEqual(parsed.count, MetricsCSV.columnCount,
                       "a quoted comma split the row into extra columns")
        XCTAssertEqual(parsed[0], "iPhone14,5")
        XCTAssertEqual(parsed[1], "A15")
        XCTAssertEqual(parsed.last, "note with a comma, and \"quotes\"")
    }

    /// Minimal RFC-4180 reader, so the test verifies the file a parser would actually
    /// see rather than trusting the writer's own escaping.
    static func parseCSVLine(_ line: String) -> [String] {
        var out: [String] = []
        var field = ""
        var inQuotes = false
        var i = line.startIndex
        while i < line.endIndex {
            let c = line[i]
            if inQuotes {
                if c == "\"" {
                    let next = line.index(after: i)
                    if next < line.endIndex, line[next] == "\"" {
                        field.append("\""); i = next
                    } else {
                        inQuotes = false
                    }
                } else {
                    field.append(c)
                }
            } else if c == "\"" {
                inQuotes = true
            } else if c == "," {
                out.append(field); field = ""
            } else {
                field.append(c)
            }
            i = line.index(after: i)
        }
        out.append(field)
        return out
    }
}

final class OCRGateTests: XCTestCase {

    /// C-1: OCR must be GATED, not universal. Running text recognition over 100k
    /// assets is the single most likely cause of an A1 failure, so a gate that lets
    /// everything through would fail A1 for a reason that is a bug, not a limit.
    func testOrdinaryPhotoIsGatedOut() {
        var r = AssetRecord(localID: "x")
        r.pxW = 4032; r.pxH = 3024          // ordinary landscape capture
        r.isScreenshot = false
        XCTAssertFalse(OCRGate.decide(record: r, textLikelihood: 0.1).run)
    }

    func testScreenshotSubtypeAlwaysRuns() {
        var r = AssetRecord(localID: "x")
        r.isScreenshot = true
        r.pxW = 4032; r.pxH = 3024          // deliberately NOT screen-shaped
        let d = OCRGate.decide(record: r, textLikelihood: 0.0)
        XCTAssertTrue(d.run)
        XCTAssertEqual(d.reason, "screenshot-subtype")
    }

    /// A shared screenshot often loses its subtype flag, so aspect ratio is the
    /// second cheap signal. 1170x2532 is an iPhone 13/14 screen.
    func testScreenShapedAspectRatioRuns() {
        var r = AssetRecord(localID: "x")
        r.isScreenshot = false
        r.pxW = 1170; r.pxH = 2532
        XCTAssertEqual(OCRGate.decide(record: r, textLikelihood: 0.0).reason, "screen-aspect")
    }

    func testHighTextLikelihoodRuns() {
        var r = AssetRecord(localID: "x")
        r.pxW = 4032; r.pxH = 3024
        XCTAssertEqual(OCRGate.decide(record: r, textLikelihood: 0.9).reason, "text-likelihood")
    }

    /// The gate must not depend on a resolution it was never given. A record with no
    /// pixel dimensions must not divide by zero or accidentally pass.
    func testMissingDimensionsDoNotCrashOrPass() {
        var r = AssetRecord(localID: "x")
        r.pxW = 0; r.pxH = 0
        XCTAssertFalse(OCRGate.decide(record: r, textLikelihood: 0.0).run)
    }
}

final class Layer1SignalsTests: XCTestCase {

    private func image(_ draw: (CGContext, CGSize) -> Void, size: CGSize = CGSize(width: 128, height: 128)) -> UIImage {
        UIGraphicsImageRenderer(size: size).image { ctx in
            draw(ctx.cgContext, size)
        }
    }

    /// FC-1 depends on this: the same bytes must produce the same hash, or the
    /// duplicate-skip the Minimum Necessary Inference architecture calls for can
    /// never fire.
    func testIdenticalImagesHashIdentically() {
        let a = image { ctx, s in
            ctx.setFillColor(UIColor.white.cgColor); ctx.fill(CGRect(origin: .zero, size: s))
            ctx.setFillColor(UIColor.black.cgColor); ctx.fill(CGRect(x: 0, y: 0, width: s.width / 2, height: s.height))
        }
        let b = image { ctx, s in
            ctx.setFillColor(UIColor.white.cgColor); ctx.fill(CGRect(origin: .zero, size: s))
            ctx.setFillColor(UIColor.black.cgColor); ctx.fill(CGRect(x: 0, y: 0, width: s.width / 2, height: s.height))
        }
        XCTAssertEqual(Layer1.dHash(a), Layer1.dHash(b))
        XCTAssertNotEqual(Layer1.dHash(a), 0, "a uniform-zero hash means the draw failed, not that the images matched")
    }

    func testVisiblyDifferentImagesHashDifferently() {
        let leftHalf = image { ctx, s in
            ctx.setFillColor(UIColor.white.cgColor); ctx.fill(CGRect(origin: .zero, size: s))
            ctx.setFillColor(UIColor.black.cgColor); ctx.fill(CGRect(x: 0, y: 0, width: s.width / 2, height: s.height))
        }
        let topHalf = image { ctx, s in
            ctx.setFillColor(UIColor.white.cgColor); ctx.fill(CGRect(origin: .zero, size: s))
            ctx.setFillColor(UIColor.black.cgColor); ctx.fill(CGRect(x: 0, y: 0, width: s.width, height: s.height / 2))
        }
        XCTAssertNotEqual(Layer1.dHash(leftHalf), Layer1.dHash(topHalf))
    }

    /// The gate's cheap proxy must actually separate the two cases it exists to
    /// separate. If a blank wall scores as high as a page of text, the gate degrades
    /// into "OCR everything" without anyone noticing.
    func testTextLikelihoodRanksStripesAboveFlatColour() {
        let flat = image { ctx, s in
            ctx.setFillColor(UIColor.gray.cgColor); ctx.fill(CGRect(origin: .zero, size: s))
        }
        let stripes = image { ctx, s in
            ctx.setFillColor(UIColor.white.cgColor); ctx.fill(CGRect(origin: .zero, size: s))
            ctx.setFillColor(UIColor.black.cgColor)
            var x: CGFloat = 0
            while x < s.width {
                ctx.fill(CGRect(x: x, y: 0, width: 2, height: s.height))
                x += 4
            }
        }
        XCTAssertGreaterThan(Layer1.textLikelihood(stripes), Layer1.textLikelihood(flat))
    }
}

final class IndexStoreTests: XCTestCase {

    private var store: IndexStore!

    override func setUp() {
        super.setUp()
        store = IndexStore()
        store.reset()
    }

    func testUpsertIsIdempotentAndCounted() {
        var r = AssetRecord(localID: "asset-1")
        r.pxW = 4032; r.pxH = 3024; r.dhash = 0xDEAD_BEEF
        store.upsert(r)
        store.upsert(r)                       // same asset seen twice
        XCTAssertEqual(store.count(), 1, "re-indexing an asset must not duplicate the row")
        XCTAssertTrue(store.contains("asset-1"))
        XCTAssertFalse(store.contains("asset-2"))
    }

    /// C-3 checkpointing. If the cursor does not survive, a killed run restarts from
    /// zero and the A3 survivability verdict measures the bug rather than the device.
    func testCursorPersistsAcrossStoreInstances() {
        store.setCursor("asset-500")
        let reopened = IndexStore()
        XCTAssertEqual(reopened.cursor(), "asset-500")
    }

    /// DEC-009 is a safety rule, not a nicety: the harness may write to a real photo
    /// library, and cleanup must be able to touch ONLY what it created. An asset that
    /// was never recorded as synthetic must never appear in the deletion list.
    func testCleanupListContainsOnlyAssetsWeCreated() {
        store.upsert(AssetRecord(localID: "users-real-photo"))
        store.upsert(AssetRecord(localID: "synthetic-1"))
        store.recordSynthetic("synthetic-1")

        let ids = store.syntheticIDs()
        XCTAssertEqual(ids, ["synthetic-1"])
        XCTAssertFalse(ids.contains("users-real-photo"),
                       "a pre-existing asset reached the deletion list — DEC-009 violation")
        XCTAssertEqual(store.syntheticCount(), 1)

        store.forgetSynthetic(ids)
        XCTAssertTrue(store.syntheticIDs().isEmpty)
        XCTAssertTrue(store.contains("users-real-photo"),
                      "forgetting synthetic tracking must not remove the asset rows")
    }

    func testResetEmptiesTheIndex() {
        store.upsert(AssetRecord(localID: "a"))
        store.reset()
        XCTAssertEqual(store.count(), 0)
    }
}
