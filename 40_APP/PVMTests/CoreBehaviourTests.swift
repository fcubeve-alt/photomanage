import XCTest
@testable import PVM

/// The behaviours that must hold for every library, and the safety red lines that must
/// hold even when the classifier is wrong. Ported from
/// `30_ENGINE/tests/test_engine.py` — if these two suites ever disagree, the app and
/// the reference implementation have diverged and one of them is lying.

private let london = GeoFix(lat: 51.5074, lon: -0.1278)
private let tokyo = GeoFix(lat: 35.6762, lon: 139.6503)
private let uk = PlaceName(country: "United Kingdom", city: "London", confidence: 0.9)
private let japan = PlaceName(country: "Japan", city: "Tokyo", confidence: 0.9)

private func makeDate(_ y: Int, _ m: Int, _ d: Int, _ h: Int = 12) -> Date {
    var c = DateComponents(); c.year = y; c.month = m; c.day = d; c.hour = h
    return Calendar(identifier: .gregorian).date(from: c)!
}

private func asset(_ id: String = "a", build: (inout AssetSignals) -> Void = { _ in }) -> AssetSignals {
    var s = AssetSignals(assetID: id)
    s.createdAt = makeDate(2025, 6, 18)
    build(&s)
    return s
}

private func classify(_ a: AssetSignals, context: LibraryContext = LibraryContext(),
                      budget: Tier = .text) -> Classification {
    Classifier(context: context, budget: budget).classify(a)
}

final class EveryAssignmentExplainsItselfTests: XCTestCase {
    func testAssignmentWithoutEvidenceCannotExist() {
        XCTAssertNil(Assignment(path: "Documents", evidence: []))
    }

    func testEvidenceWithoutAReasonCannotExist() {
        XCTAssertNil(Evidence(signal: "ocrText", tier: .text, weight: 0.9, reason: "   "))
    }

    func testARuleCannotInventACategory() {
        XCTAssertNil(TaxonomyRuntime.ensure("Documents > Crypto"))
        XCTAssertNotNil(TaxonomyRuntime.ensure("People > Zoe"))
    }

    func testNoAmountOfEvidenceReachesCertainty() {
        let weights = Array(repeating: 0.99, count: 20)
        XCTAssertLessThan(combineConfidence(weights), 1.0)
    }

    func testEveryClassifiedPathCarriesAReason() {
        let c = classify(asset { s in
            s.isScreenshot = true; s.ocrRan = true; s.ocrText = "VERIFICATION CODE 115838"
        })
        for (path, why) in c.explain() {
            XCTAssertFalse(why.trimmingCharacters(in: .whitespaces).isEmpty,
                           "\(path) was filed with no explanation")
        }
    }
}

final class CascadeTests: XCTestCase {
    func testAScreenshotWithNoReadableTextStopsAtTheRoot() {
        let c = classify(asset { s in
            s.isScreenshot = true; s.ocrRan = true; s.ocrText = "SCREENSHOT"
        })
        XCTAssertEqual(c.primary?.path, "Screenshots")
        XCTAssertFalse(c.paths.contains("Screenshots > Chat"))
    }

    func testTextDeepensAScreenshotAndTheParentIsNotCountedTwice() {
        let c = classify(asset { s in
            s.isScreenshot = true; s.ocrRan = true; s.ocrText = "PICKUP CODE 4417 — LOCKER B12"
        })
        XCTAssertTrue(c.paths.contains("Screenshots > Temporary > Pickup Codes"))
        XCTAssertFalse(c.paths.contains("Screenshots"))
    }

    func testAnAmbiguousDocumentStopsAtTheBranchItCanProve() {
        let c = classify(asset { s in
            s.ocrRan = true; s.ocrText = "CONTRACT — PAGE 1 OF 4"
        })
        XCTAssertEqual(c.primary?.path, "Documents > Contracts")
    }

    func testReceiptsAreCrossListedOnceNotCopied() {
        let c = classify(asset { s in
            s.ocrRan = true; s.ocrText = "RECEIPT — HEADPHONES £129.00"
        })
        XCTAssertTrue(c.paths.contains("Purchases > Receipts"))
        XCTAssertTrue(c.paths.contains("Documents > Receipts"))
        XCTAssertEqual(c.paths.count, Set(c.paths).count)
    }

    func testEveryAssetReachesTheTimeline() {
        XCTAssertTrue(classify(asset()).paths.contains("Timeline > 2025"))
    }

    func testAnAssetWithNoDateSaysSoInsteadOfGuessingOne() {
        let c = classify(asset { $0.createdAt = nil })
        XCTAssertFalse(c.paths.contains { $0.hasPrefix("Timeline") })
        XCTAssertTrue(c.notes.contains { $0.contains("timeline") })
    }

    func testVideoIsReportedAsHavingNowhereToGo() {
        let c = classify(asset { $0.isVideo = true })
        XCTAssertTrue(c.notes.contains { $0.contains("video") })
    }
}

/// The regression that cost nine of nine identity documents in the reference engine:
/// with the location rule running first, a GPS fix settled every photographed document
/// as `Places > … > London` at 0.91, the escalation policy saw a settled leaf, and the
/// OCR pass that would have recognised the passport never ran. Silent, and plausible.
final class LocationIsContextNotIdentityTests: XCTestCase {
    func testADocumentPhotographedAtHomeIsStillADocument() {
        let c = classify(asset { s in
            s.geo = london; s.place = uk; s.ocrRan = true; s.ocrText = "PASSPORT"
        })
        XCTAssertEqual(c.primary?.path, "Documents > Identity > Passports")
    }

    func testPaperworkDoesNotAppearUnderPlaces() {
        let c = classify(asset { s in
            s.geo = london; s.place = uk; s.ocrRan = true; s.ocrText = "PASSPORT"
        })
        XCTAssertTrue(c.paths.filter { $0.hasPrefix("Places") }.isEmpty,
                      "a passport was filed on the Places shelf next to the holiday photos")
    }

    func testAnOrdinaryPhotoWithAFixStillGetsItsPlace() {
        let c = classify(asset { s in s.geo = tokyo; s.place = japan })
        XCTAssertEqual(c.primary?.path, "Places > Japan > Tokyo")
    }

    func testAnInferredFixIsNotTreatedAsAMeasuredOne() {
        let c = classify(asset { s in
            s.geo = GeoFix(lat: 51.5, lon: -0.1, source: .inferred); s.place = uk
        })
        XCTAssertTrue(c.paths.filter { $0.hasPrefix("Places") }.isEmpty)
    }
}

final class CostTests: XCTestCase {
    func testACheapAnswerDoesNotPayForExpensiveSignals() {
        let c = classify(asset { s in
            s.isScreenshot = true; s.ocrRan = true; s.ocrText = "SCREENSHOT"
        })
        XCTAssertFalse(c.tiersSpent.contains(.faces), "face clustering ran on a screenshot")
        XCTAssertFalse(c.tiersSpent.contains(.visual))
    }

    func testSpentAndUsedAreReportedSeparately() {
        let c = classify(asset { s in s.geo = tokyo; s.place = japan })
        XCTAssertEqual(c.tierUsed, .metadata)
        XCTAssertTrue(c.tiersSpent.contains(.faces))
    }

    func testAMetadataBudgetNeverReadsText() {
        let c = classify(asset { s in s.ocrRan = true; s.ocrText = "PASSPORT" }, budget: .metadata)
        XCTAssertFalse(c.paths.contains("Documents > Identity > Passports"))
    }
}

final class LibraryContextTests: XCTestCase {
    private func homeAndTrip() -> [AssetSignals] {
        var out: [AssetSignals] = []
        for i in 0..<60 {
            out.append(asset("h\(i)") { s in
                s.createdAt = makeDate(2024, 1, 1, 21).addingTimeInterval(Double(i) * 86400)
                s.geo = london; s.place = uk
            })
        }
        for i in 0..<20 {
            out.append(asset("t\(i)") { s in
                s.createdAt = makeDate(2025, 4, 12, 10).addingTimeInterval(Double(i) * 3600 * 6)
                s.geo = tokyo; s.place = japan
            })
        }
        return out
    }

    func testHomeIsLearnedAndNeverAskedFor() {
        let ctx = LibraryContextBuilder.build(homeAndTrip())
        XCTAssertEqual(ctx.homeCity, "London")
        XCTAssertGreaterThan(ctx.homeConfidence, 0.4)
    }

    /// One weekend of 500 beach photos must not outvote two years of living somewhere.
    /// Counting captures instead of days is how it does.
    func testHomeIsMeasuredInDaysNotInCaptures() {
        var assets: [AssetSignals] = []
        for i in 0..<60 {
            assets.append(asset("h\(i)") { s in
                s.createdAt = makeDate(2024, 1, 1, 21).addingTimeInterval(Double(i) * 86400)
                s.geo = london; s.place = uk
            })
        }
        for i in 0..<400 {
            assets.append(asset("b\(i)") { s in
                s.createdAt = makeDate(2024, 7, 6, 12).addingTimeInterval(Double(i) * 60)
                s.geo = GeoFix(lat: 50.8225, lon: -0.1372)
                s.place = PlaceName(country: "United Kingdom", city: "Brighton", confidence: 0.9)
            })
        }
        XCTAssertEqual(LibraryContextBuilder.build(assets).homeCity, "London")
    }

    func testARunOfDaysAwayBecomesATrip() {
        let ctx = LibraryContextBuilder.build(homeAndTrip())
        XCTAssertEqual(ctx.trips.count, 1)
        XCTAssertEqual(ctx.trips.first?.city, "Tokyo")
    }

    func testTwoPhotosOnADayOutAreNotATrip() {
        var assets = homeAndTrip().filter { !$0.assetID.hasPrefix("t") }
        assets.append(asset("x1") { s in
            s.createdAt = makeDate(2025, 4, 12, 10); s.geo = tokyo; s.place = japan
        })
        assets.append(asset("x2") { s in
            s.createdAt = makeDate(2025, 4, 13, 10); s.geo = tokyo; s.place = japan
        })
        XCTAssertTrue(LibraryContextBuilder.build(assets).trips.isEmpty)
    }
}
