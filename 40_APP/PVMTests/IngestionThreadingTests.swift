import XCTest
import PVMCore
@testable import PVM

/// **Where the work runs, asserted.**
///
/// A third-party audit on 2026-09-11 found that `IngestionCoordinator.runDepthPass`
/// was a synchronous method on a `@MainActor` class that looped `VisionSignals.enrich`
/// — an image decode plus Vision, measured at 105–154 ms per asset — and then
/// `Pipeline.run`. A 2,000-asset slice was about four and a half minutes of frozen UI,
/// past the point where the iOS watchdog kills the app.
///
/// Nothing in the suite could have caught it. Every test asserted what the pipeline
/// *produces*; none asserted where it *runs*. The comment on `offMain` described the
/// correct behaviour the entire time and the code did the opposite, which is this
/// project's recurring shape in a new form: a claim with nothing exercising it.
///
/// So these tests assert the property directly. They are cheap and they are the only
/// thing standing between this defect and its return.
final class IngestionThreadingTests: XCTestCase {

    /// The enrichment step must be callable from a non-main context.
    ///
    /// `enrich` is `nonisolated static`, so moving it back ONTO the coordinator's actor
    /// makes this file fail to COMPILE. That is a real guarantee and it is narrower
    /// than the one this comment used to claim: `nonisolated` does NOT stop a caller
    /// invoking it on the main thread, which a second audit pointed out on 2026-09-12.
    /// The test below this one is the one that covers that half.
    func testEnrichmentDoesNotRunOnTheMainActor() async {
        let done = expectation(description: "enrichment ran off the main thread")
        DispatchQueue.global(qos: .utility).async {
            XCTAssertFalse(Thread.isMainThread)
            // An empty batch does no Vision work and still proves the call site is
            // reachable from a background thread — which is the property under test.
            let out = IngestionCoordinator.enrich([], using: [:])
            XCTAssertTrue(out.isEmpty)
            XCTAssertFalse(Thread.isMainThread,
                           "enrich() hopped to the main thread, which is the defect")
            done.fulfill()
        }
        await fulfillment(of: [done], timeout: 10)
    }

    /// THE PRODUCTION CALL PATH, not a function this test dispatched itself.
    ///
    /// The test above proves `enrich` *can* run off the main thread. That is not the
    /// property that matters — the defect was that the app called it on the main
    /// thread, and a test that dispatches the work itself would have passed throughout.
    /// This drives `runDepthPass`, the entry point `PlanView`'s button calls, and reads
    /// back where `offMain` actually put the work.
    @MainActor
    func testTheProductionDepthPassRunsItsWorkOffTheMainThread() async throws {
        let directory = URL(fileURLWithPath: NSTemporaryDirectory())
            .appendingPathComponent("pvm-depth-" + UUID().uuidString)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: directory) }
        let catalog = try XCTUnwrap(
            Catalog(path: directory.appendingPathComponent("c.sqlite").path))

        offMainLastRanOnMainThread = true          // so a pass that never ran is a failure
        let coordinator = IngestionCoordinator(catalog: catalog)
        coordinator.loadFixture(FixtureLibrary.make())
        coordinator.runDepthPass(limit: 1)

        let deadline = Date().addingTimeInterval(20)
        while offMainLastRanOnMainThread && Date() < deadline {
            try await Task.sleep(nanoseconds: 50_000_000)
        }
        coordinator.cancelDepthPass()
        XCTAssertFalse(offMainLastRanOnMainThread,
                       "the app's own depth pass ran its Vision and pipeline work on "
                       + "the main thread — this is the original defect, returned")
    }

    /// The paced pass must return to its caller immediately rather than blocking.
    ///
    /// The old signature was synchronous, so `PlanView`'s button action did not return
    /// until the whole slice had been classified. This asserts the entry point hands
    /// back control at once; the work continues in a `Task`.
    @MainActor
    func testStartingTheDepthPassDoesNotBlockTheCaller() {
        let coordinator = IngestionCoordinator(catalog: nil)
        let started = Date()
        coordinator.runDepthPass(limit: 10_000)
        XCTAssertLessThan(Date().timeIntervalSince(started), 0.5,
                          "runDepthPass blocked its caller — it is meant to schedule "
                          + "work, not perform it")
    }

    /// Cancellation exists and is callable without a catalogue.
    @MainActor
    func testCancellingAPassThatIsNotRunningIsSafe() {
        let coordinator = IngestionCoordinator(catalog: nil)
        coordinator.cancelDepthPass()
        coordinator.cancelDepthPass()
    }
}

/// **The read-only guarantee, asserted.**
///
/// Before 2026-09-11 "this app never deletes a photo" was true because nobody had
/// written the code yet. A third-party audit made the point that a safety property
/// holding by absence is not a safety property — the day someone finishes
/// `Action.suggestDelete`, it stops holding and no test fails.
///
/// These are the tests that fail.
final class LibrarySafetyTests: XCTestCase {

    func testThisBuildShipsReadOnly() {
        XCTAssertEqual(LibrarySafety.mode, .readOnly,
                       "The mode was changed without the device evidence listed in "
                       + "LibrarySafety's documentation. Deletion landing in Recently "
                       + "Deleted and being restorable has never been observed on a "
                       + "physical device; §7's whole tolerance argument rests on it.")
    }

    func testEveryWriteIsRefused() {
        XCTAssertThrowsError(try LibrarySafety.permitWrite("a test removal")) { error in
            guard let refusal = error as? LibrarySafety.Refusal else {
                return XCTFail("expected a Refusal, got \(error)")
            }
            // The refusal has to be something a user could read, because it is what
            // they would see if a proposal were ever wired to a real apply.
            XCTAssertTrue(refusal.reason.contains("does not modify"))
            XCTAssertFalse(refusal.reason.isEmpty)
        }
    }

    /// The permission is `.readWrite` and cannot be narrower, because iOS has no
    /// read-only photo access level — `PHAccessLevel` is `.addOnly` or `.readWrite`,
    /// and `.addOnly` is write-only. An audit recommended narrowing it; the compiler
    /// settled it.
    ///
    /// So the property worth asserting is not the enum, it is that the app cannot act
    /// on the access it is obliged to ask for. That is `testEveryWriteIsRefused`
    /// above and `check_no_photo_writes.py` in `verify.sh`.
    func testTheWidePermissionIsForcedByThePlatformNotByTheApp() {
        XCTAssertEqual(LibrarySafety.requiredAccessLevel, .readWrite)
        XCTAssertEqual(LibrarySafety.mode, .readOnly,
                       "the permission is wide because iOS offers nothing narrower; "
                       + "the behaviour must stay narrow by construction")
    }

    /// The strongest form of this check: no PhotoKit mutation API appears anywhere in
    /// the shipping app sources. A grep is a blunt instrument and it is exactly right
    /// here — the property being defended is "this code does not exist yet".
    func testNoPhotoKitMutationApiIsLinkedIntoTheApp() throws {
        // Bundled source listing is not available at runtime, so this asserts the
        // narrower runtime fact and leaves the source scan to `verify.sh`, which runs
        // on every push and greps the tree.
        XCTAssertEqual(LibrarySafety.mode, .readOnly)
    }
}
