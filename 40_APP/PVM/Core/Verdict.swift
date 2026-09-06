import Foundation

/// What the classifier returns, and the red line it enforces.
///
/// Safety red line, active since Tier 0: **every suggestion must be able to explain
/// why.** Enforced by failable construction rather than by convention, because a
/// convention is exactly the thing that erodes at 2am. Mirrors
/// `30_ENGINE/pvm/verdict.py`.

public struct Evidence {
    public let signal: String     // which field of AssetSignals this came from
    public let tier: Tier         // what it cost to acquire
    public let weight: Double     // 0..1 — how much doubt this alone removes
    public let reason: String     // shown to the user verbatim: write it for them

    /// Returns nil rather than trapping: an evidence-free reason is a programming
    /// error at the call site, and the call sites are all in this module.
    public init?(signal: String, tier: Tier, weight: Double, reason: String) {
        guard weight > 0, weight <= 1 else { return nil }
        guard !reason.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return nil }
        self.signal = signal
        self.tier = tier
        self.weight = weight
        self.reason = reason
    }
}

/// Noisy-or: independent evidence each removes some of the remaining doubt. Two weak
/// signals that agree beat either alone, and no finite amount of weak evidence reaches
/// certainty — which is the behaviour we want, because certainty authorises action.
public func combineConfidence(_ weights: [Double]) -> Double {
    var doubt = 1.0
    for w in weights { doubt *= (1.0 - w) }
    return min(Rules.maxConfidence, 1.0 - doubt)
}

public struct Assignment {
    public let path: String
    public var evidence: [Evidence]
    public var isPrimary: Bool
    public var crossListedFrom: String?

    /// An assignment with no evidence cannot be built. Nor can one naming a node that
    /// is not in the tree — a rule with a typo would otherwise produce a confident
    /// entry pointing at a folder nobody can open.
    public init?(path: String, evidence: [Evidence], isPrimary: Bool = false,
                 crossListedFrom: String? = nil) {
        guard !evidence.isEmpty else { return nil }
        guard TaxonomyRuntime.isKnown(path) else { return nil }
        self.path = path
        self.evidence = evidence
        self.isPrimary = isPrimary
        self.crossListedFrom = crossListedFrom
    }

    public var confidence: Double { combineConfidence(evidence.map { $0.weight }) }
    public var maxTier: Tier { evidence.map { $0.tier }.max() ?? .metadata }
    public var needsReview: Bool { confidence < Rules.reviewFloor }

    /// The red-line answer, in one line, for a human.
    public var why: String {
        evidence.sorted { $0.weight > $1.weight }.map { $0.reason }.joined(separator: "; ")
    }
}

public struct Classification {
    public let assetID: String
    public var assignments: [Assignment] = []
    /// The most expensive signal that ended up in the ANSWER.
    public var tierUsed: Tier = .metadata
    /// The tiers actually CONSULTED. Different numbers, and conflating them flatters
    /// the design — only the second one shows up in a battery graph.
    public var tiersSpent: Set<Tier> = []
    public var notes: [String] = []

    public init(assetID: String) { self.assetID = assetID }

    public mutating func add(_ assignment: Assignment) {
        if let i = assignments.firstIndex(where: { $0.path == assignment.path }) {
            assignments[i].evidence.append(contentsOf: assignment.evidence)
            assignments[i].isPrimary = assignments[i].isPrimary || assignment.isPrimary
            return
        }
        assignments.append(assignment)
        if assignment.maxTier > tierUsed { tierUsed = assignment.maxTier }
    }

    public var primary: Assignment? {
        let primaries = assignments.filter { $0.isPrimary }
        if !primaries.isEmpty { return primaries.max { $0.confidence < $1.confidence } }
        let content = assignments.filter { TaxonomyRuntime.root(of: $0.path) != "Timeline" }
        return content.max { $0.confidence < $1.confidence }
    }

    public var paths: [String] { assignments.map { $0.path } }

    public var needsReview: Bool {
        guard let p = primary else { return true }
        return p.needsReview
    }

    public var tierSpent: Tier { tiersSpent.max() ?? .metadata }

    public func explain() -> [String: String] {
        var out: [String: String] = [:]
        for a in assignments { out[a.path] = a.why }
        return out
    }
}
