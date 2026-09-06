import XCTest
@testable import PVMCore

/// Tests for the Category-Specific Entity Resolver — §24 Gate 2.
/// Ported from `30_ENGINE/tests/test_resolver.py`.
///
/// `eval/evaluate_entities.py` scores the resolver and reports False Merge and False
/// Split. These are the different job: they lock the *rules*, so a later change that
/// improves the score by loosening a boundary fails here instead of passing there.
///
/// The asymmetry is the design. Tier 1-B: 错误合并证件/合同的代价远高于漏检. So most of
/// this file is about what the resolver must refuse to do.

private func rDate(_ y: Int, _ m: Int, _ d: Int, _ h: Int = 14) -> Date {
    var c = DateComponents(); c.year = y; c.month = m; c.day = d; c.hour = h
    var cal = Calendar(identifier: .gregorian)
    cal.timeZone = TimeZone(identifier: "UTC")!
    return cal.date(from: c)!
}

private let rWhen = rDate(2025, 6, 18)

private func rAsset(_ id: String, text: String = "", when: Date? = nil,
                    dhash: UInt64 = 0x1234_5678_9ABC_DEF0, labels: [String] = [],
                    screenshot: Bool = false, geo: GeoFix? = nil,
                    contentHash: String? = nil) -> AssetSignals {
    var a = AssetSignals(assetID: id)
    a.createdAt = when ?? rWhen
    a.pixelW = 4032; a.pixelH = 3024; a.byteSize = 500_000
    a.contentHash = contentHash ?? "sha::\(id)"
    a.dhash = dhash
    a.source = screenshot ? "screenshot" : "camera"
    a.isScreenshot = screenshot
    if !text.isEmpty { a.ocrRan = true; a.ocrText = text }
    a.sceneLabels = labels.map { SceneLabel(identifier: $0, confidence: 0.8) }
    if let geo {
        a.geo = geo
        a.place = PlaceName(country: "United Kingdom", city: "London", confidence: 0.9)
    }
    return a
}

private func rDecide(_ a: AssetSignals, _ b: AssetSignals) -> Resolution {
    let context = LibraryContextBuilder.build([a, b])
    let classifier = Classifier(context: context, budget: .text)
    return EntityResolver.resolve(a, b, classifier.classify(a), classifier.classify(b))
}

/// A classification that says "this is a document" and nothing more — the state a
/// photograph of paperwork reaches when the OCR came back empty.
private func asDocument(_ assetID: String) -> Classification {
    var c = Classification(assetID: assetID)
    c.add(Assignment(path: "Documents",
                     evidence: [Evidence(signal: "shape", tier: .metadata, weight: 0.6,
                                         reason: "the page shape reads as paperwork")!],
                     isPrimary: true)!)
    return c
}

/// A wrong identifier is worse than none: none ends at uncertain, wrong ends at same.
/// Every case here is one the first version of the patterns got wrong.
final class ResolverFieldExtractionTests: XCTestCase {

    func testALabelAloneIsNotAnIdentifier() {
        XCTAssertEqual([], EntityResolver.identifiers(in: "PASSPORT UNITED KINGDOM"))
    }

    func testNoInsideAWordIsNotTheWordNo() {
        XCTAssertEqual([], EntityResolver.identifiers(in: "RECEIPT NORTHSIDE COFFEE"))
    }

    func testAnIdentifierMustContainADigit() {
        XCTAssertEqual([], EntityResolver.identifiers(in: "ORDER CONFIRMED"))
        XCTAssertEqual(["A882291"], EntityResolver.identifiers(in: "ORDER NO: A88-2291"))
    }

    func testPunctuationInsideAnIdentifierIsIgnored() {
        XCTAssertEqual(["INV2025889"],
                       EntityResolver.identifiers(in: "INVOICE NO: INV-2025-889"))
        XCTAssertEqual(["INV2025889"],
                       EntityResolver.identifiers(in: "INVOICE NO. INV/2025/889"))
    }

    /// When OCR reads `INV-2025-889` as three space-separated tokens the pattern no
    /// longer sees an identifier and the pair falls through to the text fingerprint.
    /// That is a false-split risk, and it is the right way round: allowing spaces inside
    /// a reference would capture `ORDER NO 5 ITEMS TOTAL 12` as the reference `512`,
    /// and a wrong reference merges.
    func testAKnownLimitOCRThatBreaksAnIdentifierIntoWords() {
        XCTAssertEqual([], EntityResolver.identifiers(in: "INVOICE NO INV 2025 889"))
    }

    func testAHolderNameStopsAtTwoWords() {
        XCTAssertEqual(["JANE DOE"],
                       EntityResolver.holderNames(in: "IDENTITY CARD NAME: JANE DOE DATE OF BIRTH 1990"))
    }

    func testProseHasNoHolder() {
        XCTAssertEqual([], EntityResolver.holderNames(in: "the name of this thing is unclear"))
    }

    func testPageMarkers() {
        let p = EntityResolver.page(in: "CONTRACT PAGE 2 OF 4")
        XCTAssertEqual(2, p?.page); XCTAssertEqual(4, p?.total)
        let cn = EntityResolver.page(in: "第 3 页 共 7 页")
        XCTAssertEqual(3, cn?.page); XCTAssertEqual(7, cn?.total)
        XCTAssertNil(EntityResolver.page(in: "no pagination here"))
    }

    func testSimilarityOfNothingIsNotEvidenceOfDifference() {
        XCTAssertEqual(0, EntityResolver.textSimilarity("", "anything at all here"),
                       "an empty side means no evidence, and callers must not read 0 as "
                       + "proof that the two differ")
    }
}

/// The Tier 1-B PASS criterion, as rules rather than as a score.
final class ResolverDocumentTests: XCTestCase {

    func testTwoPassportsWithDifferentNumbersAreTwoPassports() {
        let a = rAsset("p1", text: "PASSPORT UNITED KINGDOM SURNAME: DOE PASSPORT NO: 123456789")
        let b = rAsset("p2", text: "PASSPORT UNITED KINGDOM SURNAME: DOE PASSPORT NO: 987654321",
                       dhash: 0x1234_5678_9ABC_DEF1)
        let r = rDecide(a, b)
        XCTAssertEqual(.different, r.verdict)
        XCTAssertFalse(r.mayMerge)
    }

    func testTwoIDCardsWithDifferentHoldersAreTwoCards() {
        let a = rAsset("i1", text: "IDENTITY CARD NAME: JANE DOE DATE OF BIRTH 1990-01-04")
        let b = rAsset("i2", text: "IDENTITY CARD NAME: JOHN ROE DATE OF BIRTH 1988-11-22",
                       dhash: 0x1234_5678_9ABC_DEF1)
        XCTAssertEqual(.different, rDecide(a, b).verdict)
    }

    /// Page 1 of two contracts on one template: same page number, same page count, same
    /// boilerplate. Only the contract number differs, and it has to win.
    func testADisagreeingReferenceBeatsEverySimilaritySignal() {
        let boiler = "THIS AGREEMENT is made between the parties and shall be governed "
                   + "by the laws of England and Wales. "
        let a = rAsset("c1", text: boiler + "CONTRACT NO: AB-4417 PAGE 1 OF 4")
        let b = rAsset("c2", text: boiler + "CONTRACT NO: ZZ-9902 PAGE 1 OF 4",
                       dhash: 0x1234_5678_9ABC_DEF1)
        let r = rDecide(a, b)
        XCTAssertEqual(.different, r.verdict)
        XCTAssertEqual("document.identifier", r.resolver)
    }

    func testPagesOfOneContractAreOneDocumentAndBothAreKept() {
        let boiler = "THIS AGREEMENT is made between the parties named below. "
        let a = rAsset("c3", text: boiler + "CONTRACT NO: AB-4417 PAGE 1 OF 4")
        let b = rAsset("c4", text: boiler + "CONTRACT NO: AB-4417 PAGE 2 OF 4",
                       dhash: 0x1234_5678_9ABC_DEF1)
        let r = rDecide(a, b)
        XCTAssertEqual(.same, r.verdict)
        XCTAssertEqual(.otherPage, r.relation)
    }

    /// Two document photographs that look identical and carry no readable text.
    /// Appearance is the only signal left, and for documents that is not enough.
    func testAnUnreadableDocumentIsNeverMergedOnLooks() {
        let a = rAsset("d1")
        let b = rAsset("d2", dhash: 0x1234_5678_9ABC_DEF0)
        let r = EntityResolver.resolve(a, b, asDocument("d1"), asDocument("d2"))
        XCTAssertEqual(.uncertain, r.verdict)
        XCTAssertFalse(r.mayMerge)
    }

    /// §9: both records survive. `.sameInstance` would let a caller fold them.
    func testOneDocumentOnTwoOccasionsIsAVersionNotADuplicate() {
        let a = rAsset("v1", text: "INVOICE NO: INV-2025-889 TOTAL 240.00")
        let b = rAsset("v2", text: "INVOICE NO: INV-2025-889 TOTAL 240.00 PAID",
                       when: rDate(2025, 7, 18), dhash: 0x1234_5678_9ABC_DEF1)
        let r = rDecide(a, b)
        XCTAssertEqual(.same, r.verdict)
        XCTAssertEqual(.otherVersion, r.relation)
    }
}

final class ResolverScreenshotTests: XCTestCase {

    func testOneOrderCapturedAtTwoStagesIsOnePurchase() {
        let a = rAsset("o1", text: "ORDER CONFIRMED ORDER NO: A88-2291 HEADPHONES",
                       screenshot: true)
        let b = rAsset("o2", text: "OUT FOR DELIVERY ORDER NO: A88-2291 ARRIVING TODAY",
                       when: rDate(2025, 6, 20), dhash: 0x0F0F_0F0F_0F0F_0F0F,
                       screenshot: true)
        let r = rDecide(a, b)
        XCTAssertEqual(.same, r.verdict)
        XCTAssertTrue(r.mayMerge)
    }

    func testTwoOrdersFromOneRetailerAreTwoOrders() {
        let a = rAsset("o3", text: "ORDER CONFIRMED ORDER NO: A88-2291 HEADPHONES",
                       screenshot: true)
        let b = rAsset("o4", text: "ORDER CONFIRMED ORDER NO: B12-7740 KEYBOARD",
                       dhash: 0x1234_5678_9ABC_DEF1, screenshot: true)
        XCTAssertEqual(.different, rDecide(a, b).verdict)
    }
}

/// Tier 1 allows a category to be downgraded to Review rather than guessed:
/// 部分类别（例如复杂物品识别）暂时做不到高置信度，可以先把这些类别降级为
/// 「Review Queue 优先」上线. This is that downgrade, made explicit.
final class ResolverObjectTests: XCTestCase {

    func testTheSameObjectWithinOneMomentResolves() {
        let a = rAsset("b1", dhash: 0xAAAA_BBBB_CCCC_DDDD, labels: ["bicycle"])
        let b = rAsset("b2", when: rWhen.addingTimeInterval(4),
                       dhash: 0xAAAA_BBBB_CCCC_DDDF, labels: ["bicycle"])
        XCTAssertEqual(.same, rDecide(a, b).verdict)
    }

    func testAcrossOccasionsItRefusesRatherThanGuesses() {
        let a = rAsset("c1", dhash: 0x0F0F_0F0F_0F0F_0F0F, labels: ["chair"])
        let b = rAsset("c2", when: rDate(2025, 6, 20),
                       dhash: 0x0F0F_0F0F_0F0F_0F0E, labels: ["chair"])
        let r = rDecide(a, b)
        XCTAssertEqual(.uncertain, r.verdict,
                       "one chair twice and two identical chairs look the same here; "
                       + "answering same would merge the second case")
        XCTAssertTrue(r.needsReview)
        XCTAssertFalse(r.mayMerge)
    }

    /// FC-1a: dHash returns 0 both for flat images and for failure.
    func testAMissingHashIsNeverReadAsAMatch() {
        let a = rAsset("h1", dhash: 0, labels: ["chair"])
        let b = rAsset("h2", dhash: 0, labels: ["chair"])
        XCTAssertEqual(.uncertain, rDecide(a, b).verdict)
    }
}

final class ResolverPhotoTests: XCTestCase {

    func testLookalikesTakenInTwoCitiesAreTwoPhotographs() {
        let a = rAsset("v1", dhash: 0xC0FF_EE00_C0FF_EE00,
                       geo: GeoFix(lat: 51.5074, lon: -0.1278))
        var b = rAsset("v2", when: rWhen.addingTimeInterval(7200),
                       dhash: 0xC0FF_EE00_C0FF_EE01)
        b.geo = GeoFix(lat: 50.8225, lon: -0.1372)
        b.place = PlaceName(country: "United Kingdom", city: "Brighton", confidence: 0.9)
        XCTAssertEqual(.different, rDecide(a, b).verdict)
    }

    func testByteIdentitySettlesItBeforeAnyCategoryQuestion() {
        let a = rAsset("m1", dhash: 0, contentHash: "sha::meme")
        let b = rAsset("m2", when: rDate(2025, 7, 28), dhash: 0, contentHash: "sha::meme")
        let r = EntityResolver.resolve(a, b)
        XCTAssertEqual(.same, r.verdict)
        XCTAssertEqual("bytes", r.resolver)
    }
}

final class ResolverEvidenceTests: XCTestCase {

    func testAResolutionCannotBeBuiltWithoutEvidence() {
        XCTAssertNil(Resolution(.same, .sameInstance, 0.9, "test", []))
    }

    func testEveryBranchExplainsItself() {
        let pairs: [(AssetSignals, AssetSignals)] = [
            (rAsset("a1", text: "PASSPORT NO: 111111"),
             rAsset("a2", text: "PASSPORT NO: 222222")),
            (rAsset("b1", labels: ["chair"]),
             rAsset("b2", when: rDate(2025, 6, 20), labels: ["chair"])),
            (rAsset("c1", dhash: 0), rAsset("c2", dhash: 0, contentHash: "other")),
            (rAsset("d1"), rAsset("d2", dhash: 0xFFFF_FFFF_FFFF_FFFF)),
        ]
        for (a, b) in pairs {
            let r = rDecide(a, b)
            XCTAssertFalse(r.why.trimmingCharacters(in: .whitespaces).isEmpty,
                           "\(r.resolver) explained nothing")
        }
    }
}

/// §24 Gate 2: 禁止寻找一个万能 Same-Entity 模型.
final class ResolverGateTests: XCTestCase {

    func testDifferentCategoriesUseDifferentResolvers() {
        var used: Set<String> = []
        let cases: [(AssetSignals, AssetSignals)] = [
            (rAsset("x1", text: "PASSPORT NO: 111111"),
             rAsset("x2", text: "PASSPORT NO: 222222", dhash: 0x1234_5678_9ABC_DEF1)),
            (rAsset("y1", text: "ORDER NO: A1-1 THING", screenshot: true),
             rAsset("y2", text: "ORDER NO: B2-2 OTHER",
                    dhash: 0x1234_5678_9ABC_DEF1, screenshot: true)),
            (rAsset("z1", labels: ["chair"]),
             rAsset("z2", when: rDate(2025, 6, 20), labels: ["chair"])),
            (rAsset("w1", dhash: 0xC0FF_EE00_C0FF_EE00),
             rAsset("w2", dhash: 0xFFFF_0000_FFFF_0000)),
        ]
        for (a, b) in cases {
            used.insert(String(rDecide(a, b).resolver.split(separator: ".")[0]))
        }
        XCTAssertGreaterThanOrEqual(used.count, 4,
                                    "one ladder answered every category: \(used)")
    }

    /// 低置信度只能进入 Review Queue，不自动合并/删除.
    func testAnUncertainPairReachesTheReviewListAndStaysDistinct() {
        let a = rAsset("r1", dhash: 0x0F0F_0F0F_0F0F_0F0F, labels: ["chair"])
        let b = rAsset("r2", when: rDate(2025, 6, 20),
                       dhash: 0x0F0F_0F0F_0F0F_0F0E, labels: ["chair"])
        let context = LibraryContextBuilder.build([a, b])
        let classifier = Classifier(context: context, budget: .text)
        let classifications = [a.assetID: classifier.classify(a),
                               b.assetID: classifier.classify(b)]
        let report = Dedup.analyse([a, b], classifications: classifications)

        XCTAssertEqual(1, report.needsEntityReview.count)
        XCTAssertFalse(report.needsEntityReview[0].2.trimmingCharacters(in: .whitespaces).isEmpty)
        for group in report.relations {
            XCTAssertEqual(group.members.sorted(), group.distinctMembers.sorted(),
                           "undecided is not permission to fold")
        }
    }
}
