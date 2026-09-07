import Foundation

/// Library-level context — the facts no single photo contains.
///
/// "Is this a travel photo?" cannot be answered from one asset. It needs to know where
/// this person usually is, and whether this capture sits inside a run of days spent
/// somewhere else. Computed once from the cheapest signals available and handed to the
/// per-asset rules. Mirrors `30_ENGINE/pvm/context.py`.
///
/// **Home is learned, never asked.** The Constitution's premise is a library that
/// catalogues itself; a setup wizard asking "where do you live?" fails that on the
/// first screen.

public struct Trip {
    public let city: String?
    public let country: String?
    public let start: Date
    public let end: Date
    public let assetCount: Int

    /// `Travel > Tokyo · Apr 2025` — the shape the tree already uses.
    public var label: String {
        let f = DateFormatter()
        f.locale = Locale(identifier: "en_US_POSIX")
        f.dateFormat = "MMM yyyy"
        return "\(city ?? country ?? "Away") · \(f.string(from: start))"
    }

    public func contains(_ when: Date) -> Bool {
        let cal = Calendar(identifier: .gregorian)
        let day = cal.startOfDay(for: when)
        return day >= cal.startOfDay(for: start) && day <= cal.startOfDay(for: end)
    }
}

/// §3's fourth level of time: a capture session.
public struct Moment {
    public let start: Date
    public let end: Date
    public let assetCount: Int

    public var label: String {
        let f = DateFormatter()
        f.locale = Locale(identifier: "en_GB")
        f.timeZone = TimeZone(identifier: "UTC")
        f.dateFormat = "HH:mm"
        return f.string(from: start)
    }
}

/// One day away from home with enough photographs in it to be an occasion.
///
/// Deliberately not a `Trip`: the browse tree treats Travel as a run of days, and
/// calling a Saturday afternoon a trip would put it on the same shelf as a fortnight
/// in Japan. This is an *event* — it reaches the memory graph and mints no folder.
public struct DayOut {
    public let day: Date
    public let city: String?
    public let country: String?
    public let assetCount: Int

    public var label: String {
        let f = DateFormatter()
        f.locale = Locale(identifier: "en_GB")
        f.dateFormat = "d MMM yyyy"
        return "\(city ?? country ?? "Away") · \(f.string(from: day))"
    }
}

/// One capture session with several named people in it — §11's 时间 + 人物.
///
/// Two people who are both in the library are a photograph of two people; two people
/// photographed together across a session is an occasion, and it is the only kind of
/// event this engine can derive without knowing what a birthday is.
public struct Gathering {
    public let start: Date
    public let people: [String]
    public let assetCount: Int

    public var label: String {
        var names = people.prefix(3).joined(separator: ", ")
        if people.count > 3 { names += " and \(people.count - 3) more" }
        let f = DateFormatter()
        f.locale = Locale(identifier: "en_GB")
        f.dateFormat = "d MMM yyyy"
        return "\(names) · \(f.string(from: start))"
    }
}

public struct LibraryContext {
    public var home: GeoFix?
    public var homeCity: String?
    public var homeCountry: String?
    /// Counts DAYS, not captures. See `build`.
    public var homeSampleSize: Int = 0
    public var trips: [Trip] = []
    public var knownPeople: [String] = []
    /// assetID → the capture session it belongs to. Absent for an asset with no
    /// neighbours: a lone photograph is not a session, and inventing one would put a
    /// browse entry in front of the user for every stray shot they ever took.
    public var moments: [String: Moment] = [:]
    /// §11 无 GPS 时可以利用相邻时间照片…推断，但必须保存置信度. assetID → the place
    /// worked out from the photographs either side of it in time. Absent for every
    /// asset the evidence did not reach, which is most of them.
    public var inferredPlaces: [String: InferredPlace] = [:]
    /// §11's other Event candidates. Trips are `trips`; these are the occasions that
    /// are not trips.
    public var daysOut: [DayOut] = []
    public var gatherings: [Gathering] = []
    public var assetCount: Int = 0

    public init() {}

    public var homeConfidence: Double {
        guard homeSampleSize > 0 else { return 0 }
        return min(0.95, 0.4 + Double(homeSampleSize) / 400.0)
    }

    public func isAway(_ geo: GeoFix?) -> Bool {
        guard let g = geo, let h = home else { return false }
        return g.km(to: h) > LibraryContextBuilder.awayKm
    }

    public func moment(for assetID: String) -> Moment? { moments[assetID] }

    public func inferredPlace(for assetID: String) -> InferredPlace? {
        inferredPlaces[assetID]
    }

    public func trip(for when: Date?, geo: GeoFix?) -> Trip? {
        guard let w = when, isAway(geo) else { return nil }
        return trips.first { $0.contains(w) }
    }
}

public enum LibraryContextBuilder {
    /// Photographs taken further apart than this are two occasions, not one. Clock
    /// hours cannot do this job — six frames at 17:59 and two at 18:01 are one moment
    /// and would land in two.
    public static let momentGapSeconds = 20.0 * 60
    /// A single photograph is a photograph, not a session worth its own browse entry.
    public static let minMomentAssets = 2

    /// Group captures into sessions by proximity in time, derived from neighbours
    /// rather than from the clock. A moment that splits one occasion in two is worse
    /// than no moment at all: the user sees the same afternoon twice and trusts the
    /// timeline less.
    public static func findMoments(_ assets: [AssetSignals]) -> [String: Moment] {
        let dated = assets.filter { $0.createdAt != nil }
            .sorted { $0.createdAt! < $1.createdAt! }
        var out: [String: Moment] = [:]
        var run: [AssetSignals] = []

        func close(_ group: [AssetSignals]) {
            guard group.count >= minMomentAssets,
                  let first = group.first?.createdAt,
                  let last = group.last?.createdAt else { return }
            let moment = Moment(start: first, end: last, assetCount: group.count)
            for asset in group { out[asset.assetID] = moment }
        }

        for asset in dated {
            if let previous = run.last?.createdAt,
               asset.createdAt!.timeIntervalSince(previous) > momentGapSeconds {
                close(run)
                run = []
            }
            run.append(asset)
        }
        close(run)
        return out
    }

    /// A capture this far from home is somewhere else, not a longer walk.
    public static let awayKm = 120.0
    /// Below this many days away it is a day out, not a trip worth its own entry.
    public static let minTripDays = 2
    /// ...and below this many assets it is not worth a browse entry either. Without
    /// this floor the detector produced 53 "trips" of two photos each from a scatter of
    /// single captures, burying the one real nine-day trip. A folder the user has to
    /// read past costs more attention than it saves.
    public static let minTripAssets = 8

    /// A day away from home that is NOT long enough to be a trip. The bar is high for
    /// the reason `minTripAssets` is: the first trip detector produced 53 "trips" of
    /// two photos each and buried the one real trip in noise.
    public static let minDayOutAssets = 6
    /// How many named people make a session a gathering rather than a photograph that
    /// happens to have two faces in it.
    public static let minGatheringPeople = 2
    /// ...and how many photographs. One frame of two people is not an occasion.
    public static let minGatheringAssets = 4
    /// ~1 km. Coarse enough that GPS jitter does not split one home into four, fine
    /// enough that the next town does not merge into it.
    public static let grid = 0.01

    private struct Cell: Hashable { let lat: Double; let lon: Double }

    /// One pass, metadata only. Nothing here decodes a pixel.
    public static func build(_ assets: [AssetSignals]) -> LibraryContext {
        var ctx = LibraryContext()
        let cal = Calendar(identifier: .gregorian)

        var cellCaptures: [Cell: Int] = [:]
        var cellNames: [Cell: [String: Int]] = [:]
        // Home is measured in DISTINCT DAYS, not captures. Counting captures makes home
        // wherever the camera was busiest, so one weekend of 500 beach photos outvotes
        // two years of living somewhere.
        var homeDays: [Cell: Set<Date>] = [:]
        var cellDays: [Cell: Set<Date>] = [:]
        var people: [String: Int] = [:]
        var located: [(Date, GeoFix, String?, String?)] = []

        for a in assets {
            ctx.assetCount += 1
            for f in a.faceClusters where f.name != nil {
                people[f.name!, default: 0] += 1
            }
            guard let geo = a.geo, geo.source == .exif else { continue }
            let cell = Cell(lat: (geo.lat / grid).rounded() * grid,
                            lon: (geo.lon / grid).rounded() * grid)
            cellCaptures[cell, default: 0] += 1
            if let place = a.place {
                let key = "\(place.country ?? "")|\(place.city ?? "")"
                cellNames[cell, default: [:]][key, default: 0] += 1
            }
            guard let when = a.createdAt else { continue }
            let day = cal.startOfDay(for: when)
            cellDays[cell, default: []].insert(day)
            let hour = cal.component(.hour, from: when)
            let weekday = cal.component(.weekday, from: when)
            // Home is where the evenings and weekends are. Daytime weekday captures are
            // where the office is, and an office is not home.
            if hour >= 19 || hour <= 7 || weekday == 1 || weekday == 7 {
                homeDays[cell, default: []].insert(day)
            }
            located.append((when, geo, a.place?.country, a.place?.city))
        }

        ctx.knownPeople = people.sorted { $0.value > $1.value }.map { $0.key }

        let pool = homeDays.isEmpty ? cellDays : homeDays
        if let best = pool.max(by: { lhs, rhs in
            if lhs.value.count != rhs.value.count { return lhs.value.count < rhs.value.count }
            return (cellCaptures[lhs.key] ?? 0) < (cellCaptures[rhs.key] ?? 0)
        }) {
            ctx.home = GeoFix(lat: best.key.lat, lon: best.key.lon, source: .inferred)
            ctx.homeSampleSize = best.value.count
            if let names = cellNames[best.key],
               let top = names.max(by: { $0.value < $1.value }) {
                let parts = top.key.components(separatedBy: "|")
                ctx.homeCountry = parts.first?.isEmpty == false ? parts[0] : nil
                ctx.homeCity = parts.count > 1 && !parts[1].isEmpty ? parts[1] : nil
            }
        }

        ctx.trips = findTrips(located, home: ctx.home, calendar: cal)
        ctx.moments = findMoments(assets)
        // §11. Last, because it reads only the assets and not the rest of the context.
        // Keeping the dependency one-way makes it obvious that home and trips are
        // derived from MEASURED fixes only — an inferred place feeding the home
        // cluster would be the system learning from itself.
        ctx.inferredPlaces = PlaceInference.inferPlaces(assets)
        // §11: 时间 + 地点 + 人物 + 内容 可以自动形成 Event / Trip 候选. Trip was the
        // only one derived; these are the others the metadata pass supports honestly.
        ctx.daysOut = findDaysOut(located, home: ctx.home, trips: ctx.trips, calendar: cal)
        ctx.gatherings = findGatherings(assets, moments: ctx.moments)
        return ctx
    }

    /// Days away from home that no trip already covers.
    ///
    /// Subtracts what `findTrips` claimed, because a day inside a twelve-day trip is
    /// part of the trip; surfacing it separately would put the same photographs under
    /// two events and make both mean less.
    static func findDaysOut(_ located: [(Date, GeoFix, String?, String?)],
                            home: GeoFix?, trips: [Trip],
                            calendar cal: Calendar) -> [DayOut] {
        guard let home = home else { return [] }
        var claimed: Set<Date> = []
        for trip in trips {
            var day = cal.startOfDay(for: trip.start)
            let end = cal.startOfDay(for: trip.end)
            while day <= end {
                claimed.insert(day)
                guard let next = cal.date(byAdding: .day, value: 1, to: day) else { break }
                day = next
            }
        }

        var away: [Date: [String: Int]] = [:]
        for (when, geo, country, city) in located where geo.km(to: home) > awayKm {
            let day = cal.startOfDay(for: when)
            guard !claimed.contains(day) else { continue }
            away[day, default: [:]]["\(country ?? "")|\(city ?? "")", default: 0] += 1
        }

        var out: [DayOut] = []
        for day in away.keys.sorted() {
            let names = away[day] ?? [:]
            let total = names.values.reduce(0, +)
            guard total >= minDayOutAssets,
                  let top = names.max(by: { $0.value < $1.value }) else { continue }
            let parts = top.key.components(separatedBy: "|")
            out.append(DayOut(day: day,
                              city: parts.count > 1 && !parts[1].isEmpty ? parts[1] : nil,
                              country: parts.first?.isEmpty == false ? parts[0] : nil,
                              assetCount: total))
        }
        return out
    }

    /// Capture sessions with several named people in them.
    ///
    /// Built on `moments` rather than clock hours for the same reason `findMoments` is:
    /// an occasion does not end at six o'clock. Only NAMED faces count — an unnamed
    /// cluster is a face the user has not identified, and §16 forbids inferring
    /// anything further about who they are, including that they were somewhere
    /// together.
    static func findGatherings(_ assets: [AssetSignals],
                               moments: [String: Moment]) -> [Gathering] {
        guard !moments.isEmpty else { return [] }
        var byMoment: [Date: [AssetSignals]] = [:]
        for asset in assets {
            guard let moment = moments[asset.assetID] else { continue }
            byMoment[moment.start, default: []].append(asset)
        }

        var out: [Gathering] = []
        for start in byMoment.keys.sorted() {
            let members = byMoment[start] ?? []
            guard members.count >= minGatheringAssets else { continue }
            let people = Set(members.flatMap { $0.faceClusters.compactMap { $0.name } }).sorted()
            guard people.count >= minGatheringPeople else { continue }
            out.append(Gathering(start: start, people: people, assetCount: members.count))
        }
        return out
    }

    /// A trip is a run of consecutive days spent away from home. A one-day gap is
    /// tolerated — a trip does not end because nobody took a photo on the Tuesday.
    private static func findTrips(_ located: [(Date, GeoFix, String?, String?)],
                                  home: GeoFix?, calendar cal: Calendar) -> [Trip] {
        guard let home = home else { return [] }
        var awayDays: [Date: [String: Int]] = [:]
        for (when, geo, country, city) in located where geo.km(to: home) > awayKm {
            let day = cal.startOfDay(for: when)
            awayDays[day, default: [:]]["\(country ?? "")|\(city ?? "")", default: 0] += 1
        }
        guard !awayDays.isEmpty else { return [] }

        var trips: [Trip] = []
        var run: [Date] = []

        func close(_ days: [Date]) {
            guard days.count >= minTripDays, let first = days.first, let last = days.last else { return }
            var names: [String: Int] = [:]
            var total = 0
            for d in days {
                for (k, v) in awayDays[d] ?? [:] {
                    names[k, default: 0] += v
                    total += v
                }
            }
            guard total >= minTripAssets, let top = names.max(by: { $0.value < $1.value }) else { return }
            let parts = top.key.components(separatedBy: "|")
            trips.append(Trip(city: parts.count > 1 && !parts[1].isEmpty ? parts[1] : nil,
                              country: parts.first?.isEmpty == false ? parts[0] : nil,
                              start: first, end: last, assetCount: total))
        }

        for day in awayDays.keys.sorted() {
            if let previous = run.last,
               let gap = cal.dateComponents([.day], from: previous, to: day).day, gap > 2 {
                close(run)
                run = []
            }
            run.append(day)
        }
        close(run)
        return trips
    }
}
