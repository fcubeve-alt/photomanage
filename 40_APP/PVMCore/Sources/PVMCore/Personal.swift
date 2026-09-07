import Foundation

/// PERSONAL POLICY — §14, and the one place the product is allowed to change its mind.
///
///     Global Default Policy 是所有用户的初始规则。
///     用户的 Keep/Delete/Protect/Restore/Correction 逐渐形成 Personal Policy。
///     如果用户总是删除某类工作截图，系统以后可以更激进。
///     如果用户始终保留人物连拍，系统对该用户自动变得保守。
///                                                                     — L1 §14
///
/// THE TENSION THIS FILE RESOLVES, stated plainly because it is the whole design.
///
/// §14 says the system **may become more aggressive** for a category the user always
/// deletes. `RiskEngine.decide` honoured a personal preference only when it was PROTECT
/// or KEEP — it could be made more careful and never less. That is safe, and it is also
/// not what §14 says: it makes 系统越来越懂这个用户 impossible by construction.
///
/// The reconciliation is not "split the difference". §6's red lines are not preferences
/// and are not negotiable by anybody, the user included:
///
/// * **R4 and above are untouchable.** No amount of consistent behaviour makes a
///   passport a disposable screenshot. A policy that could reach R4 would be a
///   mechanism for a user to talk themselves out of the protection that exists
///   precisely because one day they will be tired and wrong.
/// * **Below that, §14 governs.** A demonstrated pattern may move a category from
///   Review to Suggest Delete — §18's Human Review Burden falling because the user
///   stops being asked something they have answered the same way a dozen times.
/// * **Nothing here is ever irreversible.** The most aggressive outcome is
///   SUGGEST_DELETE, which still needs confirmation and still goes to Recently Deleted.
///
/// And 总是 means a pattern, not a decision. One deletion is a mood; twelve with no
/// keeps is a preference. Mirrors `30_ENGINE/pvm/personal.py`.

public struct UserDecision {
    /// The five verbs §14 names, and no others. A feedback vocabulary that grows by
    /// guesswork is one where "the user did something" quietly becomes "the system may
    /// act".
    public enum Verb: String, CaseIterable {
        case keep, delete, protectAsset = "protect", restore, correction
    }

    public let assetID: String
    public let path: String
    public let verb: Verb
    public let at: Date

    public init(assetID: String, path: String, verb: Verb, at: Date) {
        self.assetID = assetID
        self.path = path
        self.verb = verb
        self.at = at
    }
}

public struct Preference {
    public let path: String
    public let action: Action
    public let observations: Int
    public let agreement: Double
    /// True when this makes the system *less* careful than the global default would be.
    /// Kept separate because it is the half that needs a red line.
    public let relaxes: Bool

    public var why: String {
        let verb: String
        switch action {
        case .suggestDelete: verb = "removed"
        case .keep: verb = "kept"
        case .protectAsset: verb = "protected"
        default: verb = "handled"
        }
        return "you have \(verb) \(Int(agreement * 100))% of the last \(observations) "
             + "things filed under \(path)"
    }
}

public struct PersonalPolicy {
    /// Empty is the correct starting state and is not a defect: a new user has told the
    /// system nothing, and §14's whole point is that the global default is where
    /// everyone begins.
    public private(set) var preferences: [String: Preference] = [:]
    public private(set) var decisionsSeen = 0

    /// Below this many decisions about a category there is no pattern — only a few
    /// choices, which every user makes differently on different days.
    public static let minObservations = 8
    /// And they have to agree. 总是 / 始终 is the Constitution's own word for this.
    public static let minAgreement = 0.85
    /// Risk at or above which no personal policy may make the system less careful.
    public static let neverRelaxAtOrAbove = RiskPolicy.neverActAtOrAbove

    public init() {}

    /// The most specific preference that applies, or nil.
    ///
    /// A user who deletes `Screenshots > Temporary` but keeps `Screenshots` has said
    /// two different things, and the deeper one is the one they said about this photo.
    public func preference(for paths: [String], risk: Risk) -> Preference? {
        var candidates: [Preference] = []
        for path in paths {
            for node in [path] + TaxonomyRuntime.ancestors(of: path) {
                if let p = preferences[node] { candidates.append(p) }
            }
        }
        guard let best = candidates.max(by: {
            TaxonomyRuntime.depth($0.path) < TaxonomyRuntime.depth($1.path)
        }) else { return nil }

        // §6 outranks §14. Dropping the preference entirely rather than clamping it to
        // KEEP is deliberate: at R4+ the global policy is already the careful answer,
        // and silently substituting a different one would make the explanation wrong.
        if best.relaxes, risk.rawValue >= PersonalPolicy.neverRelaxAtOrAbove.rawValue {
            return nil
        }
        return best
    }

    /// Turn a decision log into a policy.
    ///
    /// Corrections are counted and never become preferences: a correction says the
    /// *classification* was wrong, not that the action was. Reading "you filed this in
    /// the wrong place" as "you may delete things like this" is exactly the inference
    /// §11 and §16 exist to prevent.
    public static func learn(_ decisions: [UserDecision]) -> PersonalPolicy {
        let asPreference: [UserDecision.Verb: Action] = [
            .keep: .keep,
            .protectAsset: .protectAsset,
            // The loudest signal in the set — the user had to go and undo something.
            .restore: .protectAsset,
            .delete: .suggestDelete,
        ]

        var counts: [String: [Action: Int]] = [:]
        var policy = PersonalPolicy()
        policy.decisionsSeen = decisions.count

        for decision in decisions {
            guard let preference = asPreference[decision.verb] else { continue }
            for node in [decision.path] + TaxonomyRuntime.ancestors(of: decision.path) {
                counts[node, default: [:]][preference, default: 0] += 1
            }
        }

        for (path, tally) in counts {
            let observations = tally.values.reduce(0, +)
            guard observations >= minObservations else { continue }
            guard let (action, hits) = tally.max(by: { $0.value < $1.value }) else { continue }
            let agreement = Double(hits) / Double(observations)
            // An inconsistent category teaches nothing. Being asked case by case is
            // what the user is saying there, and taking the majority would read a coin
            // flip as a preference.
            guard agreement >= minAgreement else { continue }
            policy.preferences[path] = Preference(
                path: path, action: action, observations: observations,
                agreement: agreement,
                relaxes: action == .suggestDelete || action == .autoClean)
        }
        return policy
    }
}
