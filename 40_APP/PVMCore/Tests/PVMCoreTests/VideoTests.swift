import XCTest
@testable import PVMCore

/// The delta gate and what a video leaves behind.
/// Ported from `30_ENGINE/pvm/deltas.py` and the video half of `tests/test_memory.py`.
///
/// L1-B is blunt about the design this replaces: 任何"把所有照片、所有视频帧全部交给重型
/// 模型理解"的架构，原则上都应视为错误设计. These tests are what stops that architecture
/// creeping back in as a threshold change.

private func vDate(_ y: Int, _ m: Int, _ d: Int, _ h: Int = 9) -> Date {
    var c = DateComponents(); c.year = y; c.month = m; c.day = d; c.hour = h
    var cal = Calendar(identifier: .gregorian)
    cal.timeZone = TimeZone(identifier: "UTC")!
    return cal.date(from: c)!
}

/// A minute at 30 fps: a static opening shot, a twenty-frame cut at ten seconds, back
/// to the opening shot, then a different closing scene.
private func minuteOfVideo() -> [Frame] {
    (0..<1800).map { i -> Frame in
        let h: UInt64
        switch i {
        case ..<300:   h = 0x1111_1111_1111_1111
        case ..<320:   h = 0xFFFF_0000_FFFF_0000
        case ..<1500:  h = 0x1111_1111_1111_1111
        default:       h = 0x0F0F_F0F0_0F0F_F0F0
        }
        return Frame(index: i, dhash: h, timestampSeconds: Double(i) / 30.0)
    }
}

private func videoAsset() -> AssetSignals {
    var a = AssetSignals(assetID: "vid")
    a.createdAt = vDate(2025, 4, 12)
    a.isVideo = true
    a.durationSeconds = 60
    a.pixelW = 1920; a.pixelH = 1080; a.byteSize = 40_000_000
    a.contentHash = "sha::vid"
    a.dhash = 0xAAAA_BBBB_CCCC_DDDD
    a.source = "camera"
    a.geo = GeoFix(lat: 35.6762, lon: 139.6503)
    a.place = PlaceName(country: "Japan", city: "Tokyo", confidence: 0.9)
    a.faceClusters = [FaceCluster(clusterID: "c-anna", name: "Anna")]
    return a
}

final class DeltaGateTests: XCTestCase {

    /// The correction that matters. Comparing each frame with the one before it fails
    /// on a slow pan: every adjacent pair is similar, so nothing is ever processed,
    /// while frame 1 and frame 500 are different scenes entirely.
    func testDriftIsMeasuredFromTheLastFrameActuallyLookedAt() {
        // One bit flips every ten frames — invisible pairwise, obvious cumulatively.
        var hash: UInt64 = 0
        let frames = (0..<400).map { i -> Frame in
            if i % 10 == 0, i > 0 { hash |= (1 << UInt64(i / 10 % 63)) }
            return Frame(index: i, dhash: hash | 1, timestampSeconds: Double(i) / 30)
        }
        let result = Deltas.selectKeyframes(frames)
        let drifted = result.decisions.filter { $0.reason.hasPrefix("drifted") }
        XCTAssertFalse(drifted.isEmpty,
                       "a slow pan must eventually open a new keyframe; comparing "
                       + "pairwise it never would")
    }

    /// FC-1a: dHash returns 0 both for a class of ordinary images and for every
    /// failure, so a failed hash is indistinguishable from a perfect match — and a
    /// perfect match is what authorises a skip.
    func testAnUnusableHashAlwaysProcesses() {
        let frames = (0..<50).map { Frame(index: $0, dhash: $0 == 20 ? 0 : 0x1111_1111_1111_1111) }
        let result = Deltas.selectKeyframes(frames)
        let twenty = result.decisions.first { $0.index == 20 }
        XCTAssertEqual(true, twenty?.process,
                       "skipping on a hash failure is the one bug here that would be "
                       + "invisible in testing and unrecoverable in the field")
    }

    /// Page 1 and page 2 of a contract are visually near-identical and semantically
    /// unrelated. Visual similarity may never skip text extraction on documents.
    func testDocumentContentIsNeverSkipped() {
        let frames = (0..<50).map { Frame(index: $0, dhash: 0x1111_1111_1111_1111) }
        let result = Deltas.selectKeyframes(frames, isDocument: true)
        XCTAssertEqual(result.total, result.processed)
    }

    func testTheFirstAndLastFrameAreAlwaysProcessed() {
        let frames = (0..<50).map { Frame(index: $0, dhash: 0x1111_1111_1111_1111) }
        let result = Deltas.selectKeyframes(frames)
        XCTAssertTrue(result.keyframes.contains(0))
        XCTAssertTrue(result.keyframes.contains(49),
                      "a sequence whose end was never looked at is one we cannot describe")
    }

    func testAStaticShotIsStillSampledPeriodically() {
        let frames = (0..<200).map { Frame(index: $0, dhash: 0x1111_1111_1111_1111) }
        let result = Deltas.selectKeyframes(frames)
        XCTAssertGreaterThan(result.processed, 2, "insurance against drift under the "
                             + "threshold forever")
        XCTAssertLessThan(result.processed, 20, "and it must still be a saving")
    }

    func testItSavesRealWork() {
        let result = Deltas.selectKeyframes(minuteOfVideo())
        let cost = Deltas.estimateCost(result)
        XCTAssertLessThan(result.processed, 100,
                          "1,800 frames through a full model is the design L1-B calls "
                          + "wrong on principle")
        XCTAssertGreaterThan(cost.savedFraction, 0.8)
    }

    /// The gate is the only place that knows which keyframes were changes and which
    /// were periodic re-checks, and segments depend on the difference.
    func testNewContentFramesExcludeTheHeartbeatSamples() {
        let result = Deltas.selectKeyframes(minuteOfVideo())
        XCTAssertLessThan(result.newContentFrames.count, result.keyframes.count,
                          "a static minute is sampled repeatedly; those are not changes")
        XCTAssertTrue(result.newContentFrames.contains(300),
                      "the cut at ten seconds is new content")
    }
}

/// The bug this locks out: the gate takes a keyframe every thirty frames even inside a
/// completely static shot, so its keyframes are almost never consecutive — and grouping
/// by adjacency turned a sixty-second video into sixty-one zero-length "segments". A
/// list of instants is exactly the pile of frames L1-B §4 says a video must not leave.
final class VideoSegmentTests: XCTestCase {

    func testAHeartbeatSampleExtendsASegmentRatherThanEndingIt() {
        let record = VideoMemory.record(asset: videoAsset(), keyframes: [0, 30, 60, 90, 120],
                                        frameRate: 30, newContentAt: [0, 90])
        XCTAssertEqual(2, record.segments.count,
                       "one shot then a cut — two spans, not five instants")
        XCTAssertEqual(0.0, record.segments[0].lowerBound, accuracy: 1e-9)
        XCTAssertEqual(3.0, record.segments[0].upperBound, accuracy: 1e-9)
        XCTAssertEqual(4.0, record.segments[1].upperBound, accuracy: 1e-9)
    }

    func testNoSegmentIsZeroLength() {
        let record = VideoMemory.record(asset: videoAsset(), keyframes: [0, 30, 60, 90],
                                        frameRate: 30, newContentAt: [0])
        for span in record.segments {
            XCTAssertGreaterThan(span.upperBound, span.lowerBound,
                                 "a span the user cannot scrub to is not a span")
        }
    }

    /// Callers holding only indices, with no record of why each was taken, get the
    /// honest reading of that input.
    func testTheBareIndexFormStillGroupsByAdjacency() {
        let record = VideoMemory.record(asset: videoAsset(), keyframes: [0, 1, 2, 90, 91],
                                        frameRate: 30)
        XCTAssertEqual(2, record.segments.count)
    }
}

/// Losing a distinction in the formatter, after taking the trouble to keep it in the
/// record, is the same failure one layer out.
final class SpanFormattingTests: XCTestCase {

    func testASubSecondSpanDoesNotRenderAsNothing() {
        XCTAssertEqual("00:10.0–00:10.7", formatSpan(10.0, 10.667),
                       "a cut lasting two thirds of a second printed as 00:10–00:10, "
                       + "which reads as no span at all")
    }

    func testALongSpanStaysInWholeSeconds() {
        XCTAssertEqual("02:05–03:11", formatSpan(125.0, 190.5))
    }

    /// Python rounds halves to even and Swift's `.rounded()` rounds them away from
    /// zero, so 190.5 seconds printed 03:10 in the engine and 03:11 in the app. Only
    /// ever visible on an exact half, and very hard to find from a screenshot — the
    /// Linux job found it in fifty seconds. Both now round half away from zero.
    func testAnExactHalfRoundsTheSameWayInBothImplementations() {
        XCTAssertEqual("00:00–00:11", formatSpan(0.0, 10.5))
        XCTAssertEqual("00:00–00:13", formatSpan(0.0, 12.5))
    }

    func testTheMinuteCarriesAfterRoundingNotBefore() {
        XCTAssertEqual("00:50.0–01:00.0", formatSpan(50.0, 59.967),
                       "splitting before rounding prints 00:60.0")
    }
}

/// B4-RECORD's production half: video reaching `Pipeline.run`.
final class VideoReachesThePipelineTests: XCTestCase {

    private var directory: URL!

    override func setUpWithError() throws {
        directory = URL(fileURLWithPath: NSTemporaryDirectory())
            .appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: directory,
                                                withIntermediateDirectories: true)
    }

    override func tearDownWithError() throws {
        try? FileManager.default.removeItem(at: directory)
    }

    private func run(framesFor: ((AssetSignals) -> [Frame])?) throws
        -> (RunStats, [Catalog.VideoRow]) {
        // No explicit close: `Catalog` releases its handle in `deinit`, and the
        // temporary directory goes with it in tearDown.
        let catalog = try XCTUnwrap(
            Catalog(path: directory.appendingPathComponent("c.sqlite").path))
        let stats = Pipeline.run(assets: [videoAsset()], catalog: catalog,
                                 framesFor: framesFor)
        return (stats, catalog.videoRecords())
    }

    func testAVideoLeavesARecordAndMostFramesAreNeverProcessed() throws {
        let frames = minuteOfVideo()
        let (stats, rows) = try run(framesFor: { _ in frames })

        XCTAssertEqual(1, stats.videos)
        XCTAssertEqual(1800, stats.videoFramesSeen)
        XCTAssertLessThan(stats.videoFramesProcessed, 100)
        XCTAssertGreaterThan(stats.videoMillisecondsSaved, 0)

        XCTAssertEqual(1, rows.count)
        let segments = rows[0].segments
        XCTAssertEqual(4, segments.count, "expected four spans, got \(segments)")
        // The cut is twenty frames at 30 fps, starting at ten seconds.
        XCTAssertEqual(10.0, segments[1][0], accuracy: 0.01)
        XCTAssertEqual(10.667, segments[1][1], accuracy: 0.01)
    }

    func testTheRecordCarriesWhoAndWhereNotJustFrames() throws {
        let frames = minuteOfVideo()
        let (_, rows) = try run(framesFor: { _ in frames })
        XCTAssertEqual("Tokyo", rows[0].place)
        XCTAssertEqual(["Anna"], rows[0].people)
    }

    /// Not the same as a video with no new information. Writing an empty record would
    /// claim the opposite of what happened.
    func testAVideoWhoseFramesCannotBeReadLeavesNoRecord() throws {
        let (stats, rows) = try run(framesFor: { _ in [] })
        XCTAssertEqual(0, stats.videos)
        XCTAssertTrue(rows.isEmpty)
    }

    func testWithoutAFrameSourceTheRunDoesNotImplyItLooked() throws {
        let (stats, rows) = try run(framesFor: nil)
        XCTAssertEqual(0, stats.videos)
        XCTAssertTrue(rows.isEmpty)
    }

    /// A caller sampling every tenth frame of a 30 fps video is giving us 3 fps, and
    /// using the file's rate would name the wrong seconds of the user's own video.
    func testFrameRateComesFromTheFramesHandedIn() {
        let sampled = stride(from: 0, to: 1800, by: 10).map {
            Frame(index: $0, dhash: 0x1111_1111_1111_1111, timestampSeconds: Double($0) / 30)
        }
        XCTAssertEqual(30.0, Pipeline.frameRate(sampled, videoAsset()), accuracy: 0.01,
                       "timestamps say 30 fps of source frames, whatever the sampling")
    }
}
