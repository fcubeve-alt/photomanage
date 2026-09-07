// INFERRING A PLACE — Constitution §11, L1-B Minimum Necessary Inference.
//
//     无 GPS 时可以利用相邻时间照片、地标等推断，但必须保存置信度。
//
// The reference implementation is `30_ENGINE/pvm/infer.py` and its docstring carries
// the argument. The short version:
//
// * It infers from the photographs either side of an asset in time, and from nothing
//   else. §11 names 相邻时间照片 first and it is the one signal a metadata pass has.
// * Minimum Necessary Inference is a ladder, not a decision. Two anchors that agree on
//   a city give a city; two that agree only on a country give a country and say so;
//   two that disagree give nothing. A photo between Shinjuku and Yokohama is in Japan
//   and is in neither city, and picking the nearer anchor invents a fact.
// * One-sided inference is weaker than bracketed and reaches much less far. Knowing
//   where someone was ten minutes before a photo is consistent with them having got on
//   a train.
// * Screenshots and downloads never get an inferred place and are never anchors. A
//   screenshot taken while its owner was in Tokyo was not taken *in* Tokyo in any
//   sense a shelf of photographs should record.

import Foundation

/// A location the engine worked out rather than read.
///
/// §11: 必须保存置信度 — so the confidence is a stored property, not a constant applied
/// downstream where it could be forgotten.
public struct InferredPlace {
    public let geo: GeoFix
    public let place: PlaceName
    public let confidence: Double
    /// How specific the claim is: "city" or "country". Never finer than the evidence.
    public let granularity: String
    /// The assets it rests on, kept so the user can be shown them.
    public let anchors: [String]
    public let gapSeconds: Double
    public let reason: String

    public var isBracketed: Bool { anchors.count == 2 }
}

public enum PlaceInference {
    /// A bracketed inference — an anchor on each side — reaches this far.
    public static let maxGapSeconds = 2.0 * 60 * 60
    /// A one-sided inference reaches much less far.
    public static let maxOneSidedGapSeconds = 30.0 * 60
    /// Anchors further apart than this were not in the same place, whatever their
    /// names say.
    public static let agreeKm = 25.0
    /// The best an inference may claim, at zero gap. A measured fix is 1.0 and this
    /// must never approach it.
    public static let baseConfidence = 0.80
    /// Applied to the ceiling for a one-sided inference, not to the result — see
    /// `confidence(gap:limit:ceiling:)`.
    public static let oneSidedPenalty = 0.7
    /// The floor, reached exactly at the limits above.
    public static let minConfidence = 0.45

    public static func inferPlaces(_ assets: [AssetSignals]) -> [String: InferredPlace] {
        let anchors = assets.filter(isEligibleAnchor)
            .sorted { ($0.createdAt ?? .distantPast) < ($1.createdAt ?? .distantPast) }
        guard !anchors.isEmpty else { return [:] }
        let times = anchors.map { $0.createdAt ?? .distantPast }

        var out: [String: InferredPlace] = [:]
        for target in assets where isEligibleTarget(target) {
            guard let when = target.createdAt else { continue }
            let (before, after) = neighbours(anchors, times, when, target.assetID)
            if let inferred = decide(when: when, before: before, after: after) {
                out[target.assetID] = inferred
            }
        }
        return out
    }

    // MARK: - eligibility

    static func isEligibleTarget(_ a: AssetSignals) -> Bool {
        guard a.createdAt != nil else { return false }
        if let g = a.geo, g.source == .exif { return false }
        if a.isScreenshot || a.source == "downloaded" { return false }
        return true
    }

    static func isEligibleAnchor(_ a: AssetSignals) -> Bool {
        guard a.createdAt != nil, let g = a.geo, g.source == .exif,
              let p = a.place, (p.city != nil || p.country != nil) else { return false }
        return !a.isScreenshot && a.source != "downloaded"
    }

    // MARK: - selection

    private static func neighbours(_ anchors: [AssetSignals], _ times: [Date],
                                   _ when: Date, _ targetID: String)
            -> (AssetSignals?, AssetSignals?) {
        // Lower bound, then a linear step over any anchor that is the target itself.
        var lo = 0, hi = times.count
        while lo < hi {
            let mid = (lo + hi) / 2
            if times[mid] < when { lo = mid + 1 } else { hi = mid }
        }
        var before: AssetSignals?
        var j = lo - 1
        while j >= 0 {
            if anchors[j].assetID != targetID { before = anchors[j]; break }
            j -= 1
        }
        var after: AssetSignals?
        j = lo
        while j < anchors.count {
            if anchors[j].assetID != targetID { after = anchors[j]; break }
            j += 1
        }
        return (before, after)
    }

    private static func decide(when: Date, before: AssetSignals?,
                               after: AssetSignals?) -> InferredPlace? {
        var usable: [(AssetSignals, Double)] = []
        for anchor in [before, after] {
            guard let a = anchor, let t = a.createdAt else { continue }
            usable.append((a, abs(t.timeIntervalSince(when))))
        }

        if usable.count == 2 {
            let widest = max(usable[0].1, usable[1].1)
            if widest <= maxGapSeconds {
                return fromPair(usable[0].0, usable[1].0, gap: widest)
            }
            // One side is too far to help. A distant anchor must not veto a close one.
            usable = usable.filter { $0.1 <= maxOneSidedGapSeconds }
            if usable.count == 2 {
                usable = [usable.min(by: { $0.1 < $1.1 })!]
            }
        }

        if usable.count == 1, usable[0].1 <= maxOneSidedGapSeconds {
            return fromSingle(usable[0].0, gap: usable[0].1)
        }
        return nil
    }

    // MARK: - confidence

    /// Linear from `ceiling` at no gap down to `minConfidence` at the limit.
    ///
    /// Decaying towards zero and then refusing anything under the floor — which is
    /// what the first version did — makes the stated limits fiction: `maxGapSeconds`
    /// would really have been 52 minutes and a one-sided inference would have been
    /// refused at every gap including zero.
    static func confidence(gap: Double, limit: Double,
                           ceiling: Double = baseConfidence) -> Double {
        let span = max(0, min(1, gap / limit))
        return ((ceiling - (ceiling - minConfidence) * span) * 1000).rounded() / 1000
    }

    // MARK: - the ladder

    private static func fromPair(_ a: AssetSignals, _ b: AssetSignals,
                                 gap: Double) -> InferredPlace? {
        guard let ga = a.geo, let gb = b.geo, let pa = a.place, let pb = b.place
        else { return nil }
        // The subject was moving. A photo between London and Paris is in neither.
        guard ga.km(to: gb) <= agreeKm else { return nil }
        let conf = confidence(gap: gap, limit: maxGapSeconds)
        guard conf >= minConfidence else { return nil }

        let geo = GeoFix(lat: (ga.lat + gb.lat) / 2, lon: (ga.lon + gb.lon) / 2,
                         source: .inferred)
        let minutes = Int((gap / 60).rounded())

        if let city = pa.city, city == pb.city, pa.country == pb.country {
            let place = PlaceName(country: pa.country, city: city, confidence: conf)
            let reason = "no location was saved with this photo; the photos taken "
                + "within \(minutes) minutes either side were both in \(city)"
            return InferredPlace(geo: geo, place: place, confidence: conf,
                                 granularity: "city", anchors: [a.assetID, b.assetID],
                                 gapSeconds: gap, reason: reason)
        }

        if let country = pa.country, country == pb.country {
            // The middle rung: the country is supported, the city is not.
            let place = PlaceName(country: country, city: nil, confidence: conf)
            let cities = Set([pa.city, pb.city].compactMap { $0 }).sorted()
                .joined(separator: " and ")
            let detail = cities.isEmpty ? ""
                : " — they were in \(cities), so the city is not certain"
            let reason = "no location was saved with this photo; the photos taken "
                + "within \(minutes) minutes either side were both in \(country)\(detail)"
            return InferredPlace(geo: geo, place: place, confidence: conf,
                                 granularity: "country", anchors: [a.assetID, b.assetID],
                                 gapSeconds: gap, reason: reason)
        }
        return nil
    }

    private static func fromSingle(_ anchor: AssetSignals, gap: Double) -> InferredPlace? {
        guard let g = anchor.geo, let p = anchor.place else { return nil }
        let conf = confidence(gap: gap, limit: maxOneSidedGapSeconds,
                              ceiling: baseConfidence * oneSidedPenalty)
        guard conf >= minConfidence else { return nil }
        guard let where_ = p.city ?? p.country else { return nil }

        let geo = GeoFix(lat: g.lat, lon: g.lon, source: .inferred)
        let place = PlaceName(country: p.country, city: p.city, confidence: conf)
        let minutes = Int((gap / 60).rounded())
        let reason = "no location was saved with this photo; the nearest photo that has "
            + "one was taken \(minutes) minutes away, in \(where_)"
        return InferredPlace(geo: geo, place: place, confidence: conf,
                             granularity: p.city != nil ? "city" : "country",
                             anchors: [anchor.assetID], gapSeconds: gap, reason: reason)
    }
}
