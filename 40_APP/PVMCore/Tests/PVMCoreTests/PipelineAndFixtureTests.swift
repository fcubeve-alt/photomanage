import XCTest
@testable import PVMCore

/// End-to-end over the fixture library, plus the persistence guarantees the phone will
/// actually depend on: incrementality, checkpointing, and the safety audit read back
/// from the rows that were written rather than from the code that wrote them.
final class PipelineAndFixtureTests: XCTestCase {

    private var directory: URL!

    override func setUpWithError() throws {
        directory = URL(fileURLWithPath: NSTemporaryDirectory())
            .appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        TaxonomyRuntime.resetMinted()
    }

    private func makeCatalog() throws -> Catalog {
        let path = directory.appendingPathComponent("c.sqlite").path
        return try XCTUnwrap(Catalog(path: path))
    }

    func testTheFixtureLibraryIsCatalogued() throws {
        let catalog = try makeCatalog()
        let stats = Pipeline.run(assets: FixtureLibrary.make(), catalog: catalog)
        XCTAssertEqual(stats.classified, FixtureLibrary.make().count)
        XCTAssertEqual(stats.scored, stats.classified)

        let rolled = catalog.rolledCounts()
        for root in ["Documents", "People", "Screenshots", "Places", "Travel", "Timeline"] {
            XCTAssertGreaterThan(rolled[root] ?? 0, 0, "\(root) is empty in the fixture")
        }
    }

    func testTheAwkwardAssetsLandCorrectly() throws {
        let catalog = try makeCatalog()
        _ = Pipeline.run(assets: FixtureLibrary.make(), catalog: catalog)
        let paths = catalog.assets(under: "Documents > Identity").map { $0.primaryPath }
        XCTAssertTrue(paths.contains("Documents > Identity > Passports"))
        XCTAssertTrue(paths.contains("Documents > Identity > ID Cards"))
        XCTAssertGreaterThan(catalog.rolledCounts()["Travel"] ?? 0, 0,
                             "a twelve-asset run of days in Tokyo should be a trip")
    }

    /// §12: the queue exists for what the system genuinely could not decide.
    func testTheReviewQueueIsSmall() throws {
        let catalog = try makeCatalog()
        let assets = FixtureLibrary.make()
        _ = Pipeline.run(assets: assets, catalog: catalog)
        let reviews = catalog.scalar("SELECT COUNT(*) FROM assets WHERE needs_review=1")
        XCTAssertLessThan(Double(reviews) / Double(assets.count), 0.2)
    }

    /// A4, in the catalogue rather than the index.
    func testASecondRunOverAnUnchangedLibraryDoesNoWork() throws {
        let catalog = try makeCatalog()
        let assets = FixtureLibrary.make()
        _ = Pipeline.run(assets: assets, catalog: catalog)
        let second = Pipeline.run(assets: assets, catalog: catalog)
        XCTAssertEqual(second.classified, 0)
        XCTAssertEqual(second.skippedUnchanged, assets.count)
    }

    func testAnAssetWhoseSignalsChangedIsReclassified() throws {
        let catalog = try makeCatalog()
        var assets = FixtureLibrary.make()
        _ = Pipeline.run(assets: assets, catalog: catalog)
        let index = try XCTUnwrap(assets.firstIndex { $0.assetID == "mystery" })
        assets[index].ocrRan = true
        assets[index].ocrText = "PASSPORT"
        let second = Pipeline.run(assets: assets, catalog: catalog)
        XCTAssertEqual(second.classified, 1)
        XCTAssertTrue(catalog.assets(under: "Documents > Identity")
            .contains { $0.assetID == "mystery" })
    }

    func testADeletedAssetDropsOutOfTheCatalogue() throws {
        let catalog = try makeCatalog()
        let assets = FixtureLibrary.make()
        _ = Pipeline.run(assets: assets, catalog: catalog)
        let fewer = Array(assets.dropLast(5))
        let stats = Pipeline.run(assets: fewer, catalog: catalog)
        XCTAssertEqual(stats.forgotten, 5)
        XCTAssertEqual(catalog.scalar("SELECT COUNT(*) FROM assets"), fewer.count)
    }

    /// Checked against the rows that were written, not the constructor that wrote them.
    /// A red line enforced only where it is enforced is not a red line.
    func testTheSafetyRedLinesHoldInTheWrittenRows() throws {
        let catalog = try makeCatalog()
        _ = Pipeline.run(assets: FixtureLibrary.make(), catalog: catalog)

        let acting = RiskPolicy.actingActions.map { "'\($0.rawValue)'" }.joined(separator: ",")
        XCTAssertEqual(catalog.scalar("""
            SELECT COUNT(*) FROM proposals
            WHERE risk >= \(RiskPolicy.neverActAtOrAbove.rawValue) AND action IN (\(acting));
            """), 0, "something R4+ was acted on")

        XCTAssertEqual(catalog.scalar("""
            SELECT COUNT(*) FROM assignments a
            WHERE NOT EXISTS (SELECT 1 FROM evidence e
                              WHERE e.asset_id = a.asset_id AND e.path = a.path);
            """), 0, "an assignment was written with no evidence")

        XCTAssertEqual(catalog.scalar("SELECT COUNT(*) FROM proposals WHERE reversible=0"), 0)
    }

    /// The one thing the system may do on its own: an exact byte-duplicate where an
    /// identical copy demonstrably remains.
    func testOnlyExactDuplicatesAreAutoApplicable() throws {
        let catalog = try makeCatalog()
        _ = Pipeline.run(assets: FixtureLibrary.make(), catalog: catalog)
        XCTAssertEqual(catalog.scalar("""
            SELECT COUNT(*) FROM proposals WHERE auto_applicable=1 AND action != 'auto_clean';
            """), 0)
        XCTAssertGreaterThan(catalog.scalar("SELECT COUNT(*) FROM proposals WHERE auto_applicable=1"), 0,
                             "the fixture contains a byte-identical re-download; it should be tidyable")
    }

    /// §24 Gate 3 names TTFUV a P0 metric, and Tier 2-C sets the bar at under 30
    /// seconds for the first value and two minutes for a basic library.
    func testTimeToFirstUsefulViewMeetsTheTier2Bar() {
        XCTAssertLessThan(IngestionPlanner.timeToFirstUsefulView(librarySize: 100_000), 30)
        XCTAssertLessThan(IngestionPlanner.timeToFirstUsefulView(librarySize: 10_000), 5)
    }

    func testALargeLibraryIsPacedNotRefused() {
        let plan = IngestionPlanner.plan(librarySize: 100_000)
        XCTAssertEqual(plan.recommended, "overnight")
        XCTAssertTrue(plan.notes.contains { $0.contains("A3") })
        XCTAssertEqual(IngestionPlanner.plan(librarySize: 2_000).recommended, "now")
    }
}

/// The app and the reference engine share a taxonomy and a rule set. These are
/// generated from the Python source, and this is the last line of defence if the
/// generator is ever bypassed.
final class SharedFingerprintTests: XCTestCase {
    func testTheTreeHasTheElevenRootsTheConstitutionSpecifies() {
        XCTAssertEqual(Taxonomy.roots.count, 11)
        for root in ["Documents", "People", "Screenshots", "Places", "Travel", "Objects",
                     "Purchases", "Clothing", "Work", "Downloads", "Timeline"] {
            XCTAssertTrue(Taxonomy.roots.contains(root), "\(root) is missing from the tree")
        }
    }

    func testEveryRulePathIsANodeInTheTree() {
        let groups = [Rules.documentRules, Rules.purchaseRules,
                      Rules.screenshotRules, Rules.workTextRules]
        for group in groups {
            for rule in group {
                XCTAssertTrue(Taxonomy.allNodes.contains(rule.path),
                              "rule points at \(rule.path), which is not in the tree")
            }
        }
        for path in Rules.sceneMap.values {
            XCTAssertTrue(Taxonomy.allNodes.contains(path), "\(path) is not in the tree")
        }
    }

    func testEveryRuleRegexCompiles() {
        let groups = [Rules.documentRules, Rules.purchaseRules,
                      Rules.screenshotRules, Rules.workTextRules]
        for group in groups {
            for rule in group {
                XCTAssertNoThrow(try NSRegularExpression(pattern: rule.pattern,
                                                         options: [.caseInsensitive]),
                                 "rule for \(rule.path) has a pattern Swift cannot compile")
            }
        }
    }
}
