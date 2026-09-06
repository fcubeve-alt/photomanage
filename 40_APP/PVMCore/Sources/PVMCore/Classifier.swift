import Foundation

/// THE CLASSIFIER — where a photo belongs, how sure we are, why, and stopping as early
/// as the evidence allows. Mirrors `30_ENGINE/pvm/classifier.py`.
///
/// The escalation policy is L1-B made executable: run the cheapest tier; if the answer
/// is already settled — a leaf, above the settle threshold — stop; otherwise buy the
/// next tier and ask again.
///
/// Two consequences, both features:
///  * Most of a real camera roll settles at metadata. A photo with a GPS fix and a date
///    is `Places > United Kingdom > London` and `Timeline > 2025` for free.
///  * When the evidence supports "Screenshots" and nothing narrower, the answer is
///    `Screenshots`. It does not guess a leaf. A library full of confidently wrong
///    leaves is worse than one that admits the depth it earned, because the user cannot
///    tell the two apart until they go looking for something.
public struct Classifier {

    private let context: LibraryContext
    private let budget: Tier
    private static var regexCache: [String: NSRegularExpression] = [:]
    private static let cacheLock = NSLock()

    public init(context: LibraryContext, budget: Tier = .text) {
        self.context = context
        self.budget = budget
    }

    public func classify(_ a: AssetSignals) -> Classification {
        var c = Classification(assetID: a.assetID)
        c.tiersSpent.insert(.metadata)

        timeline(a, &c)
        metadataRoot(a, &c)

        // Screenshots are exempt from the visual tiers. Face clustering and scene
        // classification on a chat window produce noise at full price — the only signal
        // that tells you anything about a screenshot is its text.
        let visualWorthIt = !(a.isScreenshot || a.isScreenRecording)

        if visualWorthIt, !settled(c), budget >= .visual {
            c.tiersSpent.insert(.visual)
            scenes(a, &c)
        }
        if visualWorthIt, !settled(c), budget >= .faces {
            c.tiersSpent.insert(.faces)
            faces(a, &c)
        }
        if budget >= .text, wantsText(a, c) {
            c.tiersSpent.insert(.text)
            text(a, &c)
        }

        // Places runs LAST among the content roots, and that ordering is load-bearing.
        // Run first, a GPS fix settled every photographed document as `Places > … >
        // London` at 0.91, the escalation policy saw a settled leaf, and the OCR pass
        // that would have recognised the passport never happened. Nine of nine
        // foreground documents were lost that way, silently, with a plausible answer in
        // their place. Location is context; it is not what the thing IS.
        places(a, &c)
        travel(a, &c)
        pruneImpliedAncestors(&c)
        crossList(&c)
        unfiled(&c)
        return c
    }

    // MARK: - escalation policy

    private func settled(_ c: Classification) -> Bool {
        guard let p = c.primary else { return false }
        return TaxonomyRuntime.isLeaf(p.path) && p.confidence >= Rules.settleAt
    }

    /// Whether to READ text that exists. Whether to SPEND an OCR pass is the C-1 gate,
    /// and it lives upstream where the pixels are. Duplicating that decision here on
    /// metadata the classifier cannot verify would be two gates disagreeing about one
    /// photo. Screenshots always read their text: the subtype settles the root, and
    /// only the text can ever open the leaf.
    private func wantsText(_ a: AssetSignals, _ c: Classification) -> Bool {
        guard a.ocrRan, !a.ocrText.isEmpty else { return false }
        if let p = c.primary, TaxonomyRuntime.root(of: p.path) == "Screenshots" { return true }
        return !settled(c)
    }

    // MARK: - tiers

    private func timeline(_ a: AssetSignals, _ c: inout Classification) {
        guard let when = a.createdAt, let year = a.year else {
            c.notes.append("no capture date — this asset cannot be placed on the timeline")
            return
        }
        guard let path = TaxonomyRuntime.ensure("Timeline" + Taxonomy.separator + String(year))
        else { return }
        let f = DateFormatter()
        f.locale = Locale(identifier: "en_GB")
        f.dateFormat = "d MMMM yyyy"
        guard let e = Evidence(signal: "createdAt", tier: .metadata, weight: 0.98,
                               reason: "taken on \(f.string(from: when))"),
              let assignment = Assignment(path: path, evidence: [e]) else { return }
        c.add(assignment)
    }

    private func metadataRoot(_ a: AssetSignals, _ c: inout Classification) {
        if a.isVideo {
            // The tree has eleven roots and none is Video. A real gap (FC-2), recorded
            // rather than papered over by filing video as a photo.
            c.notes.append("video: the taxonomy has no node for video assets (FC-2)")
        }
        if a.isScreenshot || a.isScreenRecording {
            if let e = Evidence(signal: "isScreenshot", tier: .metadata, weight: 0.95,
                                reason: "the system recorded this as a screenshot"),
               let assignment = Assignment(path: "Screenshots", evidence: [e], isPrimary: true) {
                c.add(assignment)
            }
            return
        }
        if a.source == "downloaded" {
            if let e = Evidence(signal: "source", tier: .metadata, weight: 0.88,
                                reason: "saved from another app rather than taken with the camera"),
               let assignment = Assignment(path: "Downloads", evidence: [e], isPrimary: true) {
                c.add(assignment)
            }
        }
    }

    /// Paperwork is not a place memory. A receipt photographed at the kitchen table does
    /// not belong on the Places shelf next to the holiday photos.
    private static let notPlaces: Set<String> = ["Documents", "Purchases", "Screenshots", "Downloads"]

    private func places(_ a: AssetSignals, _ c: inout Classification) {
        guard let geo = a.geo, geo.source == .exif else { return }
        guard let place = a.place, let country = place.country else { return }
        if c.assignments.contains(where: { Classifier.notPlaces.contains(TaxonomyRuntime.root(of: $0.path)) }) {
            return
        }
        var parts = ["Places", country]
        var reason = "the location saved with the photo is in \(country)"
        if let city = place.city {
            parts.append(city)
            reason = "the location saved with the photo is in \(city), \(country)"
        }
        guard let path = TaxonomyRuntime.ensure(parts.joined(separator: Taxonomy.separator)) else { return }
        let weight = min(0.92, 0.55 + 0.40 * place.confidence) * geo.confidence
        let isPrimary = !c.assignments.contains { $0.isPrimary }
        if let e = Evidence(signal: "geo", tier: .metadata, weight: weight, reason: reason),
           let assignment = Assignment(path: path, evidence: [e], isPrimary: isPrimary) {
            c.add(assignment)
        }
    }

    /// Travel is a library-level judgement, not a per-photo one: a run of days spent
    /// away from home. One photo in Tokyo is not a trip.
    private func travel(_ a: AssetSignals, _ c: inout Classification) {
        guard let trip = context.trip(for: a.createdAt, geo: a.geo) else { return }
        guard let path = TaxonomyRuntime.ensure("Travel" + Taxonomy.separator + trip.label) else { return }
        let cal = Calendar(identifier: .gregorian)
        let span = (cal.dateComponents([.day], from: trip.start, to: trip.end).day ?? 0) + 1
        let f = DateFormatter()
        f.locale = Locale(identifier: "en_GB")
        f.dateFormat = "MMMM yyyy"
        let where_ = trip.city ?? trip.country ?? "another place"
        if let e = Evidence(signal: "geo+createdAt", tier: .metadata, weight: 0.80,
                            reason: "part of \(span) days away from home in \(where_), \(f.string(from: trip.start))"),
           let assignment = Assignment(path: path, evidence: [e]) {
            c.add(assignment)
        }
    }

    private func faces(_ a: AssetSignals, _ c: inout Classification) {
        let named = a.namedPeople
        if named.isEmpty {
            if !a.faceClusters.isEmpty {
                // An unnamed cluster still changes the risk class, which is the point:
                // "someone is in this photo" is enough to stop treating it as disposable.
                c.notes.append("unnamed person present")
            }
            return
        }
        let path: String?
        let reason: String
        let weight: Double
        if named.count == 1 {
            path = TaxonomyRuntime.ensure("People" + Taxonomy.separator + named[0])
            reason = "\(named[0]) was recognised in this photo"
            weight = 0.88
        } else {
            path = "People > Groups"
            reason = "recognised " + named.joined(separator: ", ") + " together in this photo"
            weight = 0.85
        }
        guard let p = path else { return }
        let isPrimary = !c.assignments.contains { $0.isPrimary }
        if let e = Evidence(signal: "faceClusters", tier: .faces, weight: weight, reason: reason),
           let assignment = Assignment(path: p, evidence: [e], isPrimary: isPrimary) {
            c.add(assignment)
        }
    }

    private func scenes(_ a: AssetSignals, _ c: inout Classification) {
        var best: [String: SceneLabel] = [:]
        for label in a.sceneLabels where label.confidence >= Rules.sceneFloor {
            guard let path = Rules.sceneMap[label.identifier] else { continue }
            if let existing = best[path], existing.confidence >= label.confidence { continue }
            best[path] = label
        }
        for (path, label) in best {
            let weight = max(0.30, min(0.86, 0.30 + 0.60 * label.confidence))
            let pretty = label.identifier.replacingOccurrences(of: "_", with: " ")
            let root = TaxonomyRuntime.root(of: path)
            let isPrimary = !c.assignments.contains { $0.isPrimary }
                && (root == "Objects" || root == "Downloads")
            if let e = Evidence(signal: "sceneLabels", tier: .visual, weight: weight,
                                reason: "a \(pretty) was recognised in the picture"),
               let assignment = Assignment(path: path, evidence: [e], isPrimary: isPrimary) {
                c.add(assignment)
            }
        }
    }

    private static func regex(_ pattern: String) -> NSRegularExpression? {
        cacheLock.lock(); defer { cacheLock.unlock() }
        if let cached = regexCache[pattern] { return cached }
        guard let made = try? NSRegularExpression(pattern: pattern, options: [.caseInsensitive]) else {
            return nil
        }
        regexCache[pattern] = made
        return made
    }

    private func matches(_ pattern: String, _ text: String) -> Bool {
        guard let re = Classifier.regex(pattern) else { return false }
        let range = NSRange(text.startIndex..<text.endIndex, in: text)
        return re.firstMatch(in: text, options: [], range: range) != nil
    }

    private func text(_ a: AssetSignals, _ c: inout Classification) {
        let body = a.ocrText
        guard !body.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
        let root = c.primary.map { TaxonomyRuntime.root(of: $0.path) }

        // Within a group the first match wins, so specific rules precede general ones
        // in the generated table — `Documents > Identity > Passports` before `Documents`.
        let groups = [Rules.screenshotRules, Rules.documentRules,
                      Rules.purchaseRules, Rules.workTextRules]
        for group in groups {
            for rule in group {
                if let required = rule.requiresRoot, required != root { continue }
                guard matches(rule.pattern, body) else { continue }
                var isPrimary = !c.assignments.contains { $0.isPrimary }
                if root == "Screenshots", rule.requiresRoot == "Screenshots" {
                    isPrimary = true
                    for i in c.assignments.indices where c.assignments[i].path == "Screenshots" {
                        c.assignments[i].isPrimary = false
                    }
                }
                if let e = Evidence(signal: "ocrText", tier: .text, weight: rule.weight,
                                    reason: rule.reason),
                   let assignment = Assignment(path: rule.path, evidence: [e], isPrimary: isPrimary) {
                    c.add(assignment)
                }
                break
            }
        }
    }

    /// `Screenshots` and `Screenshots > Temporary > Pickup Codes` are one entry, not
    /// two. The browse tree rolls counts up from the leaves, so leaving both in would
    /// count the asset twice in its own parent. The ancestor's evidence is merged into
    /// the descendant rather than discarded — it is half the reason the leaf is right,
    /// and the user is owed the whole reason.
    private func pruneImpliedAncestors(_ c: inout Classification) {
        let held = Set(c.assignments.map { $0.path })
        for assignment in c.assignments {
            let deeper = held.filter { $0 != assignment.path
                && TaxonomyRuntime.ancestors(of: $0).contains(assignment.path) }
            guard let target = deeper.min(by: { TaxonomyRuntime.depth($0) < TaxonomyRuntime.depth($1) })
            else { continue }
            for i in c.assignments.indices where c.assignments[i].path == target {
                c.assignments[i].evidence.append(contentsOf: assignment.evidence)
                c.assignments[i].isPrimary = c.assignments[i].isPrimary || assignment.isPrimary
            }
            c.assignments.removeAll { $0.path == assignment.path }
        }
    }

    /// `_also_in` from the tree. One original, two entries (§3) — the receipt the user
    /// thinks of as paperwork and the receipt they think of as a purchase are the same
    /// photo, filed once.
    private func crossList(_ c: inout Classification) {
        for assignment in c.assignments {
            guard let also = TaxonomyRuntime.crossListing(of: assignment.path) else { continue }
            if let e = Evidence(signal: "taxonomy", tier: .metadata,
                                weight: min(0.9, assignment.confidence),
                                reason: "also filed under \(also) — the same photo, not a copy "
                                        + "(cross-listed from \(assignment.path))"),
               let extra = Assignment(path: also, evidence: [e],
                                      crossListedFrom: assignment.path) {
                c.add(extra)
            }
        }
    }

    /// An asset with a date and nothing else is on the timeline and nowhere else.
    /// Saying so is more useful than inventing a home for it, and it is the honest
    /// count of how much of a library the engine cannot yet explain.
    private func unfiled(_ c: inout Classification) {
        let content = c.assignments.filter { TaxonomyRuntime.root(of: $0.path) != "Timeline" }
        if content.isEmpty {
            c.notes.append("unfiled: no signal placed this asset anywhere but the timeline")
        }
    }
}
