import Foundation

/// DUPLICATES, MOMENTS AND THE THINGS THAT ONLY LOOK LIKE DUPLICATES.
///
/// This is the part of a photo manager that destroys libraries. Every competitor ships
/// a "remove duplicates" button; the interesting question is what it does to the four
/// cases that are not duplicates and look exactly like them:
///
///  1. **Same Entity, different capture** (§9) — the same ID card six months later.
///  2. **Near-identical, different content** — pages 1 and 2 of a contract. This is the
///     Document-class False Merge, the make-or-break number for Tier 1.
///  3. **A burst where one frame is genuinely different** (§8) — frame 5 is the one
///     everyone's eyes are open in, and it is the frame a naive collapse deletes.
///  4. **A failed hash** — FC-1a: `dHash` returns 0 both for a class of ordinary images
///     and for every failure, so a failure is indistinguishable from a perfect match.
///
/// The policy is deliberately asymmetric. Exact byte-identity is the only thing allowed
/// to be confident. Everything else produces a *relation* — useful for browsing, and
/// never on its own a reason to remove anything.
/// Mirrors `30_ENGINE/pvm/dedup.py`.

public struct DuplicateGroup {
    public let keeper: String
    public let duplicates: [String]
    public let reason: String
}

/// Assets that belong together but must all survive.
public struct RelationGroup {
    public let kind: String        // "same_moment" | "same_entity" | "looks_alike"
    public let members: [String]
    public let distinctMembers: [String]
    public let reason: String
}

public struct DedupReport {
    public var exactGroups: [DuplicateGroup] = []
    public var relations: [RelationGroup] = []
    public var exactDuplicateOf: [String: String] = [:]
    public var nearDuplicateInMoment: Set<String> = []
    public var protectedDistinct: Set<String> = []
    public var unusableHash: Set<String> = []
}

public enum Dedup {
    /// 64-bit dHash. <= 5 differing bits is "looks the same to a person at thumbnail size".
    public static let nearBits = 5
    /// Above this, a frame inside a burst carries different content and is never an
    /// archive candidate, whatever the rest of the burst looks like (§8).
    public static let distinctBits = 10
    /// Two captures of the same thing more than this apart are a Same Entity relation,
    /// not redundancy — the second one was taken deliberately.
    public static let separateOccasionHours = 12.0

    public static func analyse(_ assets: [AssetSignals],
                               documentIDs: Set<String> = []) -> DedupReport {
        var report = DedupReport()

        // ---- exact: the only confident case ----------------------------
        var byHash: [String: [AssetSignals]] = [:]
        for a in assets {
            guard let h = a.contentHash else { continue }
            byHash[h, default: []].append(a)
        }
        for (_, group) in byHash where group.count > 1 {
            // The earliest capture is the original; the later ones are the copies.
            let ordered = group.sorted {
                let l = $0.createdAt ?? Date.distantPast
                let r = $1.createdAt ?? Date.distantPast
                return l == r ? $0.assetID < $1.assetID : l < r
            }
            let keeper = ordered[0]
            let rest = Array(ordered.dropFirst())
            report.exactGroups.append(DuplicateGroup(keeper: keeper.assetID,
                                                     duplicates: rest.map { $0.assetID },
                                                     reason: "byte-for-byte identical files"))
            for x in rest { report.exactDuplicateOf[x.assetID] = keeper.assetID }
        }

        // ---- moments: bursts and rapid sequences ------------------------
        var moments: [String: [AssetSignals]] = [:]
        for a in assets {
            guard let b = a.burstID else { continue }
            moments[b, default: []].append(a)
        }
        for (_, group) in moments where group.count > 1 {
            let distinct = distinctFrames(group)
            report.relations.append(RelationGroup(kind: "same_moment",
                                                  members: group.map { $0.assetID },
                                                  distinctMembers: distinct,
                                                  reason: "\(group.count) frames from one burst"))
            for x in group {
                if distinct.contains(x.assetID) { continue }
                if report.exactDuplicateOf[x.assetID] != nil { continue }
                report.nearDuplicateInMoment.insert(x.assetID)
            }
            // §8: the frames that differ are never archive candidates. Not "usually" —
            // never. The distinct frame is the reason the burst exists.
            report.protectedDistinct.formUnion(distinct)
        }

        // ---- look-alikes: a relation, never a removal -------------------
        for a in assets where !a.hasUsableDHash {
            if a.dhash != nil { report.unusableHash.insert(a.assetID) }
        }
        lookAlikes(assets, documentIDs: documentIDs, into: &report)
        return report
    }

    /// Inside a burst, a frame far from the others carries different content. Frames
    /// whose hash is unusable count as distinct: an unreadable hash is not permission to
    /// treat a photo as redundant (FC-1a).
    private static func distinctFrames(_ group: [AssetSignals]) -> [String] {
        let usable = group.filter { $0.hasUsableDHash }
        var distinct = group.filter { !$0.hasUsableDHash }.map { $0.assetID }
        guard usable.count >= 2 else { return group.map { $0.assetID } }

        for x in usable {
            let far = usable.filter { $0.assetID != x.assetID
                && hamming($0.dhash ?? 0, x.dhash ?? 0) > distinctBits }.count
            if far >= usable.count - 1 { distinct.append(x.assetID) }
        }
        if distinct.isEmpty {
            let first = group.sorted {
                ($0.createdAt ?? Date.distantPast) < ($1.createdAt ?? Date.distantPast)
            }.first
            if let f = first { distinct.append(f.assetID) }
        }
        return distinct
    }

    private static func lookAlikes(_ assets: [AssetSignals], documentIDs: Set<String>,
                                   into report: inout DedupReport) {
        // Bucket on the high bits so comparison stays near-linear instead of comparing
        // 100k assets pairwise. The cost of a rare miss is a relation we do not draw,
        // never a deletion.
        var buckets: [UInt64: [AssetSignals]] = [:]
        for a in assets where a.hasUsableDHash {
            buckets[(a.dhash ?? 0) >> 48, default: []].append(a)
        }
        var seen = Set<String>()
        for (_, bucket) in buckets {
            for i in bucket.indices {
                for j in bucket.indices where j > i {
                    let a = bucket[i], b = bucket[j]
                    if hamming(a.dhash ?? 0, b.dhash ?? 0) > nearBits { continue }
                    // Already related by a stronger fact. Restating it adds a row and no
                    // information, and a review queue full of restatements is one the
                    // user stops reading.
                    if let ah = a.contentHash, ah == b.contentHash { continue }
                    if let ab = a.burstID, ab == b.burstID { continue }
                    let key = [a.assetID, b.assetID].sorted().joined(separator: "|")
                    if seen.contains(key) { continue }
                    seen.insert(key)
                    report.relations.append(relate(a, b, documentIDs: documentIDs))
                }
            }
        }
    }

    private static func relate(_ a: AssetSignals, _ b: AssetSignals,
                               documentIDs: Set<String>) -> RelationGroup {
        let members = [a.assetID, b.assetID]
        var gapHours: Double?
        if let x = a.createdAt, let y = b.createdAt {
            gapHours = abs(x.timeIntervalSince(y)) / 3600
        }

        if documentIDs.contains(a.assetID) || documentIDs.contains(b.assetID) {
            let ta = a.ocrText.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
            let tb = b.ocrText.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
            if !ta.isEmpty, !tb.isEmpty, ta != tb {
                // Pages 1 and 2 of a contract. This is the false merge that matters.
                return RelationGroup(kind: "looks_alike", members: members,
                                     distinctMembers: members,
                                     reason: "these two pages look alike but their text differs — "
                                             + "kept as separate documents")
            }
            if ta.isEmpty || tb.isEmpty {
                return RelationGroup(kind: "looks_alike", members: members,
                                     distinctMembers: members,
                                     reason: "these look alike, but there is not enough text to be "
                                             + "sure they are the same document — both kept")
            }
        }

        if let gap = gapHours, gap > separateOccasionHours {
            // §9 Same Entity: one thing, two occasions. A relation the user wants, and a
            // deletion they would not forgive.
            return RelationGroup(kind: "same_entity", members: members,
                                 distinctMembers: members,
                                 reason: "the same subject photographed on two different occasions — "
                                         + "related, and both kept")
        }
        return RelationGroup(kind: "looks_alike", members: members, distinctMembers: [],
                             reason: "these look nearly identical")
    }
}
