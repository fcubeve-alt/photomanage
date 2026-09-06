import Foundation

/// CATEGORY-SPECIFIC ENTITY RESOLVER — §24 Gate 2, and Tier 1-B.
///
/// The Constitution is unusually blunt here:
///
///     禁止寻找一个万能 Same-Entity 模型。采用 Category-Specific Entity Resolver：
///     证件用 OCR/版式/字段，合同用文本指纹/页码，普通照片用时间/地点/视觉相似，
///     人物与物品使用适合其类别的组合信号。            — L1 §24, Gate 2
///
/// So there is no `sameEntity(a, b)` here. There is a dispatch on what the two assets
/// *are*, and a different resolver behind each branch, because "are these the same
/// thing" means something different for an ID card than for a chair.
///
/// `Dedup` answers the narrower question — do these look alike, were they taken in one
/// moment. That is Layer 1 in §25 terms. This is Layer 4.
///
/// Mirrors `30_ENGINE/pvm/resolver.py`. Two rules run through every branch:
///
/// * **A document is never merged on appearance.** Tier 1-B's PASS criterion is that
///   Document False Merge stays extremely low — 错误合并证件/合同的代价远高于漏检.
///   Documents merge on *fields*: a shared reference, a shared holder. Looking
///   identical buys UNCERTAIN at most.
/// * **低置信度只能进入 Review Queue，不自动合并/删除.** `.uncertain` is a verdict,
///   not a rounded-down `.same`. It is review burden (§18), a cost to report rather
///   than an error to hide by guessing.

public enum EntityVerdict: String {
    case same, different, uncertain
}

public enum EntityRelation: String {
    /// The same real thing, photographed again in one moment.
    case sameInstance
    /// One document, two pages. Same entity; both assets must survive.
    case otherPage
    /// One thing on two occasions — a version, not a duplicate. §9: both survive.
    case otherVersion
    case distinct
    case unknown
}

public struct Resolution {
    public let verdict: EntityVerdict
    public let relation: EntityRelation
    public let confidence: Double
    public let resolver: String
    public let evidence: [Evidence]

    /// Fails on empty evidence, like `Assignment` and `Entity`. A merge nobody can
    /// justify is the failure Gate 2 is about.
    public init?(_ verdict: EntityVerdict, _ relation: EntityRelation,
                 _ confidence: Double, _ resolver: String, _ evidence: [Evidence]) {
        guard !evidence.isEmpty else { return nil }
        self.verdict = verdict
        self.relation = relation
        self.confidence = confidence
        self.resolver = resolver
        self.evidence = evidence
    }

    /// The only gate a caller should consult before joining two assets.
    public var mayMerge: Bool { verdict == .same && relation != .distinct }
    public var needsReview: Bool { verdict == .uncertain }

    public var why: String {
        evidence.sorted { $0.weight > $1.weight }.map { $0.reason }.joined(separator: "; ")
    }
}

public enum EntityResolver {

    // MARK: - Thresholds. Each is a policy choice, so each says what it trades.

    /// Above this, two texts are the same text captured twice.
    public static let sameText = 0.80
    /// Below this, two documents of one type are different documents. Between them the
    /// answer is uncertain, and the user decides.
    public static let differentText = 0.35
    public static let sameViewBits = 6
    public static let differentViewBits = 16
    /// Two captures further apart than this are two occasions, whatever they show.
    public static let sameOccasionHours = 12.0

    // MARK: - Field extraction

    /// Labelled identifiers. Three rules, each of which the first version got wrong and
    /// the evaluation caught within a minute:
    ///
    /// 1. The label needs an explicit `no` / `number` / `#` / `:` after it, or
    ///    `PASSPORT UNITED KINGDOM` yields the identifier "UNITED".
    /// 2. `no` must end on a word boundary, or `RECEIPT NORTHSIDE COFFEE` yields
    ///    "RTHSIDE".
    /// 3. The token must contain a digit. Identifiers do; English words do not, and
    ///    this one rule kills "UNITED", "ENTITY", "CONFIRMED" and "NORTHSIDE" at once.
    ///
    /// A wrong identifier is worse than none: none ends at uncertain, wrong ends at
    /// same — a false merge on the category Tier 1-B fails on.
    private static let idPattern: NSRegularExpression = {
        let label = "passport|identity\\s*card|id\\s*card|driving\\s*licen[cs]e|order|"
                  + "invoice|receipt|policy|contract|agreement|tracking|reference|ref|"
                  + "customer|account"
        let separator = "(?:(?:no|number|nr|num|id|号)\\b\\.?\\s*[:.#]?|[:#])"
        return try! NSRegularExpression(
            pattern: "\\b(?:\(label))\\b\\s*\(separator)\\s*([A-Z0-9][A-Z0-9/\\-]{3,23})\\b",
            options: [.caseInsensitive])
    }()

    private static let pagePattern = try! NSRegularExpression(
        pattern: "\\bpage\\s*(\\d{1,3})\\s*(?:of|/)?\\s*(\\d{1,3})?\\b",
        options: [.caseInsensitive])

    private static let pageCNPattern = try! NSRegularExpression(
        pattern: "第\\s*(\\d{1,3})\\s*页\\s*(?:共\\s*(\\d{1,3})\\s*页)?")

    /// Label case-insensitive, value not: a holder's name on an identity document is
    /// set in capitals, and requiring that is most of what stops this matching prose.
    /// Bounded to two words — unbounded, `NAME: JANE DOE DATE OF BIRTH` became the
    /// holder, and a holder that swallows the page compares unequal for reasons that
    /// have nothing to do with who holds it.
    private static let namePattern = try! NSRegularExpression(
        pattern: "\\b(?i:name|surname|holder|姓名)\\s*[:/]?\\s*([A-Z]{2,20}(?:[ '\\-][A-Z]{2,20})?)\\b")

    private static let stopwords: Set<String> = [
        "the", "and", "for", "with", "this", "that", "page", "of", "no", "number",
        "date", "total", "amount", "card", "id", "order", "receipt", "invoice",
    ]

    public static func identifiers(in text: String) -> Set<String> {
        var out: Set<String> = []
        let ns = text as NSString
        for m in idPattern.matches(in: text, range: NSRange(location: 0, length: ns.length)) {
            guard m.numberOfRanges > 1, m.range(at: 1).location != NSNotFound else { continue }
            let raw = ns.substring(with: m.range(at: 1)).uppercased()
            let token = raw.filter { $0.isLetter || $0.isNumber }
            if token.count >= 4, token.contains(where: { $0.isNumber }) {
                out.insert(String(token))
            }
        }
        return out
    }

    public static func page(in text: String) -> (page: Int, total: Int?)? {
        let ns = text as NSString
        for pattern in [pagePattern, pageCNPattern] {
            guard let m = pattern.firstMatch(
                in: text, range: NSRange(location: 0, length: ns.length)) else { continue }
            guard let number = Int(ns.substring(with: m.range(at: 1))) else { continue }
            var total: Int?
            if m.numberOfRanges > 2, m.range(at: 2).location != NSNotFound {
                total = Int(ns.substring(with: m.range(at: 2)))
            }
            return (number, total)
        }
        return nil
    }

    public static func holderNames(in text: String) -> Set<String> {
        var out: Set<String> = []
        let ns = text as NSString
        for m in namePattern.matches(in: text, range: NSRange(location: 0, length: ns.length))
        where m.range(at: 1).location != NSNotFound {
            out.insert(ns.substring(with: m.range(at: 1))
                .trimmingCharacters(in: .whitespaces).uppercased())
        }
        return out
    }

    /// Word trigrams minus stopwords — the 文本指纹 Gate 2 asks for on contracts.
    /// Trigrams rather than a bag of words because contract boilerplate shares almost
    /// every individual word with every other contract; what distinguishes two is which
    /// words sit next to which.
    static func shingles(_ text: String, n: Int = 3) -> Set<String> {
        let words = text.lowercased()
            .split(whereSeparator: { !($0.isLetter || $0.isNumber) })
            .map(String.init)
            .filter { !stopwords.contains($0) }
        if words.isEmpty { return [] }
        if words.count < n { return [words.joined(separator: " ")] }
        var out: Set<String> = []
        for i in 0...(words.count - n) {
            out.insert(words[i..<(i + n)].joined(separator: " "))
        }
        return out
    }

    /// Jaccard over trigrams. 0 when either side has no usable text — which is a *lack
    /// of evidence*, and callers must not read it as evidence of difference.
    public static func textSimilarity(_ a: String, _ b: String) -> Double {
        let sa = shingles(a), sb = shingles(b)
        if sa.isEmpty || sb.isEmpty { return 0 }
        return Double(sa.intersection(sb).count) / Double(sa.union(sb).count)
    }

    // MARK: - Dispatch

    private static func gapHours(_ a: AssetSignals, _ b: AssetSignals) -> Double? {
        guard let x = a.createdAt, let y = b.createdAt else { return nil }
        return abs(x.timeIntervalSince(y)) / 3600
    }

    /// One thing in one moment is an instance; one thing on two occasions is a version.
    /// The difference decides whether a caller may fold the two, so it is not cosmetic:
    /// two photographs of one ID card six months apart are the same card and two
    /// separate records of it — §9's case, and a deletion the user would not forgive.
    private static func instanceOrVersion(_ a: AssetSignals, _ b: AssetSignals) -> EntityRelation {
        guard let gap = gapHours(a, b), gap <= sameOccasionHours else { return .otherVersion }
        return .sameInstance
    }

    /// FC-1a: dHash returns 0 both for a class of flat images and for every failure, so
    /// a 0 that came from a failure is indistinguishable from a perfect match.
    private static func visualDistance(_ a: AssetSignals, _ b: AssetSignals) -> Int? {
        guard a.hasUsableDHash, b.hasUsableDHash,
              let x = a.dhash, let y = b.dhash else { return nil }
        return hamming(x, y)
    }

    /// Which resolver these assets belong to — the dispatch key of the whole file.
    static func category(_ c: Classification?) -> String {
        guard let c else { return "photo" }
        let roots = Set(c.paths.map { TaxonomyRuntime.root(of: $0) })
        // Order matters: a receipt is cross-listed into Documents *and* Purchases, and
        // the document resolver is the stricter of the two. Strictest wins.
        if roots.contains("Documents") { return "document" }
        if roots.contains("Screenshots") || roots.contains("Purchases") { return "screenshot" }
        if roots.contains("Objects") || roots.contains("Clothing") { return "object" }
        if roots.contains("People") { return "person" }
        return "photo"
    }

    public static func resolve(_ a: AssetSignals, _ b: AssetSignals,
                               _ ca: Classification? = nil,
                               _ cb: Classification? = nil) -> Resolution {
        if a.assetID == b.assetID {
            return make(.same, .sameInstance, 1.0, "identity", [
                ev("asset_id", .metadata, 0.99, "the same asset compared with itself")])
        }

        // Byte identity settles it before any category question, and before any
        // confidence gate: two identical files are the same file whatever either was
        // classified as.
        if let h = a.contentHash, h == b.contentHash {
            return make(.same, .sameInstance, 0.99, "bytes", [
                ev("content_hash", .hash, 0.99,
                   "these two files are byte-for-byte identical")])
        }

        let ka = category(ca), kb = category(cb)
        if ka != kb {
            return make(.different, .distinct, 0.8, "category", [
                ev("taxonomy", .metadata, 0.8,
                   "one is filed as \(ka), the other as \(kb) — different kinds of thing")])
        }

        switch ka {
        case "document":   return resolveDocument(a, b)
        case "screenshot": return resolveScreenshot(a, b)
        case "object":     return resolveObject(a, b)
        default:           return resolvePhoto(a, b)
        }
    }

    // MARK: - Documents — 证件用 OCR/版式/字段，合同用文本指纹/页码

    /// The order of these checks is the design, and the evaluation set it. Page 1 of two
    /// different contracts on one template shares its page number, its page count and
    /// three paragraphs of boilerplate — every similarity signal says same — and the
    /// only thing separating them is the contract number. So that check runs first.
    private static func resolveDocument(_ a: AssetSignals, _ b: AssetSignals) -> Resolution {
        let ta = a.ocrText.trimmingCharacters(in: .whitespacesAndNewlines)
        let tb = b.ocrText.trimmingCharacters(in: .whitespacesAndNewlines)
        let ida = identifiers(in: ta), idb = identifiers(in: tb)
        let pa = page(in: ta), pb = page(in: tb)
        let similarity = textSimilarity(ta, tb)

        // 1. Disagreeing references separate, whatever else agrees.
        if !ida.isEmpty, !idb.isEmpty, ida.isDisjoint(with: idb) {
            return make(.different, .distinct, 0.93, "document.identifier", [
                ev("ocr_text", .text, 0.93,
                   "each carries a reference number and they do not match — "
                   + "these are two different documents")])
        }

        // 2. Different holders separate. Compared by token overlap, because OCR gives
        //    the name with a variable amount of the page attached.
        let na = Set(holderNames(in: ta).flatMap { $0.split(separator: " ").map(String.init) })
        let nb = Set(holderNames(in: tb).flatMap { $0.split(separator: " ").map(String.init) })
        if !na.isEmpty, !nb.isEmpty, na.isDisjoint(with: nb) {
            return make(.different, .distinct, 0.9, "document.holder", [
                ev("ocr_text", .text, 0.9,
                   "these are made out to different people "
                   + "(\(na.sorted()[0]) and \(nb.sorted()[0]))")])
        }

        // 3. Pages of one document — checked before the identifier merge so page 1 and
        //    page 2 of contract AB-4417 are two pages, not two versions. The relation is
        //    what tells a view that both must be shown.
        if let pa, let pb, let total = pa.total, total == pb.total, pa.page != pb.page {
            return make(.same, .otherPage, 0.85, "document.page", [
                ev("ocr_text", .text, 0.85,
                   "page \(pa.page) and page \(pb.page) of the same \(total)-page "
                   + "document — related, and both kept")])
        }

        // 4. Agreeing references merge.
        if !ida.isEmpty, !idb.isEmpty {
            let shared = ida.intersection(idb).sorted()
            return make(.same, instanceOrVersion(a, b), 0.95, "document.identifier", [
                ev("ocr_text", .text, 0.95,
                   "both carry the same reference \(shared.first ?? "")")])
        }

        // 5. Text fingerprint, as far as it honestly reaches — and no further. Without
        //    a reference or a holder, appearance never merges a document.
        if ta.isEmpty || tb.isEmpty {
            return make(.uncertain, .unknown, 0.3, "document.text", [
                ev("ocr_text", .text, 0.3,
                   "there is not enough text on one of these to tell whether they are "
                   + "the same document")])
        }
        if similarity >= sameText {
            return make(.same, instanceOrVersion(a, b), 0.82, "document.text", [
                ev("ocr_text", .text, 0.82,
                   "the text on these two is the same text, word for word")])
        }
        if similarity <= differentText {
            return make(.different, .distinct, 0.85, "document.text", [
                ev("ocr_text", .text, 0.85,
                   "these two pages read differently — kept as separate documents")])
        }
        return make(.uncertain, .unknown, 0.5, "document.text", [
            ev("ocr_text", .text, 0.5,
               "these two documents are similar but not the same; only you can say "
               + "whether they are one thing")])
    }

    // MARK: - Screenshots — 同一订单/票务/报错/商品页面的不同截图/版本

    private static func resolveScreenshot(_ a: AssetSignals, _ b: AssetSignals) -> Resolution {
        let ta = a.ocrText.trimmingCharacters(in: .whitespacesAndNewlines)
        let tb = b.ocrText.trimmingCharacters(in: .whitespacesAndNewlines)
        let ida = identifiers(in: ta), idb = identifiers(in: tb)

        if !ida.isEmpty, !idb.isEmpty {
            let shared = ida.intersection(idb).sorted()
            if !shared.isEmpty {
                // An order confirmation, a dispatch mail and a delivery photo are one
                // purchase seen three times. §15 Purchase Memory depends on this join.
                return make(.same, .otherVersion, 0.92, "screenshot.reference", [
                    ev("ocr_text", .text, 0.92,
                       "both screens show reference \(shared[0]) — the same order, "
                       + "captured at different stages")])
            }
            return make(.different, .distinct, 0.9, "screenshot.reference", [
                ev("ocr_text", .text, 0.9,
                   "these screens show different order references")])
        }

        let similarity = textSimilarity(ta, tb)
        let distance = visualDistance(a, b)
        if similarity >= sameText, let distance, distance <= sameViewBits {
            return make(.same, .otherVersion, 0.78, "screenshot.text", [
                ev("ocr_text", .text, 0.7, "the same screen, captured twice"),
                ev("dhash", .hash, 0.6, "and the two look the same")])
        }
        if similarity <= differentText, !ta.isEmpty, !tb.isEmpty {
            return make(.different, .distinct, 0.8, "screenshot.text", [
                ev("ocr_text", .text, 0.8, "these screens show different things")])
        }
        return make(.uncertain, .unknown, 0.45, "screenshot.text", [
            ev("ocr_text", .text, 0.45,
               "these look like the same app but there is nothing on them that says "
               + "they are the same thing")])
    }

    // MARK: - Objects — 视觉 embedding + attribute + temporal evidence

    private static func resolveObject(_ a: AssetSignals, _ b: AssetSignals) -> Resolution {
        guard let distance = visualDistance(a, b) else {
            return make(.uncertain, .unknown, 0.3, "object.visual", [
                ev("dhash", .hash, 0.3,
                   "one of these has no usable visual fingerprint, so they cannot be "
                   + "compared by appearance")])
        }
        let labelsA = Set(a.sceneLabels.map { $0.identifier })
        let labelsB = Set(b.sceneLabels.map { $0.identifier })
        let shared = labelsA.intersection(labelsB).sorted()
        let sameOccasion = (gapHours(a, b).map { $0 <= sameOccasionHours }) ?? false

        if distance <= sameViewBits, !shared.isEmpty, sameOccasion {
            return make(.same, .sameInstance, 0.75, "object.visual", [
                ev("dhash", .hash, 0.65, "these two look like the same thing, minutes apart"),
                ev("scene_labels", .visual, 0.5, "and both were recognised as \(shared[0])")])
        }

        if distance <= sameViewBits, !shared.isEmpty {
            // Deliberately NOT a merge, and this is the honest half of Gate 2.
            //
            // Two near-identical photographs of a chair two days apart are either one
            // chair photographed twice or two chairs of the same model in one room, and
            // no signal here distinguishes them: appearance is identical by
            // construction, the labels agree, and the gap says nothing because objects
            // persist. Answering same would merge the two-identical-chairs case, and a
            // merge is not undone by the user noticing later.
            //
            // Tier 1 anticipates this: 部分类别（例如复杂物品识别）暂时做不到高置信度，
            // 可以先把这些类别降级为「Review Queue 优先」上线. So the category is
            // downgraded rather than the threshold loosened until the number improves.
            return make(.uncertain, .unknown, 0.55, "object.persistence", [
                ev("dhash", .hash, 0.55,
                   "these look like the same thing on two different occasions — but two "
                   + "of the same model look like this too, and nothing here can tell "
                   + "those apart")])
        }

        if distance >= differentViewBits, shared.isEmpty {
            return make(.different, .distinct, 0.8, "object.visual", [
                ev("dhash", .hash, 0.8,
                   "these look like different things and were recognised as different "
                   + "things")])
        }

        return make(.uncertain, .unknown, 0.4, "object.visual", [
            ev("dhash", .hash, 0.4,
               "these could be the same thing from a different angle, or two similar "
               + "things — telling those apart needs a visual embedding this build does "
               + "not have")])
    }

    // MARK: - Photos and people — 普通照片用时间/地点/视觉相似

    private static func resolvePhoto(_ a: AssetSignals, _ b: AssetSignals) -> Resolution {
        guard let distance = visualDistance(a, b) else {
            return make(.uncertain, .unknown, 0.3, "photo.visual", [
                ev("dhash", .hash, 0.3, "one of these has no usable visual fingerprint")])
        }
        if distance >= differentViewBits {
            return make(.different, .distinct, 0.85, "photo.visual", [
                ev("dhash", .hash, 0.85, "these are two different pictures")])
        }
        if distance <= sameViewBits {
            if let gap = gapHours(a, b), gap <= sameOccasionHours {
                var samePlace = true
                if let ga = a.geo, let gb = b.geo { samePlace = ga.km(to: gb) < 1.0 }
                if samePlace {
                    return make(.same, .sameInstance, 0.88, "photo.moment", [
                        ev("dhash", .hash, 0.7, "these look nearly identical"),
                        ev("created_at", .metadata, 0.6,
                           "and were taken within the same few hours")])
                }
                return make(.different, .distinct, 0.7, "photo.moment", [
                    ev("geo", .metadata, 0.7,
                       "these look alike but were taken in different places")])
            }
            // §9: one subject, two occasions. Related, and a deletion the user would
            // not forgive — so same as an entity, never same as a duplicate.
            return make(.same, .otherVersion, 0.6, "photo.subject", [
                ev("dhash", .hash, 0.6,
                   "the same subject photographed on two different occasions — related, "
                   + "and both kept")])
        }
        return make(.uncertain, .unknown, 0.45, "photo.visual", [
            ev("dhash", .hash, 0.45, "these are similar without being the same picture")])
    }

    // MARK: - Construction helpers
    //
    // `Evidence` and `Resolution` are both failable, and every call site here passes a
    // literal that satisfies them. Rather than sprinkle `!` through the file — which
    // would trap in front of a user — the two helpers below fall back to a resolution
    // that still explains itself.

    private static func ev(_ signal: String, _ tier: Tier, _ weight: Double,
                           _ reason: String) -> Evidence? {
        Evidence(signal: signal, tier: tier, weight: weight, reason: reason)
    }

    private static func make(_ verdict: EntityVerdict, _ relation: EntityRelation,
                             _ confidence: Double, _ resolver: String,
                             _ evidence: [Evidence?]) -> Resolution {
        let kept = evidence.compactMap { $0 }
        if let r = Resolution(verdict, relation, confidence, resolver, kept) { return r }
        // Unreachable with the literals above; if it ever is reached, the safe answer
        // is the one that merges nothing.
        return Resolution(.uncertain, .unknown, 0.0, resolver,
                          [Evidence(signal: "internal", tier: .metadata, weight: 0.01,
                                    reason: "this comparison could not be explained, so "
                                          + "nothing was concluded from it")!])!
    }
}
