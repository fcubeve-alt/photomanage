import XCTest
import PVMCore
@testable import PVM

/// The parts of shipping that are not the product: what leaves the device, what can be
/// charged for, and what the legal text says. Each of these is a claim the App Store
/// listing will repeat, so each needs something that fails when it stops being true.
@MainActor
final class LaunchReadinessTests: XCTestCase {

    private var directory: URL!

    override func setUpWithError() throws {
        directory = URL(fileURLWithPath: NSTemporaryDirectory())
            .appendingPathComponent("pvm-launch-" + UUID().uuidString)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
    }

    override func tearDownWithError() throws {
        try? FileManager.default.removeItem(at: directory)
    }

    private func makeCatalog() throws -> Catalog {
        try XCTUnwrap(Catalog(path: directory.appendingPathComponent("c.sqlite").path))
    }

    // MARK: - the support report

    /// The catalogue holds text read out of photographs — passport numbers, bank
    /// statements. A support report is a thing users mail to strangers, so the only
    /// safe shape for it is counts and enumerated names. This asserts the shape rather
    /// than the wording, so the test survives copy changes and still bites if a field
    /// carrying library content is ever added.
    func testTheSupportReportIsNumbersAndVersionsOnly() throws {
        let catalog = try makeCatalog()
        catalog.exec("INSERT INTO assets(asset_id, signals_fp, engine_fp, asset_class) "
                     + "VALUES('3F2504E0-4F89-11D3-9A0C-0305E82C3301/L0/001','fp','swift-1','document');")
        let report = Diagnostics.report(catalog: catalog, phase: "ready")

        XCTAssertFalse(report.contains("3F2504E0"), "an asset identifier reached the report")
        XCTAssertNil(report.range(of: #"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-"#, options: .regularExpression),
                     "something UUID-shaped reached the report")
        XCTAssertFalse(report.contains("/L0/"), "a PhotoKit local identifier reached the report")
        XCTAssertFalse(report.lowercased().contains(directory.path.lowercased()),
                       "a file path reached the report")

        XCTAssertTrue(report.contains("indexed assets: 1"))
        XCTAssertTrue(report.contains("integrity: ok"))
        XCTAssertTrue(report.contains("schema"))
    }

    func testTheReportSurvivesHavingNoCatalogue() {
        let report = Diagnostics.report(catalog: nil, phase: "needsPermission")
        XCTAssertTrue(report.contains("catalogue: not open"))
    }

    /// `buildSummary` is written into every crash report, including ones produced from
    /// a signal handler that cannot inspect what it is writing.
    func testTheBuildSummaryDescribesTheBuildAndNothingElse() {
        let summary = Diagnostics.buildSummary
        XCTAssertTrue(summary.contains("schema \(Catalog.schemaVersion)"))
        XCTAssertNil(summary.range(of: #"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-"#, options: .regularExpression))
        XCTAssertFalse(summary.contains("/"), "a path in the crash preamble")
    }

    // MARK: - the crash report's privacy filter

    func testRedactionRemovesPhotoIdentifiers() {
        let text = CrashReporter.redact(
            "no row for 3F2504E0-4F89-11D3-9A0C-0305E82C3301/L0/001 in assignments")
        XCTAssertFalse(text.contains("3F2504E0"))
        XCTAssertTrue(text.contains("<redacted>"))
        XCTAssertTrue(text.contains("in assignments"), "over-eager is fine; useless is not")
    }

    func testRedactionRemovesPathsAndLongNumbers() {
        XCTAssertFalse(CrashReporter.redact("/var/mobile/Containers/Data/Application/x")
            .contains("Containers"))
        XCTAssertFalse(CrashReporter.redact("ocr said 445829173261").contains("445829173261"))
    }

    func testRedactionLeavesOrdinaryMessagesReadable() {
        XCTAssertEqual(CrashReporter.redact("index out of range (3 of 2)"),
                       "index out of range (3 of 2)")
    }

    // MARK: - the paywall boundary

    /// DEC-026 cancelled the willingness-to-pay test, so there is no price. The
    /// boundary exists; it is empty; every feature is free. When that changes it should
    /// be because someone decided it, and this test is what makes the decision visible.
    func testNothingIsBehindAPaywallUntilThereIsAPrice() {
        XCTAssertTrue(Commerce.paywall.isEmpty)
        XCTAssertFalse(Commerce.isCommerceConfigured)
        for feature in Feature.allCases {
            XCTAssertTrue(Entitlements.shared.isUnlocked(feature),
                          "\(feature) is gated but nothing is for sale")
        }
    }

    /// The permission sheet says the app reads your library "so they can be catalogued
    /// and found again". Charging for the result of a permission taken on that basis is
    /// not a pricing decision, it is a different app.
    func testCataloguingAndSearchCanNeverBeChargedFor() {
        XCTAssertTrue(Commerce.alwaysFree.contains(.catalogue))
        XCTAssertTrue(Commerce.alwaysFree.contains(.search))
        XCTAssertTrue(Commerce.alwaysFree.isDisjoint(with: Commerce.paywall))
    }

    func testProductIdentifiersAreDistinctAndNamespaced() {
        XCTAssertEqual(Set(Commerce.ProductID.all).count, Commerce.ProductID.all.count)
        for identifier in Commerce.ProductID.all {
            XCTAssertTrue(identifier.hasPrefix("com.pvm.app."), identifier)
        }
    }

    // MARK: - the legal text

    /// The policy ships inside the binary because the app cannot fetch it — it has no
    /// network code. That is only worth anything if the text is actually there.
    func testTheLegalTextIsInTheBinary() {
        XCTAssertTrue(LegalText.privacyPolicy.contains("不收集"))
        XCTAssertTrue(LegalText.privacyPolicy.contains("Privacy Policy"))
        XCTAssertTrue(LegalText.termsOfService.contains("服务条款"))
        XCTAssertGreaterThan(LegalText.privacyPolicy.count, 1_000)
    }

    /// `generate_legal.py` strips the blockquoted notes, which are addressed to the
    /// Owner and not to a user.
    func testTheRepositoryNotesDoNotShipToUsers() {
        for text in [LegalText.privacyPolicy, LegalText.termsOfService] {
            for line in text.split(separator: "\n") {
                XCTAssertFalse(line.hasPrefix(">"), "an Owner note reached the app: \(line)")
            }
        }
    }
}
