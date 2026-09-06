import XCTest
@testable import PVMCore

/// §6, §5 and the safety red lines. The scale is pinned to the Constitution clause by
/// clause because an earlier version of the reference engine used these same seven
/// identifiers with invented meanings, and every test passed because the tests asserted
/// the invented scale.

private func makeDate(_ y: Int, _ m: Int, _ d: Int) -> Date {
    var c = DateComponents(); c.year = y; c.month = m; c.day = d
    return Calendar(identifier: .gregorian).date(from: c)!
}

private func asset(_ id: String = "a", build: (inout AssetSignals) -> Void = { _ in }) -> AssetSignals {
    var s = AssetSignals(assetID: id)
    s.createdAt = makeDate(2025, 6, 18)
    build(&s)
    return s
}

private func classify(_ a: AssetSignals) -> Classification {
    Classifier(context: LibraryContext()).classify(a)
}

final class RiskScaleTests: XCTestCase {
    /// §6 风险等级与默认动作, verbatim.
    private let expected: [(Risk, String, String)] = [
        (.r0Disposable, "几乎无长期价值", "激进自动处理"),
        (.r1LowValue, "通常短期/低价值", "自动处理或批量处理"),
        (.r2Normal, "普通生活内容", "按相似度/生命周期处理"),
        (.r3Personal, "具有个人意义", "保守精选"),
        (.r4Important, "可能承担交易/工作价值", "Protect/Archive 优先"),
        (.r5Critical, "法律/身份/金融价值", "默认 Protect"),
        (.r6Irreplaceable, "可能不可替代", "最高保护"),
    ]

    func testTheScaleMatchesSection6Exactly() {
        XCTAssertEqual(Risk.allCases.count, expected.count)
        for (level, meaning, policy) in expected {
            XCTAssertEqual(level.meaning, meaning)
            XCTAssertEqual(level.defaultPolicy, policy)
        }
    }

    func testR6IsTheTopOfTheScaleNotAPlaceForConfusion() {
        XCTAssertEqual(Risk.allCases.max(), .r6Irreplaceable)
    }

    /// The two placements an earlier version had inverted, straight from §6's examples.
    func testReceiptsAreImportantAndPeopleArePersonal() {
        let receipt = classify(asset { s in
            s.ocrRan = true; s.ocrText = "RECEIPT — HEADPHONES £129.00"
        })
        XCTAssertEqual(RiskEngine.classify(receipt), .r4Important)

        let person = classify(asset { s in
            s.faceClusters = [FaceCluster(clusterID: "c", name: "Anna")]
        })
        XCTAssertEqual(RiskEngine.classify(person), .r3Personal)
    }

    func testIdentityDocumentsAreCritical() {
        let c = classify(asset { s in s.ocrRan = true; s.ocrText = "PASSPORT" })
        XCTAssertEqual(RiskEngine.classify(c), .r5Critical)
    }

    /// Escalations before de-escalations, or the cheapest fact about an asset would
    /// decide what happens to the most expensive one.
    func testADuplicatePassportIsStillAPassport() {
        let c = classify(asset { s in s.ocrRan = true; s.ocrText = "PASSPORT" })
        XCTAssertEqual(RiskEngine.classify(c, isExactDuplicate: true), .r5Critical)
    }

    /// §5 keeps consequence and confidence on separate axes. Giving an unplaced asset
    /// its own rung is what let it outrank a passport.
    func testAnUnplacedAssetDoesNotGetARiskLevelOfItsOwn() {
        let c = classify(asset())
        XCTAssertEqual(RiskEngine.classify(c), .r2Normal)
    }
}

final class PolicyTableTests: XCTestCase {
    /// Tier 2-A PASS criterion: 高风险类别（R4-R6）零自动删除.
    func testNoRiskLevelAtOrAboveR4IsEverActedOn() {
        for risk in [Risk.r4Important, .r5Critical, .r6Irreplaceable] {
            for lifecycle in [Lifecycle.temporary, .active, .expired, .longTerm] {
                for confidence in [0.1, 0.6, 0.99] {
                    let action = RiskEngine.decide(Factors(
                        risk: risk, lifecycle: lifecycle, confidence: confidence,
                        recoverability: RiskEngine.recoverability(risk),
                        inEquivalenceGroup: true, isExactDuplicate: true))
                    XCTAssertFalse(RiskPolicy.actingActions.contains(action),
                                   "\(risk)/\(lifecycle) produced \(action)")
                }
            }
        }
    }

    /// §7: a policy that never acts is as much a failure as one that acts wrongly.
    func testR0AndR1CanActuallyBeAutomated() {
        XCTAssertEqual(RiskEngine.decide(Factors(
            risk: .r0Disposable, lifecycle: .active, confidence: 0.9,
            recoverability: .recoverable, isExactDuplicate: true)), .autoClean)
        XCTAssertEqual(RiskEngine.decide(Factors(
            risk: .r1LowValue, lifecycle: .expired, confidence: 0.9,
            recoverability: .recoverable)), .suggestDelete)
    }

    func testLowConfidenceRoutesToReviewRatherThanToAction() {
        for risk in [Risk.r1LowValue, .r2Normal, .r3Personal] {
            XCTAssertEqual(RiskEngine.decide(Factors(
                risk: risk, lifecycle: .expired, confidence: 0.2,
                recoverability: .recoverable, isExactDuplicate: true)), .review,
                "\(risk) was acted on at 0.2 confidence")
        }
    }

    /// The one exception: a content hash is certain whether or not the classifier
    /// worked out what the picture shows. Gating it sent every unidentifiable
    /// re-download to Review — the one thing the system can genuinely automate became
    /// the thing it refused to do.
    func testByteIdentityIsNotAClassificationGuess() {
        XCTAssertEqual(RiskEngine.decide(Factors(
            risk: .r0Disposable, lifecycle: .active, confidence: 0.0,
            recoverability: .recoverable, isExactDuplicate: true)), .autoClean)
    }

    /// §14 lets the user's corrections outrank the default. Letting them loosen a
    /// protection would turn a red line into a setting.
    func testPersonalPreferenceCanOnlyMakeTheSystemMoreCareful() {
        XCTAssertEqual(RiskEngine.decide(Factors(
            risk: .r0Disposable, lifecycle: .expired, confidence: 0.99,
            recoverability: .recoverable, isExactDuplicate: true,
            personalPreference: .protectAsset)), .protectAsset)
        XCTAssertEqual(RiskEngine.decide(Factors(
            risk: .r5Critical, lifecycle: .active, confidence: 0.99,
            recoverability: .hardToReplace, personalPreference: .autoClean)), .protectAsset)
    }

    /// §8: Same Moment + Same Subject + High Similarity + Low Risk → 选代表照.
    func testAnEquivalenceGroupIsWhereSelectBestApplies() {
        XCTAssertEqual(RiskEngine.decide(Factors(
            risk: .r2Normal, lifecycle: .active, confidence: 0.9,
            recoverability: .recoverable, inEquivalenceGroup: true)), .selectBest)
    }
}

final class RedLineTests: XCTestCase {
    private func evidence() -> [Evidence] {
        [Evidence(signal: "s", tier: .metadata, weight: 0.9, reason: "r")!]
    }

    func testAnImportantAssetCanNeverBeProposedForDeletion() {
        for risk in [Risk.r4Important, .r5Critical, .r6Irreplaceable] {
            XCTAssertNil(Proposal(assetID: "x", action: .suggestDelete,
                                  factors: Factors(risk: risk, lifecycle: .expired,
                                                   confidence: 0.9,
                                                   recoverability: RiskEngine.recoverability(risk)),
                                  evidence: evidence()))
        }
    }

    func testAnIrreplaceableAssetMayNotBeActedOnAtAll() {
        for action in RiskPolicy.actingActions {
            XCTAssertNil(Proposal(assetID: "x", action: action,
                                  factors: Factors(risk: .r0Disposable, lifecycle: .expired,
                                                   confidence: 0.9, recoverability: .irreplaceable),
                                  evidence: evidence()))
        }
    }

    func testAutoCleanIsR0AndRecoverableOnly() {
        XCTAssertNil(Proposal(assetID: "x", action: .autoClean,
                              factors: Factors(risk: .r2Normal, lifecycle: .active,
                                               confidence: 0.9, recoverability: .recoverable),
                              evidence: evidence()))
        XCTAssertNil(Proposal(assetID: "x", action: .autoClean,
                              factors: Factors(risk: .r0Disposable, lifecycle: .active,
                                               confidence: 0.9, recoverability: .hardToReplace),
                              evidence: evidence()))
    }

    func testAProposalWithoutEvidenceCannotBeConstructed() {
        XCTAssertNil(Proposal(assetID: "x", action: .keep,
                              factors: Factors(risk: .r2Normal, lifecycle: .active,
                                               confidence: 0.9, recoverability: .recoverable),
                              evidence: []))
    }

    /// §16: the category holds documents. It never characterises the human.
    func testAMedicalDocumentIsFiledWithoutAnyClaimAboutThePerson() {
        let c = classify(asset { s in
            s.ocrRan = true; s.ocrText = "PRESCRIPTION — COLLECT AT PHARMACY"
        })
        XCTAssertEqual(c.primary?.path, "Documents > Medical")
        XCTAssertEqual(RiskEngine.classify(c), .r5Critical)
        XCTAssertTrue((c.explain()["Documents > Medical"] ?? "").lowercased()
            .contains("nothing about your health"))
    }
}

final class DedupGuardTests: XCTestCase {
    private func burst() -> [AssetSignals] {
        var frames: [AssetSignals] = []
        for i in 0..<4 {
            frames.append(asset("b\(i)") { s in
                s.createdAt = makeDate(2025, 6, 18).addingTimeInterval(Double(i))
                s.burstID = "B"; s.contentHash = "h\(i)"
                s.dhash = 0xF0F0_F0F0_F0F0_F0F0 | UInt64(i)
            })
        }
        frames.append(asset("b4") { s in
            s.createdAt = makeDate(2025, 6, 18).addingTimeInterval(4)
            s.burstID = "B"; s.contentHash = "h4"; s.dhash = 0x0F0F_0F0F_0F0F_0F0F
        })
        return frames
    }

    func testExactDuplicatesKeepTheEarliestAndFlagTheRest() {
        let a = asset("orig") { s in s.contentHash = "h"; s.dhash = 0xABCD }
        let b = asset("copy") { s in
            s.createdAt = makeDate(2025, 7, 18); s.contentHash = "h"; s.dhash = 0xABCD
        }
        let report = Dedup.analyse([a, b])
        XCTAssertEqual(report.exactDuplicateOf, ["copy": "orig"])
    }

    /// §9 Same Entity: one object, two occasions. Deleting either loses a record.
    func testTheSameCardPhotographedMonthsLaterIsNotADuplicate() {
        let a = asset("id1") { s in
            s.contentHash = "h1"; s.dhash = 0x1122_3344_5566_7788; s.ocrText = "ID CARD"
        }
        let b = asset("id2") { s in
            s.createdAt = makeDate(2025, 12, 18)
            s.contentHash = "h2"; s.dhash = 0x1122_3344_5566_7789; s.ocrText = "ID CARD"
        }
        let report = Dedup.analyse([a, b])
        XCTAssertTrue(report.exactDuplicateOf.isEmpty)
        XCTAssertTrue(report.relations.contains { $0.kind == "same_entity" })
    }

    /// The Document-class False Merge — the make-or-break number for Tier 1.
    func testTwoContractPagesThatLookAlikeAreNeverMerged() {
        let a = asset("c1") { s in
            s.contentHash = "h1"; s.dhash = 0x99AA_BBCC_DDEE_FF00
            s.ocrText = "CONTRACT — PAGE 1 OF 4"
        }
        let b = asset("c2") { s in
            s.createdAt = makeDate(2025, 6, 18).addingTimeInterval(60)
            s.contentHash = "h2"; s.dhash = 0x99AA_BBCC_DDEE_FF01
            s.ocrText = "CONTRACT — PAGE 2 OF 4"
        }
        let report = Dedup.analyse([a, b], documentIDs: ["c1", "c2"])
        XCTAssertTrue(report.exactDuplicateOf.isEmpty)
        let group = report.relations.first { Set($0.members) == ["c1", "c2"] }
        XCTAssertEqual(group?.distinctMembers.sorted(), ["c1", "c2"])
        XCTAssertTrue(group?.reason.contains("text differs") ?? false)
    }

    /// §8: frame 5 is the one everybody's eyes are open in. It is why the burst was
    /// taken, and it is the frame a naive collapse deletes.
    func testTheOneFrameThatDiffersSurvivesTheBurst() {
        let report = Dedup.analyse(burst())
        XCTAssertTrue(report.protectedDistinct.contains("b4"))
        XCTAssertFalse(report.nearDuplicateInMoment.contains("b4"))
    }

    /// FC-1a: dHash returns 0 for a class of ordinary images AND for every failure.
    func testAHashOfZeroIsAFailureAndNeverAMatch() {
        let a = asset("flat1") { s in s.contentHash = "h1"; s.dhash = 0 }
        let b = asset("flat2") { s in s.contentHash = "h2"; s.dhash = 0 }
        let report = Dedup.analyse([a, b])
        XCTAssertTrue(report.relations.isEmpty)
        XCTAssertEqual(report.unusableHash, ["flat1", "flat2"])
    }
}
