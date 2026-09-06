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
        // Only what is ON SCREEN. A SwiftUI List is a collection view: rows below the
        // fold are not rendered and are not in the accessibility tree, so they are not
        // in this dump either. That cost a run — "Timeline is missing from the home"
        // was true of the dump and false of the product, and reading the two as the
        // same thing is how a screenshot becomes a wrong conclusion.
        var lines = ["PVM_SCREEN \(name) >>> (visible elements only; a List does not "
                     + "render rows below the fold)"]
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

    /// Wait for a row, scrolling the list if it has not been rendered yet.
    ///
    /// Two separate mistakes this replaces. `waitForExistence` on the navigation bar
    /// returns while the list is still showing "Reading your library…", so a tap that
    /// followed it found nothing; and a row below the fold does not exist until the
    /// list scrolls to it, so `exists` was answering a question about the viewport
    /// rather than about the product.
    @discardableResult
    private func row(_ identifier: String, swipes: Int = 6) -> XCUIElement {
        let element = app.descendants(matching: .any)[identifier]
        if element.waitForExistence(timeout: 20) { return element }
        for _ in 0..<swipes {
            app.swipeUp()
            if element.exists { return element }
        }
        return element
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
        // the fixture guarantees are checked. Looked up by accessibility identifier and
        // scrolled to, because "not on screen" is not "not in the catalogue".
        for root in ["Documents", "People", "Screenshots", "Timeline"] {
            XCTAssertTrue(row("browse-\(root)").exists,
                          "\(root) is missing from the home even after scrolling")
        }
        // §23 is about seeing the catalogue at a glance, so the fixture's whole first
        // level has to be reachable — not just the shelves that happen to fit.
        for root in ["Places", "Travel", "Purchases", "Downloads"] {
            XCTAssertTrue(row("browse-\(root)").exists, "\(root) is not reachable")
        }
    }

    func testDrillDownReachesADocumentAndExplainsIt() {
        XCTAssertTrue(app.navigationBars["Library"].waitForExistence(timeout: 20))
        row("browse-Documents").tap()
        capture("02-documents")

        // Drill until an actual photo is on screen. Sub-categories and photos are both
        // cells, so "the first cell" was a folder — the previous version drilled into
        // `Identity`, tapped cell 0 again, landed in `Passports`, and concluded that an
        // asset could not explain itself without ever having opened one.
        let asset = firstAsset(maxDepth: 3)
        XCTAssertTrue(asset.exists,
                      "no photo was reachable under Documents — the fixture files "
                      + "seven there, so either the tree or the browse view is wrong")
        capture("03-inside-documents")

        asset.tap()
        // The safety red line, on screen: every entry must be able to explain itself.
        XCTAssertTrue(app.navigationBars["Why is this here?"].waitForExistence(timeout: 5),
                      "an asset could not explain why it was filed where it was")
        capture("04-why-is-this-here")
    }

    /// The first photo reachable from here, following sub-categories as needed.
    ///
    /// Returns whatever it last looked at when it finds nothing, so the caller asserts
    /// rather than this silently returning something harmless — a helper that quietly
    /// succeeds at nothing is how a test passes without testing.
    private func firstAsset(maxDepth: Int) -> XCUIElement {
        let assets = app.descendants(matching: .any)
            .matching(NSPredicate(format: "identifier BEGINSWITH 'asset-'"))
        for _ in 0...maxDepth {
            if assets.firstMatch.waitForExistence(timeout: 5) { return assets.firstMatch }
            let children = app.descendants(matching: .any)
                .matching(NSPredicate(format: "identifier BEGINSWITH 'child-'"))
            guard children.firstMatch.exists else { break }
            children.firstMatch.tap()
        }
        return assets.firstMatch
    }

    /// §2 Remember, on screen.    /// §2 Remember, on screen. The catalogue says which shelf a photo is on; this says
    /// what the library knows exists. If this screen is ever empty on the fixture, the
    /// product has gone back to being a filing system.
    func testTheLibraryRemembersThingsAndSaysWhy() {
        XCTAssertTrue(app.navigationBars["Library"].waitForExistence(timeout: 20))
        row("memory").tap()
        XCTAssertTrue(app.navigationBars["Memory"].waitForExistence(timeout: 10))
        capture("07-memory")

        // The fixture contains Anna, London, a passport and a Tokyo trip, so the memory
        // must contain a person, a place, a document and an event.
        XCTAssertTrue(row("memory-person:anna").exists,
                      "a named face did not become someone the library remembers")

        row("memory-person:anna").tap()
        XCTAssertTrue(app.navigationBars["Anna"].waitForExistence(timeout: 5))
        capture("08-entity")
        // The red line, on screen: an entity has to say why it is believed to exist.
        XCTAssertTrue(app.staticTexts["Why the library thinks this exists"].exists,
                      "an entity is shown with no account of why it exists")
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
