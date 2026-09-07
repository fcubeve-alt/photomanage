import Foundation

/// INTENT SEARCH — §10's third retrieval path.
///
///     Intent Search：用户直接说“找我的身份证正反面”“找所有有气球的照片”。   — L1 §10
///
/// Those two examples are not the same problem, and the difference is the whole design.
///
/// The first the library can answer completely: a taxonomy node it has, plus an aspect
/// (两面) the entity resolver already models as one document with more than one side.
///
/// The second it cannot. 气球 is not a label anything in this build produces, and there
/// is no open-vocabulary visual index. Pretending otherwise is the failure this file
/// exists to avoid: **a search that silently returns everything, or silently returns
/// nothing, turns a missing capability into a false statement about the user's photos.**
/// "You have no photos of balloons" and "I cannot search for balloons" are different
/// statements and only one of them is true.
///
/// Mirrors `30_ENGINE/pvm/intent.py`. The vocabulary itself is generated into
/// `Rules.generated.swift` from the engine, because a search that recognises 身份证 on
/// one side and not the other is two products.

public struct SearchQuery {
    public let text: String
    public var paths: [String] = []
    public var people: [String] = []
    public var places: [String] = []
    public var entities: [String] = []
    public var mediaType: String?
    public var year: Int?
    public var month: Int?
    public var wantsMultipleSides = false
    /// Words that name nothing this library indexes. The most important field here.
    public var unresolved: [String] = []
    /// One line per resolved term, in the user's words.
    public var understood: [String] = []

    public var isEmpty: Bool {
        paths.isEmpty && people.isEmpty && places.isEmpty && entities.isEmpty
            && mediaType == nil && year == nil && month == nil
    }

    /// Whether anything here actually restricts the library.
    ///
    /// A media type alone does not. 找所有有气球的照片 resolves 照片 to *images* and
    /// nothing else, and running that returns every photograph the user owns —
    /// presented as the answer to a question about balloons. Fifty results is a worse
    /// lie than zero.
    public var narrows: Bool {
        !(paths.isEmpty && people.isEmpty && places.isEmpty && entities.isEmpty)
            || year != nil || month != nil
    }

    public var answerable: Bool { narrows || unresolved.isEmpty }

    public func explain() -> String {
        if !unresolved.isEmpty && !narrows {
            let words = unresolved.map { "“\($0)”" }.joined(separator: ", ")
            return "I cannot search for \(words) — nothing in this library is indexed by "
                 + "that. Showing you everything instead would look like an answer, so I "
                 + "have not. This is a limit of the search, not a statement about your "
                 + "photos."
        }
        var parts: [String] = []
        if !understood.isEmpty {
            parts.append("I looked for " + understood.joined(separator: "; ") + ".")
        }
        if !unresolved.isEmpty {
            let words = unresolved.map { "“\($0)”" }.joined(separator: ", ")
            parts.append("I do not know how to search for \(words) — nothing in this "
                       + "library is indexed by that, so it was not used to narrow the "
                       + "results. That is a limit of the search, not a statement about "
                       + "your photos.")
        }
        if parts.isEmpty {
            parts.append("I could not turn that into anything this library indexes.")
        }
        return parts.joined(separator: " ")
    }
}

public struct SearchHit {
    public let assetID: String
    public let path: String
    public let why: String
}

public struct SearchResults {
    public let query: SearchQuery
    public var hits: [SearchHit] = []
    /// Assets the query matched that also have a sibling showing another side or page.
    public var sides: [[String]] = []

    public var summary: String {
        if query.isEmpty || !query.answerable { return query.explain() }
        let head = hits.isEmpty
            ? "Nothing in the library matches that"
            : "\(hits.count) match\(hits.count == 1 ? "" : "es")"
        return "\(head). \(query.explain())"
    }
}

public enum Intent {

    private static let months: [String: Int] = [
        "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
        "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
        "december": 12,
        "一月": 1, "二月": 2, "三月": 3, "四月": 4, "五月": 5, "六月": 6,
        "七月": 7, "八月": 8, "九月": 9, "十月": 10, "十一月": 11, "十二月": 12,
    ]

    /// Resolve a sentence against what this library actually contains.
    ///
    /// The known names come from the catalogue rather than from a list in this file: a
    /// search that only recognises names someone wrote down in advance is not searching
    /// the user's library.
    public static func parse(_ text: String, knownPeople: [String] = [],
                             knownPlaces: [String] = [],
                             knownEntities: [String] = []) -> SearchQuery {
        var q = SearchQuery(text: text)
        let lowered = text.lowercased()
        var consumed: [String] = []

        // Longest phrases first, so "id card" wins over "card".
        for phrase in Rules.categoryWords.keys.sorted(by: { $0.count > $1.count })
        where lowered.contains(phrase) {
            let path = Rules.categoryWords[phrase]!
            if !q.paths.contains(path) {
                q.paths.append(path)
                q.understood.append("\(path) (from “\(phrase)”)")
            }
            consumed.append(phrase)
        }

        for phrase in Rules.multiSideWords where lowered.contains(phrase) {
            q.wantsMultipleSides = true
            q.understood.append("documents with more than one side or page")
            consumed.append(phrase)
            break
        }

        for (phrase, kind) in Rules.mediaWords.sorted(by: { $0.key.count > $1.key.count })
        where lowered.contains(phrase) {
            q.mediaType = kind
            q.understood.append("\(kind)s only")
            consumed.append(phrase)
            break
        }

        for name in knownPeople where lowered.contains(name.lowercased()) {
            q.people.append(name)
            q.understood.append("photos of \(name)")
            consumed.append(name.lowercased())
        }
        for name in knownPlaces where lowered.contains(name.lowercased()) {
            q.places.append(name)
            q.understood.append("in \(name)")
            consumed.append(name.lowercased())
        }
        for name in knownEntities
        where lowered.contains(name.lowercased())
            && !q.people.contains(name) && !q.places.contains(name) {
            q.entities.append(name)
            q.understood.append("the \(name.lowercased()) it remembers")
            consumed.append(name.lowercased())
        }

        // ---- time. Exact windows only; anything vaguer is left unresolved rather
        // than guessed at, because a window the user did not choose is a wrong answer
        // that looks like a right one.
        if let range = lowered.range(of: "(19|20)\\d{2}", options: .regularExpression),
           let year = Int(lowered[range]) {
            q.year = year
            q.understood.append("taken in \(year)")
            consumed.append(String(lowered[range]))
        }
        for (word, number) in months where lowered.contains(word) {
            q.month = number
            q.understood.append("in month \(number)")
            consumed.append(word)
            break
        }
        let thisYear = Calendar(identifier: .gregorian).component(.year, from: Date())
        if text.contains("今年") || lowered.contains("this year") {
            if q.year == nil { q.year = thisYear; q.understood.append("taken in \(thisYear)") }
            consumed.append("今年"); consumed.append("this year")
        } else if text.contains("去年") || lowered.contains("last year") {
            if q.year == nil { q.year = thisYear - 1; q.understood.append("taken in \(thisYear - 1)") }
            consumed.append("去年"); consumed.append("last year")
        }

        // ---- what is left over, computed by subtraction from the sentence.
        //
        // Not by tokenising it: Chinese runs together, so a matched sub-phrase used to
        // swallow the whole run — 找所有有气球的照片 resolved 照片 and then reported
        // nothing unresolved, which is how a query about balloons came back as the
        // entire library with no warning at all.
        var residue = lowered
        for phrase in consumed.sorted(by: { $0.count > $1.count }) {
            residue = residue.replacingOccurrences(of: phrase, with: " ")
        }
        for phrase in Rules.searchFillerCJK {
            residue = residue.replacingOccurrences(of: phrase, with: " ")
        }

        let filler = Set(Rules.searchFiller)
        for token in matches(in: residue, pattern: "[a-z0-9']+") {
            // A one-letter leftover is punctuation from subtraction, not a search term:
            // consuming "receipt" out of "receipts" leaves an "s".
            if filler.contains(token) || token.count < 2 { continue }
            if let path = Rules.sceneMap[token] {
                if !q.paths.contains(path) {
                    q.paths.append(path)
                    q.understood.append("\(path) (from “\(token)”)")
                }
                continue
            }
            if !q.unresolved.contains(token) { q.unresolved.append(token) }
        }
        for token in matches(in: residue, pattern: "[\\u4e00-\\u9fff]+") {
            if filler.contains(token) { continue }
            if let path = Rules.sceneMap[token] {
                if !q.paths.contains(path) { q.paths.append(path) }
                continue
            }
            if !q.unresolved.contains(token) { q.unresolved.append(token) }
        }
        return q
    }

    private static func matches(in text: String, pattern: String) -> [String] {
        guard let re = try? NSRegularExpression(pattern: pattern) else { return [] }
        let ns = text as NSString
        return re.matches(in: text, range: NSRange(location: 0, length: ns.length))
            .map { ns.substring(with: $0.range) }
    }

    /// Answer a sentence against the catalogue. No new signal is computed to serve a
    /// search — Gate 1's constraint as much as Gate 3's.
    public static func search(_ catalog: Catalog, _ text: String,
                              limit: Int = 50) -> SearchResults {
        let people = catalog.entities(kind: "person", limit: 500).map { $0.name }
        let places = catalog.entities(kind: "place", limit: 500).map { $0.name }
        let others = catalog.entities(limit: 1000).map { $0.name }
        let q = parse(text, knownPeople: people, knownPlaces: places, knownEntities: others)
        var results = SearchResults(query: q)
        guard !q.isEmpty, q.answerable else { return results }

        var range: (Double, Double)?
        if let year = q.year { range = yearBounds(year, q.month) }

        let rows = catalog.search(
            paths: q.paths,
            entityNameGroups: [q.people, q.places, q.entities],
            mediaType: q.mediaType, yearRange: range, limit: limit)
        results.hits = rows.map {
            SearchHit(assetID: $0.assetID,
                      path: $0.paths.components(separatedBy: " | ").first ?? "",
                      why: "filed under \($0.paths)")
        }
        if q.wantsMultipleSides {
            results.sides = catalog.sameEntityGroups(containing: results.hits.map { $0.assetID })
        }
        return results
    }

    static func yearBounds(_ year: Int, _ month: Int?) -> (Double, Double) {
        var calendar = Calendar(identifier: .gregorian)
        calendar.timeZone = TimeZone(identifier: "UTC")!
        func date(_ y: Int, _ m: Int) -> Date {
            calendar.date(from: DateComponents(year: y, month: m, day: 1))!
        }
        if let month {
            let end = month == 12 ? date(year + 1, 1) : date(year, month + 1)
            return (date(year, month).timeIntervalSince1970, end.timeIntervalSince1970)
        }
        return (date(year, 1).timeIntervalSince1970, date(year + 1, 1).timeIntervalSince1970)
    }
}
