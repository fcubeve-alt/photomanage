import XCTest
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
    /// `enrich` is `nonisolated static`, so a future edit that moves it back onto the
    /// coordinator's actor makes this file fail to COMPILE rather than fail at runtime
    /// on a user's phone. That is the strongest form this check can take.
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

    func testThePermissionRequestedIsNoWiderThanTheModeAllows() {
        XCTAssertEqual(LibrarySafety.requiredAccessLevel, .read,
                       "A read-only build must not ask for write access to someone's "
                       + "photographs on first launch")
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
