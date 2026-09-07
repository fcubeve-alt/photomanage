import Foundation

/// THE VISUAL MEMORY GRAPH — §2 "Remember".
///
/// §2 lists ten steps the product *is*, and Remember is one of them: *"把照片变成现实
/// 人物、物品、地点、文件、购买和事件的证据"*. §15 builds Wardrobe, Travel Memory,
/// Purchase & Warranty and Object Memory on top of it, and L1-B §4 says what a video
/// must ultimately leave behind is not analysed frames but *"这个视频对用户个人视觉记忆
/// 真正贡献的新信息"*.
///
/// The catalogue files photos onto shelves. Filing is not remembering: a filing system
/// can say which shelf a photo is on, and cannot answer L1-B's own worked example —
/// *"我的红色行李箱最后在哪里出现过？"* — because that needs entities which persist
/// across assets rather than labels stuck to each one.
///
/// Mirrors `30_ENGINE/pvm/memory.py`. Three boundaries hold on both sides:
///
/// * Every entity and every observation carries its evidence. An entity nobody can
///   justify is a claim, and the red line says a claim must explain itself.
/// * §11: an inferred fact declares that it is inferred — and entity provenance is
///   kept apart from place provenance, because a sentence can be half measured and
///   half guessed and only the guessed half should be hedged.
/// * §15/§16: co-occurrence is a count of shared appearances and nothing more. There
///   is no kind for a relationship, and the graph never characterises anyone.

public enum EntityKind: String, CaseIterable {
    case person, place, object, document, purchase, event
}

/// A thing in the world that the library has evidence for.
public struct Entity {
    public let entityID: String
    public let kind: EntityKind
    public let name: String
    public var evidence: [Evidence]
    /// Where the catalogue files this thing, when the two differ. The shelf is coarse
    /// ("Objects > Other"); the entity is specific ("Suitcase"). Keeping both lets the
    /// memory answer a question the shelf cannot, without pretending the shelf is
    /// finer than it is.
    public var categoryPath: String?

    /// Fails rather than traps on empty evidence, matching `Assignment`: the call
    /// sites are all in this module, so an unjustified entity is a bug here, not a
    /// runtime condition to survive.
    public init?(entityID: String, kind: EntityKind, name: String,
                 evidence: [Evidence], categoryPath: String? = nil) {
        guard !evidence.isEmpty else { return nil }
        guard !name.trimmingCharacters(in: .whitespaces).isEmpty else { return nil }
        self.entityID = entityID
        self.kind = kind
        self.name = name
        self.evidence = evidence
        self.categoryPath = categoryPath
    }

    public var confidence: Double { combineConfidence(evidence.map { $0.weight }) }

    public var why: String {
        evidence.sorted { $0.weight > $1.weight }.map { $0.reason }.joined(separator: "; ")
    }
}

/// This entity, seen in this asset. The unit the whole graph is made of.
public struct Observation {
    public enum Source: String { case measured, inferred }

    public let entityID: String
    public let assetID: String
    public let when: Date?
    public let place: String?
    public let confidence: Double
    public let reason: String
    /// How the *entity* was identified — a named face, a read of the page.
    public var source: Source = .measured
    /// How the *location* was established — a GPS fix is measured, a location borrowed
    /// from neighbouring photos is inferred. Separate from `source` because they can
    /// differ, and reporting the pair as measured is precisely the §11 failure.
    public var placeSource: Source = .measured
    /// Set to the anchor asset when this sighting repeats another from the same
    /// moment. A flag, never a deletion: the observation stays and a view may fold it.
    public var repeatsAsset: String?

    public init(entityID: String, assetID: String, when: Date?, place: String?,
                confidence: Double, reason: String,
                source: Source = .measured, placeSource: Source = .measured,
                repeatsAsset: String? = nil) {
        self.entityID = entityID
        self.assetID = assetID
        self.when = when
        self.place = place
        self.confidence = confidence
        self.reason = reason
        self.source = source
        self.placeSource = placeSource
        self.repeatsAsset = repeatsAsset
    }

    public var isInferred: Bool { source != .measured || placeSource != .measured }
    public var placeIsInferred: Bool { place != nil && placeSource != .measured }
}

public struct MemoryGraph {
    public private(set) var entities: [String: Entity] = [:]
    public private(set) var observations: [Observation] = []

    public init() {}

    // MARK: - building

    @discardableResult
    public mutating func add(_ entity: Entity) -> Entity {
        guard var existing = entities[entity.entityID] else {
            entities[entity.entityID] = entity
            return entity
        }
        let known = Set(existing.evidence.map { $0.reason })
        for e in entity.evidence where !known.contains(e.reason) {
            existing.evidence.append(e)
        }
        entities[entity.entityID] = existing
        return existing
    }

    public mutating func observe(_ observation: Observation) {
        observations.append(observation)
    }

    // MARK: - queries

    /// Every sighting, oldest first. Undated ones come last rather than being dropped:
    /// an undated sighting is still a sighting.
    public func history(of entityID: String) -> [Observation] {
        let seen = observations.filter { $0.entityID == entityID }
        let dated = seen.filter { $0.when != nil }.sorted { $0.when! < $1.when! }
        return dated + seen.filter { $0.when == nil }
    }

    public func lastSeen(_ entityID: String) -> Observation? {
        observations
            .filter { $0.entityID == entityID && $0.when != nil }
            .max { $0.when! < $1.when! }
    }

    /// Match the user's words against entity names, in two passes ordered by how much
    /// they claim: a substring hit is close to what was asked for; a word hit — "red
    /// suitcase" finding *Suitcase* — is looser. They stay separate so the answer can
    /// say when it only matched part of the question.
    public func find(_ text: String, kind: EntityKind? = nil) -> [Entity] {
        let needle = text.trimmingCharacters(in: .whitespaces).lowercased()
        guard !needle.isEmpty else { return [] }
        let pool = entities.values.filter { kind == nil || $0.kind == kind! }

        let exact = pool.filter { $0.name.lowercased().contains(needle) }
        if !exact.isEmpty { return exact.sorted { $0.confidence > $1.confidence } }

        let words = Set(needle.split(separator: " ").map(String.init).filter { $0.count > 2 })
        let loose = pool.filter { entity in
            !words.isDisjoint(with: Set(entity.name.lowercased().split(separator: " ").map(String.init)))
        }
        return loose.sorted { $0.confidence > $1.confidence }
    }

    /// Which entities show up in the same assets, and how often.
    ///
    /// §15 says relationship views must not infer sensitive relations casually. This
    /// returns a count of shared appearances and nothing more — an observation, not a
    /// conclusion about what two people are to each other.
    public func coOccurring(_ entityID: String, kind: EntityKind? = nil) -> [(String, Int)] {
        let mine = Set(observations.filter { $0.entityID == entityID }.map { $0.assetID })
        var counts: [String: Int] = [:]
        for o in observations where o.entityID != entityID && mine.contains(o.assetID) {
            if let k = kind, entities[o.entityID]?.kind != k { continue }
            counts[o.entityID, default: 0] += 1
        }
        return counts.sorted { $0.value == $1.value ? $0.key < $1.key : $0.value > $1.value }
            .map { ($0.key, $0.value) }
    }

    /// L1-B's own worked example, answered in the user's words, with the uncertainty
    /// in the answer rather than behind it.
    ///
    /// Three things it refuses to hide: an inferred place is described as inferred
    /// (§11); a **category-level** entity is not an instance, so when the question
    /// asked for more than the name could match the answer says which part went
    /// unanswered; and an entity with no dated sighting has no "last".
    public func answerWhereLastSeen(_ text: String) -> String {
        let matches = find(text)
        guard let entity = matches.first else {
            return "Nothing in the library is recorded as “\(text)”."
        }
        guard let observation = lastSeen(entity.entityID) else {
            return "\(entity.name) is in the library, but none of those photos carry a "
                 + "date, so there is no “last”."
        }

        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_GB")
        formatter.timeZone = TimeZone(identifier: "UTC")
        formatter.dateFormat = "d MMMM yyyy"

        let when = formatter.string(from: observation.when!)
        let where_ = observation.place ?? "somewhere without a recorded location"
        let hedge = observation.placeIsInferred
            ? " (place inferred from nearby photos, not recorded by the camera)" : ""
        var answer = "\(entity.name) was last seen on \(when), \(where_)\(hedge) — "
                   + "\(observation.reason)."

        let unmatched = MemoryGraph.unmatchedWords(text, entity)
        if !unmatched.isEmpty {
            let noun = entity.name.lowercased()
            answer += " I matched “\(noun)” only — nothing in the library distinguishes "
                    + "\(unmatched.joined(separator: " ")), so this is the most recent "
                    + "\(noun), which may not be yours."
        }
        return answer
    }

    static func unmatchedWords(_ text: String, _ entity: Entity) -> [String] {
        let asked = text.trimmingCharacters(in: .whitespaces).lowercased()
            .split(separator: " ").map(String.init).filter { $0.count > 2 }
        var known = Set(entity.name.lowercased().split(separator: " ").map(String.init))
        known.formUnion(["the", "my", "your"])
        return asked.filter { !known.contains($0) }
    }

    public var stats: [String: Int] {
        var out = ["entities": entities.count, "observations": observations.count]
        for kind in EntityKind.allCases {
            out["kind_\(kind.rawValue)"] = entities.values.filter { $0.kind == kind }.count
        }
        return out
    }
}

// MARK: - Building the graph from what the classifier already worked out
//
// L1-B's processing order applies here too: nothing in this file spends new
// intelligence. A person comes from a face cluster the user already named, a place
// from a GPS fix already in the metadata row, an object from a scene label that was
// going to be computed anyway.

public enum MemoryBuilder {

    public static func build(assets: [AssetSignals],
                             classifications: [String: Classification],
                             context: LibraryContext? = nil,
                             momentGroups: [[String]] = []) -> MemoryGraph {
        var graph = MemoryGraph()
        var byID: [String: AssetSignals] = [:]
        for a in assets { byID[a.assetID] = a }

        for asset in assets {
            guard let c = classifications[asset.assetID] else { continue }
            var placeName: String?
            if let p = asset.place, let n = p.city ?? p.country, !n.isEmpty { placeName = n }
            // Established once and carried by every observation this asset produces.
            // Attaching the hedge to one entity kind and not the rest is how a place
            // becomes a fact by omission.
            var placeSource: Observation.Source =
                (asset.geo == nil || asset.geo!.source == .exif) ? .measured : .inferred
            // §11's inference lives in the context rather than on the asset, because
            // the assets are the caller's and the engine does not rewrite them.
            // Without this the graph would have said nothing about where these assets
            // were, while the classifier was filing them under `Places` — so "where
            // did I last see this" would have answered from a smaller library than the
            // one the user browses.
            if placeName == nil, let ctx = context,
               let guess = ctx.inferredPlace(for: asset.assetID),
               let n = guess.place.city ?? guess.place.country, !n.isEmpty {
                placeName = n
                placeSource = .inferred
            }

            people(asset, placeName, placeSource, &graph)
            places(asset, placeName, placeSource, &graph)
            objects(asset, c, placeName, placeSource, &graph)
            documents(asset, c, placeName, placeSource, &graph)
            purchases(asset, c, placeName, placeSource, &graph)
        }

        if let context { events(context, byID, &graph) }
        if !momentGroups.isEmpty { markRepeats(momentGroups, byID, &graph) }
        return graph
    }

    // MARK: people and places

    private static func people(_ asset: AssetSignals, _ placeName: String?,
                               _ placeSource: Observation.Source, _ graph: inout MemoryGraph) {
        for face in asset.faceClusters {
            guard let name = face.name, !name.isEmpty else { continue }
            let id = "person:" + slug(name)
            guard let e = Evidence(signal: "face_clusters", tier: .faces, weight: 0.88,
                                   reason: "\(name) is a face you named"),
                  let entity = Entity(entityID: id, kind: .person, name: name, evidence: [e])
            else { continue }
            graph.add(entity)
            graph.observe(Observation(
                entityID: id, assetID: asset.assetID, when: asset.createdAt,
                place: placeName, confidence: 0.88,
                reason: "\(name) was recognised in this photo", placeSource: placeSource))
        }
    }

    private static func places(_ asset: AssetSignals, _ placeName: String?,
                               _ placeSource: Observation.Source, _ graph: inout MemoryGraph) {
        guard let placeName, let geo = asset.geo else { return }
        let measured = geo.source == .exif
        let weight = measured ? 0.9 : 0.6
        let id = "place:" + slug(placeName)
        guard let e = Evidence(signal: "geo", tier: .metadata, weight: weight,
                               reason: "photos carry a location in \(placeName)"),
              let entity = Entity(entityID: id, kind: .place, name: placeName, evidence: [e])
        else { return }
        graph.add(entity)
        graph.observe(Observation(
            entityID: id, assetID: asset.assetID, when: asset.createdAt,
            place: placeName, confidence: weight,
            reason: "this photo was taken in \(placeName)",
            source: measured ? .measured : .inferred, placeSource: placeSource))
    }

    // MARK: objects

    /// Objects are named by what was *recognised*, not by the shelf they land on.
    ///
    /// This is the clearest reason the memory exists separately from the catalogue.
    /// `Objects` is not an extensible root and its leaves are coarse — Bicycle,
    /// Appliances, Devices, Furniture, Other. A suitcase files under `Objects > Other`,
    /// and a catalogue stopping there could only ever say "you have some objects".
    ///
    /// One limit, stated rather than papered over: this is a **category-level** entity.
    /// "Suitcase" is every suitcase in the library, not your red one. Telling two apart
    /// is per-category entity resolution (§24 Gate 2), which is not built — so the
    /// graph must not imply an instance it cannot distinguish.
    private static func objects(_ asset: AssetSignals, _ c: Classification,
                                _ placeName: String?, _ placeSource: Observation.Source,
                                _ graph: inout MemoryGraph) {
        let objectPaths = Set(c.paths.filter {
            let r = TaxonomyRuntime.root(of: $0)
            return r == "Objects" || r == "Clothing"
        })
        guard !objectPaths.isEmpty else { return }

        var named: [(String, String, Double)] = []
        for label in asset.sceneLabels {
            if let path = Rules.sceneMap[label.identifier], objectPaths.contains(path) {
                named.append((pretty(label.identifier), path, min(0.9, label.confidence)))
            }
        }
        // No label explains the path — fall back to the shelf, but never to "Other",
        // which names nothing and would create an entity called "Other".
        if named.isEmpty {
            for path in objectPaths.sorted() {
                let shelf = leaf(of: path)
                if shelf != "Other" { named.append((shelf, path, 0.7)) }
            }
        }

        for (name, path, confidence) in named {
            let id = "object:" + slug(name)
            guard let e = Evidence(signal: "scene_labels", tier: .visual, weight: confidence,
                                   reason: "a \(name.lowercased()) was recognised in your photos"),
                  let entity = Entity(entityID: id, kind: .object, name: name,
                                      evidence: [e], categoryPath: path)
            else { continue }
            graph.add(entity)
            graph.observe(Observation(
                entityID: id, assetID: asset.assetID, when: asset.createdAt,
                place: placeName, confidence: confidence,
                reason: "a \(name.lowercased()) appears in this photo",
                placeSource: placeSource))
        }
    }

    // MARK: documents and purchases

    private static func documents(_ asset: AssetSignals, _ c: Classification,
                                  _ placeName: String?, _ placeSource: Observation.Source,
                                  _ graph: inout MemoryGraph) {
        for path in c.paths where path.hasPrefix("Documents") {
            let shelf = leaf(of: path)
            if shelf == "Other Documents" || shelf == "Documents" { continue }
            let name = singular(shelf)
            let id = "document:" + slug(name)
            guard let e = Evidence(signal: "ocr_text", tier: .text, weight: 0.85,
                                   reason: "the text on the page identifies it as a \(name.lowercased())"),
                  let entity = Entity(entityID: id, kind: .document, name: name,
                                      evidence: [e], categoryPath: path)
            else { continue }
            graph.add(entity)
            graph.observe(Observation(
                entityID: id, assetID: asset.assetID, when: asset.createdAt,
                place: placeName, confidence: 0.85,
                reason: "this is a photo of your \(name.lowercased())",
                placeSource: placeSource))
        }
    }

    /// §15 Purchase & Warranty Memory: a receipt is evidence about a *thing you own*.
    /// The item name is read out of the text OCR already produced — nothing new is
    /// spent — and where the text names no item the entity is simply "Purchase".
    /// Inventing a product name from a total and a date is exactly the confident guess
    /// §11 forbids.
    private static func purchases(_ asset: AssetSignals, _ c: Classification,
                                  _ placeName: String?, _ placeSource: Observation.Source,
                                  _ graph: inout MemoryGraph) {
        guard c.paths.contains(where: { $0.hasPrefix("Purchases") }) else { return }
        let name = purchaseItem(asset.ocrText) ?? "Purchase"
        let id = "purchase:" + slug(name)
        guard let e = Evidence(signal: "ocr_text", tier: .text, weight: 0.75,
                               reason: "a receipt or order in your library names \(name.lowercased())"),
              let entity = Entity(entityID: id, kind: .purchase, name: name, evidence: [e])
        else { return }
        graph.add(entity)
        graph.observe(Observation(
            entityID: id, assetID: asset.assetID, when: asset.createdAt,
            place: placeName, confidence: 0.75,
            reason: "this receipt or order is for \(name.lowercased())",
            placeSource: placeSource))
    }

    /// A receipt reads `RECEIPT — HEADPHONES £129.00`. The part after the dash is the
    /// item; the amount is not. A candidate is accepted only when it reads like a name,
    /// so an order and a receipt for the same thing land on the same entity — one
    /// purchase, two documents.
    static func purchaseItem(_ text: String) -> String? {
        for separator in ["—", "–", " - ", ":"] {
            guard let range = text.range(of: separator) else { continue }
            var candidate = String(text[range.upperBound...])
            for currency in ["£", "$", "€", "¥"] {
                if let cut = candidate.range(of: currency) {
                    candidate = String(candidate[..<cut.lowerBound])
                }
            }
            candidate = candidate.trimmingCharacters(in: CharacterSet(charactersIn: " .,\t\n"))
            let letters = candidate.filter { $0.isLetter }.count
            guard letters >= 3, candidate.count > 2, candidate.count <= 40,
                  Double(letters) / Double(candidate.count) >= 0.7 else { continue }
            return candidate.capitalized
        }
        return nil
    }

    // MARK: events

    /// §11: 时间 + 地点 + 人物 + 内容 can form Event / Trip candidates, and the user
    /// should never have to build a travel album by hand.
    private static func events(_ context: LibraryContext, _ byID: [String: AssetSignals],
                               _ graph: inout MemoryGraph) {
        for trip in context.trips {
            let id = "event:" + slug(trip.label)
            let days = max(1, Int(trip.end.timeIntervalSince(trip.start) / 86400) + 1)
            guard let e = Evidence(signal: "geo+created_at", tier: .metadata, weight: 0.8,
                                   reason: "\(trip.assetCount) photos over \(days) days away from home"),
                  let entity = Entity(entityID: id, kind: .event, name: trip.label, evidence: [e])
            else { continue }
            graph.add(entity)
            for asset in byID.values.sorted(by: { $0.assetID < $1.assetID }) {
                guard let when = asset.createdAt, trip.contains(when) else { continue }
                graph.observe(Observation(
                    entityID: id, assetID: asset.assetID, when: when,
                    place: trip.city ?? trip.country, confidence: 0.8,
                    reason: "taken during \(trip.label)"))
            }
        }
    }

    /// Mark the sightings that add no new information, without discarding any.
    ///
    /// §9 Same Entity tells the *catalogue* that several assets show one real thing, so
    /// it must relate them and delete none. It does not tell the *memory* that they are
    /// one sighting — and for a memory that difference is the whole point. Two photos
    /// of Anna eight days apart are two facts about where Anna was; collapsing them
    /// deletes the only thing the graph exists to keep. So what is marked here is
    /// narrower: members of the same *moment*, which genuinely say one thing twice.
    /// They stay stored and queryable, and `lastSeen` reads time, not this flag.
    private static func markRepeats(_ groups: [[String]], _ byID: [String: AssetSignals],
                                    _ graph: inout MemoryGraph) {
        for group in groups {
            let members = group.filter { byID[$0] != nil }
            guard members.count >= 2 else { continue }
            let anchor = members.min {
                (byID[$0]!.createdAt ?? .distantFuture) < (byID[$1]!.createdAt ?? .distantFuture)
            }!
            let repeated = Set(members).subtracting([anchor])
            graph.flagRepeats(of: repeated, anchor: anchor)
        }
    }

    // MARK: naming

    static func slug(_ text: String) -> String {
        // Built by appending Strings rather than Characters: `Character.lowercased()`
        // returns a String, and for a handful of scripts that String is two characters
        // long — `Character(_:)` traps on those. An entity id is not worth a crash.
        var out = ""
        for character in text {
            out += (character.isLetter || character.isNumber)
                ? String(character).lowercased() : "-"
        }
        return out.trimmingCharacters(in: CharacterSet(charactersIn: "-"))
    }

    /// The last component of a taxonomy path. Returns the whole string when there is
    /// no separator, and never force-unwraps a split.
    static func leaf(of path: String) -> String {
        guard let last = path.split(separator: ">").last else { return path }
        return String(last).trimmingCharacters(in: .whitespaces)
    }

    /// `Passports` -> `Passport`. The shelf is plural because it holds many; the thing
    /// one photo shows is one.
    static func singular(_ leaf: String) -> String {
        if leaf.hasSuffix("ies"), leaf.count > 4 { return String(leaf.dropLast(3)) + "y" }
        if leaf.hasSuffix("s"), !leaf.hasSuffix("ss"), !leaf.hasSuffix("us") {
            return String(leaf.dropLast())
        }
        return leaf
    }

    /// `t_shirt` -> `T Shirt`. The recogniser's identifier, in the user's alphabet.
    static func pretty(_ identifier: String) -> String {
        identifier.replacingOccurrences(of: "_", with: " ")
            .split(separator: " ")
            .map { $0.prefix(1).uppercased() + $0.dropFirst().lowercased() }
            .joined(separator: " ")
    }
}

extension MemoryGraph {
    /// Kept on the graph rather than on the builder because `observations` is
    /// `private(set)`: the only way to change a stored sighting is through a method
    /// that says what it is doing.
    mutating func flagRepeats(of assetIDs: Set<String>, anchor: String) {
        for i in observations.indices where assetIDs.contains(observations[i].assetID) {
            observations[i].repeatsAsset = anchor
        }
    }
}

// MARK: - Video (L1-B §4)

/// `mm:ss`, with a decimal when the span is short enough that whole seconds would hide
/// it.
///
/// A cut lasting two thirds of a second is a real span in the data and rendered
/// `00:10–00:10` on screen, which reads as nothing at all. Losing a distinction in the
/// formatter after taking the trouble to keep it in the record is the same failure one
/// layer out.
public func formatSpan(_ start: Double, _ end: Double) -> String {
    let decimals = (end - start) < 10 ? 1 : 0

    func clock(_ seconds: Double) -> String {
        // Rounded first, then split. Splitting first prints 59.967 as "00:60.0",
        // because the carry happens after the minute is already fixed.
        let scale = pow(10.0, Double(decimals))
        let value = (seconds * scale).rounded() / scale
        let minutes = Int(value / 60)
        let rest = value - Double(minutes) * 60
        let width = decimals == 0 ? 2 : 2 + 1 + decimals
        return String(format: "%02d:%0\(width).\(decimals)f", minutes, rest)
    }

    return "\(clock(start))–\(clock(end))"
}

/// What a video must leave behind is a record, not a pile of frames: the shape L1-B §4
/// specifies, verbatim — Date / Place / Person / Object / Event / relevant segment /
/// representative frames.
public struct VideoMemoryRecord {
    public let assetID: String
    public let date: Date?
    public let place: String?
    public let people: [String]
    public let objects: [String]
    public let event: String?
    public let segments: [ClosedRange<Double>]
    public let representativeFrames: [Int]
    public let evidence: [Evidence]

    public var summary: String {
        var parts: [String] = []
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_GB")
        formatter.timeZone = TimeZone(identifier: "UTC")
        formatter.dateFormat = "yyyy-MM-dd"
        if let date { parts.append("Date: " + formatter.string(from: date)) }
        if let place { parts.append("Place: \(place)") }
        if !people.isEmpty { parts.append("Person: " + people.joined(separator: ", ")) }
        if !objects.isEmpty { parts.append("Object: " + objects.joined(separator: ", ")) }
        if let event { parts.append("Event: \(event)") }
        if !segments.isEmpty {
            parts.append("Relevant segment: " + segments.map { clock($0) }.joined(separator: ", "))
        }
        parts.append("Representative frames: \(representativeFrames.count)")
        return parts.joined(separator: "\n")
    }

    private func clock(_ range: ClosedRange<Double>) -> String {
        formatSpan(range.lowerBound, range.upperBound)
    }
}

public enum VideoMemory {

    /// A segment runs from the change that started it to the change that ended it.
    static func segmentsByContent(_ frames: [Int], _ newContent: Set<Int>,
                                  _ frameRate: Double) -> [ClosedRange<Double>] {
        guard !frames.isEmpty, frameRate > 0 else { return [] }
        var out: [ClosedRange<Double>] = []
        var start = frames[0]
        for index in frames.dropFirst() where newContent.contains(index) {
            out.append((Double(start) / frameRate)...(Double(index) / frameRate))
            start = index
        }
        out.append((Double(start) / frameRate)...(Double(frames[frames.count - 1]) / frameRate))
        // A trailing segment that opened on the final frame has nothing after it to
        // close against. It is a moment, not a span, and is dropped rather than shown
        // as a zero-length segment the user would have to interpret.
        let spans = out.filter { $0.upperBound > $0.lowerBound }
        if !spans.isEmpty { return spans }
        return frames.count < 2 ? [] : Array(out.prefix(1))
    }

    /// For callers holding bare indices with no record of why each was taken: a run of
    /// consecutive frames is one segment. Correct for that input and no more — the
    /// gate's own output should go through `segmentsByContent`.
    static func segmentsByAdjacency(_ frames: [Int],
                                    _ frameRate: Double) -> [ClosedRange<Double>] {
        guard !frames.isEmpty, frameRate > 0 else { return [] }
        var out: [ClosedRange<Double>] = []
        var start = frames[0]
        var previous = frames[0]
        for index in frames.dropFirst() {
            if index - previous > 1 {
                out.append((Double(start) / frameRate)...(Double(previous) / frameRate))
                start = index
            }
            previous = index
        }
        out.append((Double(start) / frameRate)...(Double(max(previous, start)) / frameRate))
        return out
    }

    /// Build the record from the frames the delta gate already chose.
    ///
    /// The segments are the runs of consecutive keyframes: a keyframe opens a segment
    /// and the next one closes it, so what is stored is *when something was happening*
    /// rather than a list of timestamps. That is the difference between a record and an
    /// index of frames.
    /// Build the record from the frames the delta gate already chose.
    ///
    /// `newContentAt` is the set of keyframes taken because something *changed* — a
    /// cut, a drift, the first frame. The gate also takes a keyframe every thirty
    /// frames in a completely static shot, as a periodic re-check, and those two kinds
    /// mean opposite things here. Without the distinction a sixty-second video came
    /// back as sixty-one zero-length "segments" — a list of instants, which is exactly
    /// the pile of frames L1-B §4 says a video must not leave behind.
    ///
    /// So a segment opens on new content and is *extended*, not ended, by a heartbeat
    /// sample. What gets stored is when something was happening.
    public static func record(asset: AssetSignals, keyframes: [Int], frameRate: Double,
                              classification: Classification? = nil,
                              context: LibraryContext? = nil,
                              newContentAt: Set<Int>? = nil) -> VideoMemoryRecord {
        let frames = Array(Set(keyframes)).sorted()
        let segments = newContentAt.map { segmentsByContent(frames, $0, frameRate) }
            ?? segmentsByAdjacency(frames, frameRate)

        var place: String?
        if let p = asset.place { place = p.city ?? p.country }
        var event: String?
        if let context, let trip = context.trip(for: asset.createdAt, geo: asset.geo) {
            event = trip.label
        }

        var objects: [String] = []
        if let classification {
            for path in classification.paths {
                let root = TaxonomyRuntime.root(of: path)
                if root == "Objects" || root == "Clothing" {
                    objects.append(MemoryBuilder.leaf(of: path))
                }
            }
        }

        let evidence = Evidence(
            signal: "deltas", tier: .hash, weight: 0.7,
            reason: "\(frames.count) frames carried new information; the rest repeated them")

        return VideoMemoryRecord(
            assetID: asset.assetID, date: asset.createdAt, place: place,
            people: asset.namedPeople, objects: Array(Set(objects)).sorted(),
            event: event, segments: segments, representativeFrames: frames,
            evidence: evidence.map { [$0] } ?? [])
    }
}
