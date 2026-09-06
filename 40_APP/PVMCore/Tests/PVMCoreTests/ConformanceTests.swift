import XCTest
@testable import PVMCore

/// THE CONFORMANCE CONTRACT — the app and the reference implementation must agree.
///
/// `30_ENGINE` is the reference implementation: its rules were argued over, measured
/// against 10,000 labelled assets and audited clause by clause against L1. This package
/// is what ships. Both have their own tests, and that proves nothing about whether they
/// agree — which is the failure that actually costs something. The app files a passport
/// somewhere the engine would not, both suites stay green, and every number ever
/// measured on the engine quietly stops describing the product.
///
/// So: one fixture, defined once in Python and emitted as `fixture.json`. The engine's
/// verdict on it is emitted as `expected.json`. This replays the same library through
/// the Swift pipeline and compares, asset by asset. Whichever side moved is the side
/// that fails.
///
/// Only decisions are compared — paths, risk level, action. Confidences are floating
/// point and would turn a real conformance check into a flaky one.
final class ConformanceTests: XCTestCase {

    private struct ExpectedRow: Decodable {
        let paths: [String]
        let risk: Int?
        let action: String?
    }

    /// The fixture as it is written, decoded into a type rather than cast out of
    /// `Any`. The first version used `JSONSerialization` and `as? [[String: Any]]`,
    /// which crashed swift-corelibs-foundation outright — "Constant strings cannot be
    /// deallocated" — because bridging JSON strings through `Any` on Linux is not the
    /// same code path it is on Apple platforms. Decoding into a struct avoids the
    /// bridge entirely and is clearer about what the file is allowed to contain.
    private struct FixtureRow: Decodable {
        struct Scene: Decodable { let identifier: String; let confidence: Double }
        struct Face: Decodable { let clusterID: String; let name: String? }

        let assetID: String
        let createdAt: String?
        let pixelW: Int
        let pixelH: Int
        let byteSize: Int
        let isScreenshot: Bool
        let source: String
        let burstID: String?
        let lat: Double?
        let lon: Double?
        let country: String?
        let city: String?
        let contentHash: String?
        let dhash: String?
        let ocrRan: Bool
        let ocrText: String
        let sceneLabels: [Scene]
        let faceClusters: [Face]
    }

    /// Read from the source tree rather than a resource bundle. `Bundle.module` with a
    /// nil extension is another Linux Foundation path better left alone, and the file
    /// is right here next to the test.
    private func resource(_ name: String) throws -> Data {
        let directory = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        let url = directory.appendingPathComponent("Resources").appendingPathComponent(name)
        guard FileManager.default.fileExists(atPath: url.path) else {
            XCTFail("\(name) is missing — regenerate with: python 40_APP/generate_shared.py")
            throw CocoaError(.fileNoSuchFile)
        }
        return try Data(contentsOf: url)
    }

    /// Dates in the fixture are naive, so both sides must read them in the same
    /// calendar or a capture near midnight would land in a different year on one side.
    private static let formatter: DateFormatter = {
        let f = DateFormatter()
        f.locale = Locale(identifier: "en_US_POSIX")
        f.timeZone = TimeZone(identifier: "UTC")
        f.dateFormat = "yyyy-MM-dd'T'HH:mm:ss"
        return f
    }()

    private func loadFixture() throws -> [AssetSignals] {
        let rows = try JSONDecoder().decode([FixtureRow].self, from: try resource("fixture.json"))
        return rows.map { row in
            var s = AssetSignals(assetID: row.assetID)
            if let iso = row.createdAt {
                s.createdAt = ConformanceTests.formatter.date(from: iso)
                s.modifiedAt = s.createdAt
            }
            s.pixelW = row.pixelW
            s.pixelH = row.pixelH
            s.byteSize = Int64(row.byteSize)
            s.isScreenshot = row.isScreenshot
            s.source = row.source
            s.burstID = row.burstID
            if let lat = row.lat, let lon = row.lon {
                s.geo = GeoFix(lat: lat, lon: lon, source: .exif)
            }
            if row.country != nil || row.city != nil {
                s.place = PlaceName(country: row.country, city: row.city, confidence: 0.9)
            }
            s.contentHash = row.contentHash
            if let d = row.dhash { s.dhash = UInt64(d) }
            s.ocrRan = row.ocrRan
            s.ocrText = row.ocrText
            s.sceneLabels = row.sceneLabels.map {
                SceneLabel(identifier: $0.identifier, confidence: $0.confidence)
            }
            s.faceClusters = row.faceClusters.map {
                FaceCluster(clusterID: $0.clusterID, name: $0.name)
            }
            return s
        }
    }

    /// The number of assets the fixture is known to contain. A conformance test that
    /// silently compares nothing and passes is the exact failure this file exists to
    /// prevent, so it is guarded against itself.
    private static let expectedFixtureSize = 78

    func testTheFixtureAndTheExpectationsAreActuallyThere() throws {
        let assets = try loadFixture()
        let expected = try JSONDecoder().decode([String: ExpectedRow].self,
                                                from: try resource("expected.json"))
        XCTAssertEqual(assets.count, Self.expectedFixtureSize,
                       "the fixture changed size — regenerate and review the diff, do not "
                       + "just update this number")
        XCTAssertGreaterThan(expected.count, Self.expectedFixtureSize / 2,
                             "expected.json covers almost nothing; a comparison against it "
                             + "would pass by having nothing to compare")
        XCTAssertTrue(expected.values.allSatisfy { !$0.paths.isEmpty },
                      "an expectation with no paths cannot fail, whatever the app does")
    }

    func testTheAppAgreesWithTheReferenceImplementation() throws {
        TaxonomyRuntime.resetMinted()
        let assets = try loadFixture()
        XCTAssertEqual(assets.count, Self.expectedFixtureSize)

        let expected = try JSONDecoder().decode([String: ExpectedRow].self,
                                                from: try resource("expected.json"))
        XCTAssertFalse(expected.isEmpty, "there is nothing to compare against")

        let directory = URL(fileURLWithPath: NSTemporaryDirectory())
            .appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        let catalog = try XCTUnwrap(
            Catalog(path: directory.appendingPathComponent("conformance.sqlite").path))
        _ = Pipeline.run(assets: assets, catalog: catalog, reconcileDeletions: false)

        var actual: [String: [String]] = [:]
        for asset in assets {
            let paths = catalog.paths(for: asset.assetID)
            guard !paths.isEmpty else { continue }
            actual[asset.assetID] = paths.sorted()
        }
        XCTAssertGreaterThan(actual.count, Self.expectedFixtureSize / 2,
                             "the app filed almost nothing — the comparison below would "
                             + "otherwise report agreement it has not established")

        var compared = 0
        var mismatches: [String] = []
        for (assetID, want) in expected.sorted(by: { $0.key < $1.key }) {
            guard let got = actual[assetID] else {
                mismatches.append("\(assetID): the app filed it nowhere; the engine filed it "
                                  + "under \(want.paths.joined(separator: ", "))")
                continue
            }
            compared += 1
            if got != want.paths.sorted() {
                mismatches.append("""
                    \(assetID) is filed differently:
                        engine: \(want.paths.sorted().joined(separator: ", "))
                        app:    \(got.joined(separator: ", "))
                    """)
            }
        }
        for assetID in actual.keys.sorted() where expected[assetID] == nil {
            mismatches.append("\(assetID): the app filed it somewhere; the engine did not")
        }

        XCTAssertGreaterThan(compared, Self.expectedFixtureSize / 2,
                             "only \(compared) assets were actually compared")
        XCTAssertTrue(mismatches.isEmpty, """
            The app and the reference implementation disagree on \(mismatches.count) \
            of \(expected.count) assets. Whichever side moved is the side to fix — do not \
            regenerate expected.json to make this pass unless the engine is the one that \
            changed deliberately.

            \(mismatches.prefix(12).joined(separator: "\n"))
            """)
    }

    /// The risk level and the action are the decisions that authorise doing something
    /// to a photo, so they are compared separately and named separately when they
    /// differ — "the catalogues differ" is not a useful failure message when the thing
    /// that differs is whether a passport may be deleted.
    func testTheTwoImplementationsAgreeOnRiskAndAction() throws {
        TaxonomyRuntime.resetMinted()
        let assets = try loadFixture()
        let expected = try JSONDecoder().decode([String: ExpectedRow].self,
                                                from: try resource("expected.json"))

        let directory = URL(fileURLWithPath: NSTemporaryDirectory())
            .appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        let catalog = try XCTUnwrap(
            Catalog(path: directory.appendingPathComponent("conformance.sqlite").path))
        _ = Pipeline.run(assets: assets, catalog: catalog, reconcileDeletions: false)

        var riskMismatches: [String] = []
        var actionMismatches: [String] = []
        var compared = 0
        for (assetID, want) in expected.sorted(by: { $0.key < $1.key }) {
            guard let got = catalog.decision(for: assetID) else {
                riskMismatches.append("\(assetID): the app recorded no decision at all")
                continue
            }
            compared += 1
            if let wantRisk = want.risk, got.risk.rawValue != wantRisk {
                riskMismatches.append(
                    "\(assetID): engine R\(wantRisk) (\(Risk(rawValue: wantRisk)?.meaning ?? "?")), "
                    + "app R\(got.risk.rawValue) (\(got.risk.meaning))")
            }
            if let wantAction = want.action, got.action != wantAction {
                actionMismatches.append(
                    "\(assetID): engine would \(wantAction), app would \(got.action ?? "nothing")")
            }
        }
        XCTAssertGreaterThan(compared, Self.expectedFixtureSize / 2,
                             "only \(compared) decisions were compared")
        XCTAssertTrue(riskMismatches.isEmpty,
                      "risk levels disagree:\n" + riskMismatches.prefix(10).joined(separator: "\n"))
        XCTAssertTrue(actionMismatches.isEmpty,
                      "actions disagree:\n" + actionMismatches.prefix(10).joined(separator: "\n"))
    }
}
