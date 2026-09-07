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
    ///
    /// It queries concrete element types rather than `.any`. The first version used
    /// `app.descendants(matching: .any)[identifier]`, which forces XCUITest to snapshot
    /// the entire accessibility hierarchy on every evaluation — the UI step went from
    /// 4 minutes to over 15 and was cancelled before it could reach the 45-minute
    /// timeout. On a runner billed at ten times the Linux rate that is not a style
    /// point.
    private func element(_ identifier: String) -> XCUIElement {
        for query in [app.cells, app.buttons, app.staticTexts, app.otherElements] {
            let candidate = query[identifier]
            if candidate.exists { return candidate }
        }
        return app.cells[identifier]
    }

    @discardableResult
    private func row(_ identifier: String, swipes: Int = 4) -> XCUIElement {
        // One bounded wait for the list to populate, then scroll. Waiting the full
        // timeout again on every swipe is what turns a missing row into a minute.
        if app.cells.firstMatch.waitForExistence(timeout: 20) == false {
            return app.cells[identifier]
        }

        // A bounded wait for THIS element before scrolling at all.
        //
        // The first version checked once and swiped immediately, and `swipeUp` only
        // goes one way: a row that had not finished rendering was scrolled PAST, and
        // then hunted for below where it actually sat. That is how `browse-Documents`
        // came back "no matches found" while the captured screen text for the same run
        // showed Documents as the second row on the home. The screen dumps are what
        // made it obvious, and they were only added because the failures were
        // unreadable before.
        if element(identifier).waitForExistence(timeout: 5) { return element(identifier) }

        for _ in 0...swipes {
            app.swipeUp()
            let found = element(identifier)
            if found.exists { return found }
        }
        // Back up, in case it was above where the search started.
        for _ in 0...(swipes * 2) {
            app.swipeDown()
            let found = element(identifier)
            if found.exists { return found }
        }
        return element(identifier)
    }

    /// §23 Structure First: the home must show order and a catalogue, not another    /// §23 Structure First: the home must show order and a catalogue, not another
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
    ///
    /// Scoped to `app.cells` for the same reason as `element(_:)`: a predicate over
    /// `.any` re-snapshots the whole hierarchy every time it is evaluated.
    private func firstAsset(maxDepth: Int) -> XCUIElement {
        let assets = app.cells.matching(NSPredicate(format: "identifier BEGINSWITH 'asset-'"))
        let children = app.cells.matching(NSPredicate(format: "identifier BEGINSWITH 'child-'"))
        for depth in 0...maxDepth {
            if assets.firstMatch.waitForExistence(timeout: depth == 0 ? 10 : 3) {
                return assets.firstMatch
            }
            guard children.firstMatch.exists else { break }
            children.firstMatch.tap()
        }
        return assets.firstMatch
    }

    /// §2 Remember, on screen.    /// §2 Remember, on screen.    /// §2 Remember, on screen. The catalogue says which shelf a photo is on; this says
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
        // By identifier, and by the account itself. Matching the header's TEXT failed
        // for a reason that had nothing to do with the product: iOS renders a plain
        // Section header uppercased, so the lookup for "Why the library thinks this
        // exists" missed the "WHY THE LIBRARY THINKS THIS EXISTS" that was on screen,
        // and the test reported the red line broken while the app was keeping it.
        XCTAssertTrue(app.staticTexts["entity-why"].exists,
                      "an entity is shown with no account of why it exists")
        XCTAssertTrue(
            app.staticTexts.containing(NSPredicate(format: "label CONTAINS[c] %@",
                                                   "face you named")).firstMatch.exists,
            "the section header is there but says nothing — the red line is that an "
            + "entity can explain itself, not that it has a heading")
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
