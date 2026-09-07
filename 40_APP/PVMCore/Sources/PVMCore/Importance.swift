// §4 精细 Visual Asset Taxonomy, and IMPORTANCE as an axis of its own.
//
// The reference implementation is `30_ENGINE/pvm/importance.py` and its docstring is
// the argument; this is the same logic where the app can reach it. §4's table itself
// is GENERATED into `Importance.generated.swift` — maintained by hand on two sides it
// would be two products, and the divergence would show up only in §18's Weighted Error
// Cost, which weights every error by exactly this number.
//
// The short version of why the axis exists at all:
//
//     a photo of a passport    — risk R5 (法律/身份/金融价值), importance ORDINARY.
//                                Losing the photo costs a walk to a scanner.
//     a photo of a grandmother — risk R3 (具有个人意义), importance TREASURED.
//                                Mishandling it is not a category of legal exposure.
//                                It is simply gone.
//
// An engine that grades only consequence protects the passport harder than the
// grandmother. §6 is not wrong about the passport; §5 is explicit that both answers
// are needed.

import Foundation

/// Everything that bears on 内容重要性, in one place — the same reason `Factors` exists.
public struct ImportanceSignals {
    public var paths: [String]
    public var recoverability: Recoverability
    /// How many assets in the whole library the named people in this one also appear
    /// in. Zero when nobody here is named.
    public var peopleRecurrence: Int
    /// Size of the §8 equivalence group this asset belongs to; 1 when it is alone.
    public var groupSize: Int
    public var inEquivalenceGroup: Bool
    public var isExactDuplicate: Bool
    public var isIrreplaceable: Bool
    /// §14. The user's own settled answer for this category, where they have given one.
    public var userProtectsCategory: Bool

    public init(paths: [String] = [], recoverability: Recoverability = .recoverable,
                peopleRecurrence: Int = 0, groupSize: Int = 1,
                inEquivalenceGroup: Bool = false, isExactDuplicate: Bool = false,
                isIrreplaceable: Bool = false, userProtectsCategory: Bool = false) {
        self.paths = paths
        self.recoverability = recoverability
        self.peopleRecurrence = peopleRecurrence
        self.groupSize = groupSize
        self.inEquivalenceGroup = inEquivalenceGroup
        self.isExactDuplicate = isExactDuplicate
        self.isIrreplaceable = isIrreplaceable
        self.userProtectsCategory = userProtectsCategory
    }
}

public struct ImportanceAssessment {
    public let level: Importance
    public let assetClass: AssetClass
    /// Why it is what it is. An importance score that cannot explain itself cannot be
    /// argued with by the person whose photographs it is about.
    public let reasons: [String]

    public var why: String { reasons.joined(separator: "; ") }
}

public enum ImportanceEngine {

    /// §4's 大类 for one asset.
    ///
    /// The two non-branch classes are checked first and in this order: irreplaceability
    /// outranks everything, and one frame of a burst of a treasured moment is still
    /// part of a treasured moment.
    public static func classify(paths: [String], isIrreplaceable: Bool = false,
                                inEquivalenceGroup: Bool = false) -> AssetClass {
        if isIrreplaceable { return AssetClasses.treasuredMemory }

        var best: AssetClass?
        var bestRank = AssetClasses.all.count
        var bestLength = -1
        for (rank, cls) in AssetClasses.all.enumerated() {
            for prefix in cls.prefixes {
                let hit = paths.contains {
                    $0 == prefix || $0.hasPrefix(prefix + Taxonomy.separator)
                }
                guard hit else { continue }
                // Longest prefix wins; ties break on §4's own order, which runs from
                // most consequential to least.
                if prefix.count > bestLength || (prefix.count == bestLength && rank < bestRank) {
                    best = cls
                    bestRank = rank
                    bestLength = prefix.count
                }
            }
        }
        if let found = best { return found }
        if inEquivalenceGroup { return AssetClasses.burstMoment }
        return AssetClasses.undescribed
    }

    /// 内容重要性, from the class baseline and what the library knows about this asset.
    ///
    /// Every adjustment is ±1 and records its reason.
    public static func assess(_ s: ImportanceSignals) -> ImportanceAssessment {
        let cls = classify(paths: s.paths, isIrreplaceable: s.isIrreplaceable,
                           inEquivalenceGroup: s.inEquivalenceGroup)
        var level = cls.baselineImportance.rawValue
        var reasons = ["§4 \(cls.name) baseline \(cls.baselineImportance)"]

        if s.recoverability == .irreplaceable {
            reasons.append("irreplaceable — nothing else raises or lowers this")
            return ImportanceAssessment(level: .i4Treasured, assetClass: cls,
                                        reasons: reasons)
        }

        if s.peopleRecurrence >= AssetClasses.recurringPerson {
            level += 1
            reasons.append("someone here appears in \(s.peopleRecurrence) other "
                           + "photographs — a person in this user's life, not a passer-by")
        }

        if s.userProtectsCategory {
            level += 1
            reasons.append("§14 — the user has consistently protected this category")
        }

        // §8: 同样的相似度，在 Meme 和家庭照片上采取不同策略. Applied to the frame and
        // not to the moment, and only one level, so a burst of a treasured occasion
        // does not fall out of protection because the shutter was held down.
        if s.inEquivalenceGroup, s.groupSize >= AssetClasses.burstSize {
            level -= 1
            reasons.append("one frame of \(s.groupSize) near-identical — the moment is "
                           + "kept, this particular frame is not the whole of it")
        }

        if s.isExactDuplicate {
            level -= 1
            reasons.append("a byte-identical copy exists — this file is not the content")
        }

        level = max(Importance.i0None.rawValue, min(Importance.i4Treasured.rawValue, level))
        return ImportanceAssessment(level: Importance(rawValue: level) ?? .i2Ordinary,
                                    assetClass: cls, reasons: reasons)
    }
}
