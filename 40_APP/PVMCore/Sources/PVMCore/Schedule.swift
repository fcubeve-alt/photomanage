import Foundation

/// INGESTION PLANNING — how a large library gets catalogued without taking the phone
/// away. L1 §24 Gate 1 (分块/分时 + checkpoint + 增量处理 + 后台机会执行) and Gate 3
/// (首次使用必须 Progressive Indexing…新增 TTFUV 作为 P0 指标).
///
/// The measured data says something better than "a bit each day". Breadth is nearly
/// free and depth is what costs:
///  * A **breadth pass** reads PhotoKit metadata only — date, GPS, media subtype. No
///    pixel is decoded, so the per-asset cost is a SQLite write: 0.17 ms measured.
///    100k assets in under 30 seconds, which is already Timeline, Places, Travel and
///    Screenshots — a browsable library on the first screen.
///  * A **depth pass** decodes a thumbnail and runs OCR, embedding and faces: 105–154
///    ms measured, three orders of magnitude more. That is the part worth pacing.
///
/// So the user is never told "wait N days for your library". They are told it is here
/// in a minute and gets deeper while they use the phone.
///
/// **What this does not solve, and the point must not be lost:** pacing makes A3
/// (survivability) *more* critical. A ninety-minute run that loses its place costs
/// ninety minutes; a twenty-two-day plan that loses its place never finishes. And
/// `BGProcessingTask` is granted at the system's discretion — a daily figure is a
/// request, not a schedule. Every number here is a projection from a resumable cursor.

public struct IngestionOption {
    public let key: String
    public let label: String
    public let dailyAssets: Int
    public let days: Int
    public let dailyWorkMinutes: Double
    public let caveat: String
}

public struct IngestionPlan {
    public let librarySize: Int
    public let breadthSeconds: Double
    public let options: [IngestionOption]
    public let recommended: String
    public let notes: [String]

    /// What the user is actually told — leading with what they get, not with what we
    /// are about to do to their phone.
    public var userMessage: String {
        let f = NumberFormatter()
        f.numberStyle = .decimal
        let count = f.string(from: NSNumber(value: librarySize)) ?? "\(librarySize)"
        return """
        Your library has \(count) photos.
        The shelves are ready in about \(IngestionPlanner.human(breadthSeconds)) — dates, \
        places, trips and screenshots are sorted straight away.
        Recognising what is inside them takes longer, so it happens in the background \
        while you use your phone. You can change or pause this any time.
        """
    }

    public func option(_ key: String) -> IngestionOption? { options.first { $0.key == key } }
}

public enum IngestionPlanner {
    /// Measured on the iOS Simulator, 2026-09-06, both runs. A range, not a figure: two
    /// runs of identical code came back 1.47x apart, so the planner carries the band and
    /// quotes the pessimistic end to the user.
    public static let breadthMillisecondsPerAsset = (fast: 0.18, slow: 0.28)
    public static let depthMillisecondsPerAsset = (fast: 104.7, slow: 154.1)

    /// How much uninterrupted work is reasonable to ask of a phone in one background
    /// grant. Not measured — a product judgement, and the one most worth arguing with.
    public static let comfortableSessionMinutes = 6.0
    /// What the system might actually grant in a day, pessimistically. Also a judgement.
    public static let sessionsPerDay = 2

    public static func human(_ seconds: Double) -> String {
        if seconds < 90 { return "\(Int(seconds.rounded())) seconds" }
        if seconds < 5400 { return "\(Int((seconds / 60).rounded())) minutes" }
        return String(format: "%.1f hours", seconds / 3600)
    }

    public static func plan(librarySize: Int, pessimistic: Bool = true) -> IngestionPlan {
        let breadthMs = pessimistic ? breadthMillisecondsPerAsset.slow : breadthMillisecondsPerAsset.fast
        let depthMs = pessimistic ? depthMillisecondsPerAsset.slow : depthMillisecondsPerAsset.fast
        let breadthSeconds = Double(librarySize) * breadthMs / 1000

        let perSession = max(1, Int(comfortableSessionMinutes * 60_000 / depthMs))
        let gentleDaily = perSession * sessionsPerDay

        func option(_ key: String, _ label: String, _ daily: Int, _ caveat: String) -> IngestionOption {
            let d = max(1, daily)
            return IngestionOption(key: key, label: label, dailyAssets: d,
                                   days: max(1, Int(ceil(Double(librarySize) / Double(d)))),
                                   dailyWorkMinutes: Double(d) * depthMs / 60_000,
                                   caveat: caveat)
        }

        let options = [
            option("gentle", "Quietly in the background", gentleDaily,
                   "Uses only the time the system gives us. Some days it gives us none."),
            option("overnight", "Overnight while charging", gentleDaily * 4,
                   "Needs the phone on charge and idle. Fastest hands-off option."),
            option("now", "All at once, now", max(1, librarySize),
                   "The phone will be busy and will warm up. Best left plugged in."),
        ]

        let oneGoHours = Double(librarySize) * depthMs / 3_600_000
        let recommended = oneGoHours <= 0.5 ? "now" : (oneGoHours <= 8 ? "overnight" : "gentle")

        var notes = [String(format: "depth pass in one go would be %.1f h at %.0f ms/asset",
                            oneGoHours, depthMs)]
        if oneGoHours > 1.5 {
            notes.append("too long for a foreground run — this library must be paced, and "
                         + "pacing means the resume cursor is load-bearing (A3)")
        }
        notes.append("every figure is a projection from a resumable cursor, never a promise: "
                     + "background time is granted by the system, not scheduled by us")

        return IngestionPlan(librarySize: librarySize, breadthSeconds: breadthSeconds,
                             options: options, recommended: recommended, notes: notes)
    }

    /// §24 Gate 3 names TTFUV a P0 metric: the time until the user has a structure to
    /// browse — the breadth pass — not the time until everything is understood.
    public static func timeToFirstUsefulView(librarySize: Int, pessimistic: Bool = true) -> Double {
        Double(librarySize)
            * (pessimistic ? breadthMillisecondsPerAsset.slow : breadthMillisecondsPerAsset.fast)
            / 1000
    }

    /// What to show while it runs. A percentage alone is a progress bar; what a user
    /// wants to know is whether their library is usable yet.
    public static func progressReport(done: Int, total: Int) -> String {
        guard total > 0 else { return "nothing to do" }
        if done >= total { return "All \(total) photos have been looked at." }
        let pct = Int((Double(done) / Double(total) * 100).rounded())
        let remainingHours = Double(total - done) * depthMillisecondsPerAsset.slow / 3_600_000
        let when = remainingHours < 1.5
            ? "\(Int((remainingHours * 60).rounded())) minutes"
            : String(format: "about %.0f hours of background time", remainingHours)
        return "\(done) of \(total) photos looked at (\(pct)%). Everything is already "
             + "findable by date, place and trip; the rest needs \(when)."
    }
}
