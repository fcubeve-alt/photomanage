import Foundation

/// RISK, LIFECYCLE AND POLICY — Constitution §5, §6, §7, §8; L2 Tier 2-A.
///
/// The scale below is §6's, verbatim. An earlier version of the engine used these same
/// seven identifiers with invented meanings — R6 meant "not understood" where the
/// Constitution means "irreplaceable, highest protection" — so every catalogue row read
/// wrong against the document defining it. `RiskScaleTests` pins it clause by clause.
///
/// §5 is explicit that the action is not a function of category alone:
///   Category × Importance × Lifecycle × Confidence × Recoverability × Personal
///   Preference → Action Policy
/// So confidence is not a rung on this scale. Merging "we do not know what this is"
/// with a level of consequence is what let an unidentified asset outrank a passport.

public enum Risk: Int, Comparable, CaseIterable {
    case r0Disposable = 0      // 几乎无长期价值 · 完全重复下载、重复 Meme · 激进自动处理
    case r1LowValue = 1        // 通常短期/低价值 · 过期临时截图、验证码 · 自动处理或批量处理
    case r2Normal = 2          // 普通生活内容 · 风景、食物、普通物品 · 按相似度/生命周期处理
    case r3Personal = 3        // 具有个人意义 · 人物、旅行、生活事件 · 保守精选
    case r4Important = 4       // 可能承担交易/工作价值 · 收据、订单、工作资料 · Protect/Archive 优先
    case r5Critical = 5        // 法律/身份/金融价值 · 身份证、护照、合同、银行卡 · 默认 Protect
    case r6Irreplaceable = 6   // 可能不可替代 · 老照片、特殊家庭影像 · 最高保护

    public static func < (a: Risk, b: Risk) -> Bool { a.rawValue < b.rawValue }

    public var meaning: String {
        switch self {
        case .r0Disposable: return "几乎无长期价值"
        case .r1LowValue: return "通常短期/低价值"
        case .r2Normal: return "普通生活内容"
        case .r3Personal: return "具有个人意义"
        case .r4Important: return "可能承担交易/工作价值"
        case .r5Critical: return "法律/身份/金融价值"
        case .r6Irreplaceable: return "可能不可替代"
        }
    }

    public var defaultPolicy: String {
        switch self {
        case .r0Disposable: return "激进自动处理"
        case .r1LowValue: return "自动处理或批量处理"
        case .r2Normal: return "按相似度/生命周期处理"
        case .r3Personal: return "保守精选"
        case .r4Important: return "Protect/Archive 优先"
        case .r5Critical: return "默认 Protect"
        case .r6Irreplaceable: return "最高保护"
        }
    }

    /// What the user sees. §6's Chinese is the source of truth; this is the label.
    public var displayName: String {
        switch self {
        case .r0Disposable: return "Disposable"
        case .r1LowValue: return "Low value"
        case .r2Normal: return "Everyday"
        case .r3Personal: return "Personal"
        case .r4Important: return "Important"
        case .r5Critical: return "Critical"
        case .r6Irreplaceable: return "Irreplaceable"
        }
    }
}

/// §3 index dimension. Decides *when* something may be acted on, which is a different
/// question from how much it matters.
public enum Lifecycle: String {
    case temporary, active, expired, longTerm
}

/// §7's whole argument rests on this: tolerating cheap mistakes is only valid where the
/// mistake is genuinely recoverable. V-5 must confirm on a device that app-deleted
/// assets really do land in Recently Deleted for 30 days.
public enum Recoverability: String {
    case recoverable, hardToReplace, irreplaceable
}

/// §25 Layer 6, plus Suggest Delete from Tier 1-C.
///
/// There is deliberately no member meaning *permanent* deletion. `autoClean` is the
/// aggressive R0 action §6 calls for, constrained below to recoverable assets: the
/// deletion itself is the platform's, lands in Recently Deleted, and stays undoable.
public enum Action: String {
    // Raw values match `30_ENGINE/pvm/risk.py` exactly. Both implementations write into
    // the same schema, so they must write the same strings — "identical schema" with
    // different spellings for the same decision is not identical.
    case autoClean = "auto_clean"
    case suggestDelete = "suggest_delete"
    case selectBest = "select_best"
    case archive = "archive"
    case keep = "keep"
    case protectAsset = "protect"
    case review = "review"

    public var label: String {
        switch self {
        case .autoClean: return "Tidied automatically"
        case .suggestDelete: return "Suggested for removal"
        case .selectBest: return "Pick the best of these"
        case .archive: return "Archived"
        case .keep: return "Kept"
        case .protectAsset: return "Protected"
        case .review: return "Needs your eye"
        }
    }
}

public enum RiskPolicy {
    /// Tier 2-A PASS criterion: 高风险类别（R4-R6）零自动删除.
    public static let neverActAtOrAbove = Risk.r4Important

    /// Actions that can cost the user content. `archive` is deliberately NOT one: §6
    /// makes "Protect/Archive 优先" the correct default for R4, and archiving keeps the
    /// asset fully present and searchable. Counting it as lossy would have made the
    /// Constitution's own prescription look like a violation.
    public static let actingActions: Set<Action> = [.autoClean, .suggestDelete, .selectBest]
}

public struct Factors {
    public let risk: Risk
    public let lifecycle: Lifecycle
    public let confidence: Double
    public let recoverability: Recoverability
    public let inEquivalenceGroup: Bool
    public let isExactDuplicate: Bool
    public let personalPreference: Action?

    public init(risk: Risk, lifecycle: Lifecycle, confidence: Double,
                recoverability: Recoverability, inEquivalenceGroup: Bool = false,
                isExactDuplicate: Bool = false, personalPreference: Action? = nil) {
        self.risk = risk
        self.lifecycle = lifecycle
        self.confidence = confidence
        self.recoverability = recoverability
        self.inEquivalenceGroup = inEquivalenceGroup
        self.isExactDuplicate = isExactDuplicate
        self.personalPreference = personalPreference
    }
}

public struct Proposal {
    public let assetID: String
    public let action: Action
    public let factors: Factors
    public let evidence: [Evidence]
    public let note: String

    /// Fails rather than trapping, and the guards are the safety red lines themselves.
    public init?(assetID: String, action: Action, factors: Factors,
                 evidence: [Evidence], note: String = "") {
        guard !evidence.isEmpty else { return nil }
        if RiskPolicy.actingActions.contains(action),
           factors.risk >= RiskPolicy.neverActAtOrAbove { return nil }
        if RiskPolicy.actingActions.contains(action),
           factors.recoverability == .irreplaceable { return nil }
        if action == .autoClean {
            guard factors.risk == .r0Disposable else { return nil }
            guard factors.recoverability == .recoverable else { return nil }
        }
        self.assetID = assetID
        self.action = action
        self.factors = factors
        self.evidence = evidence
        self.note = note
    }

    public var requiresConfirmation: Bool { action != .autoClean }
    public var reversible: Bool { true }
    public var autoApplicable: Bool { action == .autoClean }
    public var why: String { evidence.map { $0.reason }.joined(separator: "; ") }
}

public enum RiskEngine {

    /// §6. Escalations before de-escalations: an exact duplicate of a passport is still
    /// a passport, so duplication only lowers risk for content that was disposable.
    public static func classify(_ c: Classification, isExactDuplicate: Bool = false,
                                hasPerson: Bool = false,
                                isIrreplaceable: Bool = false) -> Risk {
        if isIrreplaceable { return .r6Irreplaceable }

        var best: Risk?
        for path in c.paths {
            for (prefix, raw) in Rules.riskByPathPrefix {
                if path == prefix || path.hasPrefix(prefix + Taxonomy.separator) {
                    if let r = Risk(rawValue: raw) {
                        best = (best == nil) ? r : max(best!, r)
                    }
                    break
                }
            }
        }
        if hasPerson, best == nil || best! < .r3Personal { best = .r3Personal }

        // Nothing placed it. That is a confidence problem, not a level of consequence —
        // §5 keeps those axes apart, so it lands at Normal and the policy table routes
        // it to Review on its confidence.
        var level = best ?? .r2Normal

        // §6 R0 is 完全重复下载、重复 Meme. A byte-identical copy IS a re-download, so
        // this applies whether or not the classifier managed to file it — but only for
        // content that was disposable anyway.
        if isExactDuplicate, level <= .r2Normal { level = .r0Disposable }
        return level
    }

    public static func lifecycle(_ c: Classification, ageDays: Double?,
                                 transientGraceDays: Double = 30) -> Lifecycle {
        let transient = c.paths.contains { $0.hasPrefix("Screenshots > Temporary") }
        if transient {
            guard let age = ageDays else { return .temporary }
            return age >= transientGraceDays ? .expired : .temporary
        }
        let longTerm = c.paths.contains {
            let r = TaxonomyRuntime.root(of: $0)
            return r == "Documents" || r == "Purchases" || r == "People"
        }
        return longTerm ? .longTerm : .active
    }

    public static func recoverability(_ risk: Risk) -> Recoverability {
        if risk == .r6Irreplaceable { return .irreplaceable }
        if risk >= .r4Important { return .hardToReplace }
        return .recoverable
    }

    /// The §5 formula, as a table rather than a paragraph.
    public static func decide(_ f: Factors) -> Action {
        // §14: 用户的 Keep/Delete/Protect/Restore/Correction 逐渐形成 Personal Policy,
        // and 如果用户总是删除某类工作截图，系统以后可以更激进 — the Constitution
        // explicitly allows a personal policy to make the system *less* careful, not
        // only more. Honouring only PROTECT and KEEP, as this did, was safe and was not
        // what §14 says: it makes 系统越来越懂这个用户 impossible by construction.
        //
        // The resolution is not a compromise. §6's red lines are not preferences and
        // are not negotiable by anyone, the user included.
        if let pref = f.personalPreference {
            // More careful is always allowed, at any risk.
            if pref == .protectAsset || pref == .keep { return pref }
            // Less careful, only where acting is already permitted. Below R4 this turns
            // "ask again about a category they have answered the same way a dozen
            // times" into a proposal. At R4 and above it is ignored: no amount of
            // consistent behaviour makes a passport a disposable screenshot, and a
            // policy that could reach up there would be a mechanism for a user to talk
            // themselves out of the protection that exists precisely because one day
            // they will be tired and wrong.
            //
            // SUGGEST_DELETE is also the most aggressive thing a preference can ever
            // produce. AUTO_CLEAN is reachable only from byte-identical duplication,
            // which is evidence rather than taste.
            if pref == .suggestDelete, f.risk.rawValue < RiskPolicy.neverActAtOrAbove.rawValue {
                return .suggestDelete
            }
        }

        if f.risk >= .r5Critical { return .protectAsset }
        if f.risk == .r4Important { return f.lifecycle == .longTerm ? .archive : .keep }

        // Byte identity is checked BEFORE the confidence gate. `confidence` is
        // confidence in the *classification*; the evidence for an exact duplicate is a
        // content hash, certain whether or not we worked out what the picture shows.
        // Gating it sent every unidentifiable re-download to Review — the one thing the
        // system can genuinely automate became the thing it refused to do, which is the
        // trade §7 exists to forbid.
        if f.risk == .r0Disposable, f.isExactDuplicate, f.recoverability == .recoverable {
            return .autoClean
        }

        if f.confidence < Rules.reviewFloor { return .review }

        switch f.risk {
        case .r0Disposable:
            return f.lifecycle == .expired ? .suggestDelete : .keep
        case .r1LowValue:
            return f.lifecycle == .expired ? .suggestDelete : .keep
        default:
            // R2 Normal and R3 Personal — §6 says 保守精选 for R3: offered, never applied.
            return f.inEquivalenceGroup ? .selectBest : .keep
        }
    }

    public static func note(for action: Action) -> String {
        switch action {
        case .autoClean:
            return "an identical copy remains; removal goes to Recently Deleted and is undoable for 30 days"
        case .suggestDelete:
            return "offered for removal — it has passed the point where it is useful"
        case .selectBest:
            return "one of several near-identical frames; the frames that differ are kept"
        case .archive:
            return "kept and moved out of the way, still fully searchable"
        case .keep:
            return "kept where it is"
        case .protectAsset:
            return "protected — this is not offered for removal at all"
        case .review:
            return "not understood well enough to file confidently — kept and shown to you"
        }
    }

    public static func propose(_ c: Classification, _ f: Factors,
                               duplicateOf: String? = nil) -> Proposal? {
        var evidence: [Evidence] = []
        if let p = c.primary {
            evidence.append(contentsOf: p.evidence.prefix(2))
        } else if let first = c.assignments.first {
            evidence.append(contentsOf: first.evidence.prefix(1))
        }
        guard !evidence.isEmpty else { return nil }

        let action = decide(f)
        var note = RiskEngine.note(for: action)
        if action == .autoClean, let twin = duplicateOf {
            note = "byte-for-byte identical to \(twin), which stays; " + note
        }
        return Proposal(assetID: c.assetID, action: action, factors: f,
                        evidence: evidence, note: note)
    }

    /// Tier 2-A deliverable, generated from `decide` so it cannot drift from the code
    /// it documents.
    public static func policyTable() -> String {
        var lines = ["| risk | meaning | §6 default | lifecycle | confident | low confidence |",
                     "|---|---|---|---|---|---|"]
        for risk in Risk.allCases {
            for lc in [Lifecycle.expired, .active, .longTerm] {
                let dup = (risk == .r0Disposable)
                let hi = decide(Factors(risk: risk, lifecycle: lc, confidence: 0.9,
                                        recoverability: recoverability(risk),
                                        isExactDuplicate: dup))
                let lo = decide(Factors(risk: risk, lifecycle: lc, confidence: 0.3,
                                        recoverability: recoverability(risk),
                                        isExactDuplicate: dup))
                lines.append("| \(risk) | \(risk.meaning) | \(risk.defaultPolicy) | "
                             + "\(lc.rawValue) | \(hi.rawValue) | \(lo.rawValue) |")
            }
        }
        return lines.joined(separator: "\n")
    }
}
