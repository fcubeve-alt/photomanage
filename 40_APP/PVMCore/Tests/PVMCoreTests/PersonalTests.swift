import XCTest
@testable import PVMCore

/// Tests for Personal Policy — §14.
/// Ported from `30_ENGINE/tests/test_personal.py`.
///
///     如果用户总是删除某类工作截图，系统以后可以更激进。
///     如果用户始终保留人物连拍，系统对该用户自动变得保守。
///
/// The Constitution explicitly allows a personal policy to make the system **less**
/// careful, and `RiskEngine.decide` honoured only PROTECT and KEEP — safe, and not what
/// §14 says. Most of this file is about the line where §14 stops and §6 starts.

private let personalWhen = Date(timeIntervalSince1970: 1_767_268_800)

private func log(_ path: String, _ verb: UserDecision.Verb, _ n: Int) -> [UserDecision] {
    (0..<n).map {
        UserDecision(assetID: "\(path)-\($0)", path: path, verb: verb,
                     at: personalWhen.addingTimeInterval(Double($0) * 86_400))
    }
}

private func personalFactors(risk: Risk = .r2Normal, confidence: Double = 0.5,
                             preference: Action? = nil,
                             inEquivalenceGroup: Bool = false) -> Factors {
    Factors(risk: risk, lifecycle: .active, confidence: confidence,
            recoverability: .recoverable, inEquivalenceGroup: inEquivalenceGroup,
            isExactDuplicate: false, personalPreference: preference)
}

/// 总是 / 始终 is the Constitution's own word. One deletion is a mood.
final class WhatCountsAsAlwaysTests: XCTestCase {

    func testAFewDecisionsAreNotAPattern() {
        let policy = PersonalPolicy.learn(
            log("Screenshots > Work", .delete, PersonalPolicy.minObservations - 1))
        XCTAssertTrue(policy.preferences.isEmpty)
    }

    func testEnoughConsistentDecisionsAre() {
        let policy = PersonalPolicy.learn(
            log("Screenshots > Work", .delete, PersonalPolicy.minObservations))
        XCTAssertEqual(.suggestDelete, policy.preferences["Screenshots > Work"]?.action)
    }

    /// Being asked case by case is what the user is telling us here. Picking the
    /// majority would be reading a coin flip as a preference.
    func testAnInconsistentCategoryTeachesNothing() {
        let policy = PersonalPolicy.learn(log("Screenshots > Work", .delete, 6)
                                          + log("Screenshots > Work", .keep, 6))
        XCTAssertNil(policy.preferences["Screenshots > Work"])
    }

    func testThePreferenceSaysWhatItIsStandingOn() {
        let policy = PersonalPolicy.learn(log("Screenshots > Work", .delete, 12))
        let why = policy.preferences["Screenshots > Work"]?.why ?? ""
        XCTAssertTrue(why.contains("12"), why)
        XCTAssertTrue(why.contains("100%"), why)
    }

    /// A correction says the *classification* was wrong, not that the action was.
    /// Reading "you filed this in the wrong place" as "you may delete things like this"
    /// is the inference §11 and §16 exist to prevent.
    func testACorrectionIsNotAPreferenceAboutActions() {
        let policy = PersonalPolicy.learn(log("Screenshots > Work", .correction, 20))
        XCTAssertTrue(policy.preferences.isEmpty)
        XCTAssertEqual(20, policy.decisionsSeen)
    }
}

final class SectionFourteenIsHonouredTests: XCTestCase {

    func testADemonstratedPatternTurnsReviewIntoAProposal() {
        XCTAssertEqual(.review, RiskEngine.decide(personalFactors(confidence: 0.4)))
        XCTAssertEqual(.suggestDelete,
                       RiskEngine.decide(personalFactors(confidence: 0.4,
                                                         preference: .suggestDelete)),
                       "§14 allows the system to become more aggressive for a category "
                       + "the user always deletes")
    }

    /// 如果用户始终保留人物连拍，系统对该用户自动变得保守.
    func testKeepingBurstsOfPeopleMakesItConservative() {
        XCTAssertEqual(.keep, RiskEngine.decide(
            personalFactors(risk: .r3Personal, confidence: 0.9, preference: .keep,
                            inEquivalenceGroup: true)))
    }
}

/// §6's red lines are not preferences, and are not negotiable by anyone — the user
/// included. No amount of consistent behaviour makes a passport a disposable
/// screenshot.
final class SectionSixIsNotNegotiableTests: XCTestCase {

    func testADeletePreferenceCannotReachR4() {
        for risk in [Risk.r4Important, .r5Critical, .r6Irreplaceable] {
            let action = RiskEngine.decide(
                personalFactors(risk: risk, preference: .suggestDelete))
            XCTAssertNotEqual(.suggestDelete, action, "\(risk) was relaxed")
            XCTAssertNotEqual(.autoClean, action, "\(risk) was relaxed")
        }
    }

    /// One guard is a single point of failure, so the policy withholds it as well.
    func testThePolicyWithholdsItTooRatherThanRelyingOnOneGuard() {
        let policy = PersonalPolicy.learn(
            log("Documents > Identity > Passports", .delete, 30))
        XCTAssertNil(policy.preference(for: ["Documents > Identity > Passports"],
                                       risk: .r5Critical))
    }

    func testBecomingMoreCarefulIsAllowedAtAnyRisk() {
        for risk in Risk.allCases {
            XCTAssertEqual(.protectAsset,
                           RiskEngine.decide(personalFactors(risk: risk,
                                                             preference: .protectAsset)),
                           "\(risk)")
        }
    }

    /// The most aggressive thing a preference may produce is SUGGEST_DELETE, which
    /// still requires confirmation. AUTO_CLEAN is reachable only from byte-identical
    /// duplication, which is evidence rather than taste.
    func testNoPreferenceCanProduceAnIrreversibleAction() {
        for preference in [Action.autoClean, .suggestDelete] {
            XCTAssertNotEqual(.autoClean, RiskEngine.decide(
                personalFactors(confidence: 0.4, preference: preference)))
        }
    }
}

final class MostSpecificWinsTests: XCTestCase {

    func testADeeperPreferenceBeatsAShallowerOne() {
        let policy = PersonalPolicy.learn(log("Screenshots > Temporary", .delete, 12)
                                          + log("Screenshots > Chat", .keep, 12))
        let deep = policy.preference(for: ["Screenshots > Temporary"], risk: .r1LowValue)
        XCTAssertEqual("Screenshots > Temporary", deep?.path)
        XCTAssertEqual(.suggestDelete, deep?.action)
    }

    func testACategoryTheUserNeverTouchedHasNoPreference() {
        let policy = PersonalPolicy.learn(log("Screenshots > Work", .delete, 12))
        XCTAssertNil(policy.preference(for: ["People > Anna"], risk: .r3Personal))
    }

    /// A new user has told the system nothing, and §14's whole point is that the global
    /// default is where everyone begins.
    func testANewLibraryHasNoPolicyAndThatIsCorrect() {
        XCTAssertNil(PersonalPolicy().preference(for: ["Screenshots"], risk: .r2Normal))
    }
}
