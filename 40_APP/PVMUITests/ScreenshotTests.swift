import XCTest

/// Screenshots of the running app, captured on the Simulator and attached to the test
/// results so the UI can actually be looked at.
///
/// This exists because the app is being written on a machine with no Mac and no iPhone.
/// Without it, "the UI is built" would rest entirely on the fact that it compiles, which
/// is exactly the kind of claim PF-11 is about. A screenshot is not a device test — no
/// thermal, no jetsam, no real photo library — but it is the difference between having
/// seen the product and having imagined it.
///
/// The app is launched with `-PVMFixture`, which seeds a small deterministic library.
/// Same binary as the shipping one; it simply never runs that path in production.
final class ScreenshotTests: XCTestCase {

    private var app: XCUIApplication!

    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = ["-PVMFixture"]
        app.launch()
    }

    private func capture(_ name: String) {
        let screenshot = XCUIScreen.main.screenshot()
        let attachment = XCTAttachment(screenshot: screenshot)
        attachment.name = name
        attachment.lifetime = .keepAlways
        add(attachment)

        // Also written to disk. CI collects these off the runner's own filesystem,
        // because an attachment inside an .xcresult bundle is awkward to get at and a
        // screenshot nobody can open is not evidence.
        let dir = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        try? screenshot.pngRepresentation.write(
            to: dir.appendingPathComponent("pvm-\(name).png"))

        // And described in text, so the screen can be READ in the log rather than only
        // looked at. On a machine with no Mac this is the difference between verifying
        // the UI and hoping.
        var lines = ["PVM_SCREEN \(name) >>>"]
        let texts = app.staticTexts.allElementsBoundByIndex
        for element in texts where element.exists && !element.label.isEmpty {
            lines.append("  · \(element.label)")
        }
        lines.append("PVM_SCREEN \(name) <<<")
        let described = lines.joined(separator: "\n")
        print(described)
        try? described.write(to: dir.appendingPathComponent("pvm-\(name).txt"),
                             atomically: true, encoding: .utf8)
    }

    /// §23 Structure First: the home must show order and a catalogue, not another
    /// infinite scroll of photos. If a screenshot of this ever shows a photo grid, the
    /// product has drifted into being a Cleaner.
    func testHomeIsStructureFirst() {
        let library = app.navigationBars["Library"]
        XCTAssertTrue(library.waitForExistence(timeout: 20),
                      "the home never appeared — the breadth pass did not finish")
        capture("01-home")

        // The first level §23 names. Not all will be present in every library; the ones
        // the fixture guarantees are checked.
        for root in ["Documents", "People", "Screenshots", "Timeline"] {
            XCTAssertTrue(app.staticTexts[root].exists, "\(root) is missing from the home")
        }
    }

    func testDrillDownReachesADocumentAndExplainsIt() {
        XCTAssertTrue(app.navigationBars["Library"].waitForExistence(timeout: 20))
        app.staticTexts["Documents"].tap()
        capture("02-documents")

        // Down to the leaf the tree defines for identity papers.
        if app.staticTexts["Identity"].waitForExistence(timeout: 5) {
            app.staticTexts["Identity"].tap()
            capture("03-identity")
        }

        // The safety red line, on screen: every entry must be able to explain itself.
        let firstRow = app.cells.element(boundBy: 0)
        if firstRow.waitForExistence(timeout: 5) {
            firstRow.tap()
            XCTAssertTrue(app.navigationBars["Why is this here?"].waitForExistence(timeout: 5),
                          "an asset could not explain why it was filed where it was")
            capture("04-why-is-this-here")
        }
    }

    func testTheReviewQueueIsReachableAndSmall() {
        XCTAssertTrue(app.navigationBars["Library"].waitForExistence(timeout: 20))
        app.staticTexts["Review queue"].tap()
        XCTAssertTrue(app.navigationBars["Review queue"].waitForExistence(timeout: 5))
        capture("05-review-queue")
        XCTAssertTrue(app.staticTexts["Human Review Burden"].exists,
                      "the §18 KPI is not shown, so a growing queue would look normal")
    }

    /// The paced depth pass is offered, not imposed (§24 Gate 1, DEC-029).
    func testThePlanIsOfferedRatherThanImposed() {
        XCTAssertTrue(app.navigationBars["Library"].waitForExistence(timeout: 20))
        let button = app.buttons["Look inside the photos too…"]
        if button.waitForExistence(timeout: 5) {
            button.tap()
            XCTAssertTrue(app.navigationBars["Looking inside"].waitForExistence(timeout: 5))
            capture("06-plan")
        }
    }
}
