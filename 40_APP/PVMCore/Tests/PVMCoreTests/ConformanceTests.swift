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

    private func resource(_ name: String) throws -> Data {
        let url = try XCTUnwrap(
            Bundle.module.url(forResource: "Resources/\(name)", withExtension: nil)
                ?? Bundle.module.url(forResource: name, withExtension: nil),
            "\(name) is missing — regenerate with: python 40_APP/generate_shared.py")
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
        let raw = try JSONSerialization.jsonObject(with: try resource("fixture.json"))
        let rows = try XCTUnwrap(raw as? [[String: Any]])
        return rows.map { row in
            var s = AssetSignals(assetID: row["assetID"] as? String ?? "")
            if let iso = row["createdAt"] as? String {
                s.createdAt = ConformanceTests.formatter.date(from: iso)
                s.modifiedAt = s.createdAt
            }
            s.pixelW = row["pixelW"] as? Int ?? 0
            s.pixelH = row["pixelH"] as? Int ?? 0
            s.byteSize = Int64(row["byteSize"] as? Int ?? 0)
            s.isScreenshot = row["isScreenshot"] as? Bool ?? false
            s.source = row["source"] as? String ?? "unknown"
            s.burstID = row["burstID"] as? String
            if let lat = row["lat"] as? Double, let lon = row["lon"] as? Double {
                s.geo = GeoFix(lat: lat, lon: lon, source: .exif)
            }
            let country = row["country"] as? String
            let city = row["city"] as? String
            if country != nil || city != nil {
                s.place = PlaceName(country: country, city: city, confidence: 0.9)
            }
            s.contentHash = row["contentHash"] as? String
            if let d = row["dhash"] as? String { s.dhash = UInt64(d) }
            s.ocrRan = row["ocrRan"] as? Bool ?? false
            s.ocrText = row["ocrText"] as? String ?? ""
            s.sceneLabels = (row["sceneLabels"] as? [[String: Any]] ?? []).compactMap {
                guard let id = $0["identifier"] as? String,
                      let c = $0["confidence"] as? Double else { return nil }
                return SceneLabel(identifier: id, confidence: c)
            }
            s.faceClusters = (row["faceClusters"] as? [[String: Any]] ?? []).compactMap {
                guard let id = $0["clusterID"] as? String else { return nil }
                return FaceCluster(clusterID: id, name: $0["name"] as? String)
            }
            return s
        }
    }

    func testTheAppAgreesWithTheReferenceImplementation() throws {
        TaxonomyRuntime.resetMinted()
        let assets = try loadFixture()
        XCTAssertFalse(assets.isEmpty, "the fixture is empty")

        let expected = try JSONDecoder().decode([String: ExpectedRow].self,
                                                from: try resource("expected.json"))

        let directory = URL(fileURLWithPath: NSTemporaryDirectory())
            .appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        let catalog = try XCTUnwrap(
            Catalog(path: directory.appendingPathComponent("conformance.sqlite").path))
        _ = Pipeline.run(assets: assets, catalog: catalog, reconcileDeletions: false)

        var actual: [String: (paths: [String], risk: Int?, action: String?)] = [:]
        for asset in assets {
            let paths = catalog.why(asset.assetID).map { $0.path }.sorted()
            guard !paths.isEmpty else { continue }
            actual[asset.assetID] = (paths: paths, risk: nil, action: nil)
        }

        var mismatches: [String] = []
        for (assetID, want) in expected.sorted(by: { $0.key < $1.key }) {
            guard let got = actual[assetID] else {
                mismatches.append("\(assetID): the app filed it nowhere; the engine filed it "
                                  + "under \(want.paths.joined(separator: ", "))")
                continue
            }
            if got.paths != want.paths.sorted() {
                mismatches.append("""
                    \(assetID) is filed differently:
                        engine: \(want.paths.sorted().joined(separator: ", "))
                        app:    \(got.paths.joined(separator: ", "))
                    """)
            }
        }
        for assetID in actual.keys.sorted() where expected[assetID] == nil {
            mismatches.append("\(assetID): the app filed it somewhere; the engine did not")
        }

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
        for (assetID, want) in expected.sorted(by: { $0.key < $1.key }) {
            let rows = catalog.assets(under: "Timeline").filter { $0.assetID == assetID }
            if let wantRisk = want.risk, let got = rows.first {
                if got.risk.rawValue != wantRisk {
                    riskMismatches.append("\(assetID): engine R\(wantRisk), app R\(got.risk.rawValue)")
                }
            }
            if let wantAction = want.action {
                let got = catalog.reviewQueue(limit: 10_000).first { $0.assetID == assetID }?.action
                if wantAction == "review", got != "review" {
                    actionMismatches.append("\(assetID): engine says review, app does not")
                }
            }
        }
        XCTAssertTrue(riskMismatches.isEmpty,
                      "risk levels disagree:\n" + riskMismatches.prefix(10).joined(separator: "\n"))
        XCTAssertTrue(actionMismatches.isEmpty,
                      "actions disagree:\n" + actionMismatches.prefix(10).joined(separator: "\n"))
    }
}
