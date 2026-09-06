import XCTest
@testable import PVMCore

/// Tests for the visual memory graph, ported from `30_ENGINE/tests/test_memory.py`.
///
/// §2 lists Remember among the ten things the product *is*, and §15 builds every later
/// service on it. Filing a photo on a shelf is not remembering it; the graph is what
/// lets the library answer L1-B's worked example — *"我的红色行李箱最后在哪里出现过？"*
/// — instead of only "you have some objects".
///
/// Mostly these lock down what the graph is **not allowed to claim**. A memory that
/// overstates is worse than no memory: it is a confident wrong answer about the user's
/// own life, which is the failure §11 and §16 exist to prevent.

private let london = GeoFix(lat: 51.5074, lon: -0.1278)
private let tokyo = GeoFix(lat: 35.6762, lon: 139.6503)
private let uk = PlaceName(country: "United Kingdom", city: "London", confidence: 0.9)
private let japan = PlaceName(country: "Japan", city: "Tokyo", confidence: 0.9)

private func date(_ y: Int, _ m: Int, _ d: Int, _ h: Int = 14) -> Date {
    var c = DateComponents(); c.year = y; c.month = m; c.day = d; c.hour = h
    var cal = Calendar(identifier: .gregorian)
    cal.timeZone = TimeZone(identifier: "UTC")!
    return cal.date(from: c)!
}

private func asset(_ id: String, _ when: Date? = nil,
                   build: (inout AssetSignals) -> Void = { _ in }) -> AssetSignals {
    var s = AssetSignals(assetID: id)
    s.createdAt = when ?? date(2025, 6, 18)
    s.pixelW = 4032; s.pixelH = 3024; s.byteSize = 500_000
    s.contentHash = "sha::\(id)"
    build(&s)
    return s
}

private func graph(of assets: [AssetSignals], momentGroups: [[String]] = []) -> MemoryGraph {
    let context = LibraryContextBuilder.build(assets)
    let classifier = Classifier(context: context, budget: .text)
    var classifications: [String: Classification] = [:]
    for a in assets { classifications[a.assetID] = classifier.classify(a) }
    return MemoryBuilder.build(assets: assets, classifications: classifications,
                               context: context, momentGroups: momentGroups)
}

final class MemoryEvidenceTests: XCTestCase {

    /// §10's red line, applied to entities: a thing the library claims exists has to
    /// be able to say why it thinks so, or it is an assertion rather than a memory.
    func testEntityWithoutEvidenceCannotBeBuilt() {
        XCTAssertNil(Entity(entityID: "person:nobody", kind: .person,
                            name: "Nobody", evidence: []))
    }

    func testEveryEntityTheBuilderProducesCanExplainItself() {
        let g = graph(of: FixtureLibrary.make())
        XCTAssertFalse(g.entities.isEmpty, "the fixture must produce entities at all")
        for entity in g.entities.values {
            XCTAssertFalse(entity.evidence.isEmpty, "\(entity.entityID) has no evidence")
            XCTAssertFalse(entity.why.trimmingCharacters(in: .whitespaces).isEmpty,
                           "\(entity.entityID) explains nothing")
            XCTAssertGreaterThan(entity.confidence, 0)
        }
    }

    func testEveryObservationCarriesAReason() {
        let g = graph(of: FixtureLibrary.make())
        XCTAssertFalse(g.observations.isEmpty)
        for o in g.observations {
            XCTAssertFalse(o.reason.trimmingCharacters(in: .whitespaces).isEmpty)
        }
    }
}

final class MemoryPeopleAndPlacesTests: XCTestCase {

    func testNamedFacesBecomePeopleAndUnnamedOnesDoNot() {
        let g = graph(of: [
            asset("p1") { $0.faceClusters = [FaceCluster(clusterID: "c-anna", name: "Anna")] },
            asset("p2") { $0.faceClusters = [FaceCluster(clusterID: "c-unknown")] },
        ])
        let people = g.entities.values.filter { $0.kind == .person }.map { $0.name }
        XCTAssertEqual(["Anna"], people,
                       "an unnamed cluster is a face, not a person the user has named")
    }

    func testAnInferredPlaceSaysSo() {
        let measured = graph(of: [asset("m") {
            $0.geo = GeoFix(lat: london.lat, lon: london.lon, source: .exif); $0.place = uk
        }])
        let inferred = graph(of: [asset("i") {
            $0.geo = GeoFix(lat: london.lat, lon: london.lon, source: .inferred); $0.place = uk
        }])
        XCTAssertFalse(measured.observations.allSatisfy { $0.isInferred })
        XCTAssertTrue(inferred.observations.allSatisfy { $0.isInferred },
                      "§11: a place derived from neighbours must not look like a fix")
    }

    /// The bug the Python tests caught first: a face recognised with certainty in a
    /// photo whose location was inferred was reported as fact — "Anna was in London on
    /// the 18th" — because the observation carried one provenance field for both halves.
    func testTheAnswerHedgesWhenOnlyThePlaceWasInferred() {
        let g = graph(of: [asset("i") {
            $0.faceClusters = [FaceCluster(clusterID: "c", name: "Anna")]
            $0.geo = GeoFix(lat: london.lat, lon: london.lon, source: .inferred)
            $0.place = uk
        }])
        XCTAssertTrue(g.answerWhereLastSeen("Anna").contains("inferred"),
                      "an inference dressed as a measurement is the failure §11 names")
    }
}

final class MemoryObjectNamingTests: XCTestCase {

    func testASuitcaseIsASuitcaseEvenThoughTheShelfIsOther() {
        let g = graph(of: [asset("s") {
            $0.sceneLabels = [SceneLabel(identifier: "suitcase", confidence: 0.8)]
        }])
        let objects = g.entities.values.filter { $0.kind == .object }
        XCTAssertEqual(1, objects.count)
        XCTAssertEqual("Suitcase", objects.first?.name)
        XCTAssertEqual("Objects > Other", objects.first?.categoryPath,
                       "the coarse shelf is kept, not hidden — both are true")
    }

    func testNoEntityIsEverCalledOther() {
        let g = graph(of: FixtureLibrary.make())
        for entity in g.entities.values {
            XCTAssertNotEqual("other", entity.name.lowercased(),
                              "a shelf named Other names nothing; it cannot be an entity")
        }
    }

    /// *"我的红色行李箱最后在哪里出现过？"* — and the honest half of the answer.
    func testTheWorkedExampleFromL1B() {
        let g = graph(of: [
            asset("t1", date(2025, 4, 11, 10)) {
                $0.geo = tokyo; $0.place = japan
                $0.sceneLabels = [SceneLabel(identifier: "suitcase", confidence: 0.8)]
            },
            asset("t2", date(2025, 4, 19, 18)) {
                $0.geo = london; $0.place = uk
                $0.sceneLabels = [SceneLabel(identifier: "suitcase", confidence: 0.8)]
            },
        ])
        let answer = g.answerWhereLastSeen("my red suitcase")

        // The part it can answer.
        XCTAssertTrue(answer.contains("19 April 2025"), answer)
        XCTAssertTrue(answer.contains("London"), answer)
        // The part it must not pretend to answer: per-category entity resolution
        // (§24 Gate 2) is not built, so "red" is a word it cannot act on and has to
        // admit to rather than silently drop.
        XCTAssertTrue(answer.contains("red"), answer)
        XCTAssertTrue(answer.contains("may not be yours"), answer)
    }

    func testAFullMatchCarriesNoSpuriousCaveat() {
        let g = graph(of: [asset("s") {
            $0.geo = london; $0.place = uk
            $0.sceneLabels = [SceneLabel(identifier: "suitcase", confidence: 0.8)]
        }])
        XCTAssertFalse(g.answerWhereLastSeen("suitcase").contains("may not be yours"))
    }

    func testNothingKnownIsSaidPlainly() {
        let g = graph(of: [asset("a") { $0.geo = london; $0.place = uk }])
        XCTAssertTrue(g.answerWhereLastSeen("my grandmother's ring")
            .contains("Nothing in the library"))
    }
}

final class MemoryDocumentsAndPurchasesTests: XCTestCase {

    func testAPassportPhotoIsEvidenceAboutAPassport() {
        let g = graph(of: [asset("d") {
            $0.ocrRan = true; $0.ocrText = "PASSPORT"; $0.geo = london; $0.place = uk
        }])
        let docs = g.entities.values.filter { $0.kind == .document }.map { $0.name }
        XCTAssertTrue(docs.contains("Passport"),
                      "singular: one photo shows one passport, not a shelf of them")
    }

    /// §15 Purchase & Warranty Memory. Two documents, one thing you own.
    func testAReceiptAndItsOrderConfirmationAreOnePurchase() {
        let g = graph(of: [
            asset("r", date(2026, 3, 15)) {
                $0.ocrRan = true; $0.ocrText = "RECEIPT — HEADPHONES £129.00"
            },
            asset("o", date(2026, 3, 14)) {
                $0.isScreenshot = true; $0.source = "screenshot"
                $0.pixelW = 1170; $0.pixelH = 2532
                $0.ocrRan = true; $0.ocrText = "ORDER CONFIRMATION — HEADPHONES"
            },
        ])
        let purchases = g.entities.values.filter { $0.kind == .purchase }
        XCTAssertEqual(1, purchases.count, "one purchase, evidenced twice")
        XCTAssertEqual("Headphones", purchases.first?.name)
        XCTAssertEqual(2, g.history(of: purchases.first!.entityID).count)
    }

    func testAReceiptThatNamesNothingStaysAReceipt() {
        let g = graph(of: [asset("r") {
            $0.ocrRan = true; $0.ocrText = "RECEIPT 14.02.2026 TOTAL 9.99"
        }])
        let purchases = g.entities.values.filter { $0.kind == .purchase }.map { $0.name }
        XCTAssertEqual(["Purchase"], purchases,
                       "inventing a product name out of a total is the confident guess §11 forbids")
    }
}

final class MemoryEventsTests: XCTestCase {

    func testATripBecomesAnEventWithItsPhotos() {
        let g = graph(of: FixtureLibrary.make())
        let events = g.entities.values.filter { $0.kind == .event }
        XCTAssertEqual(1, events.count, "the fixture contains exactly one trip")
        XCTAssertTrue(events.first!.name.contains("Tokyo"))
        XCTAssertGreaterThanOrEqual(g.history(of: events.first!.entityID).count, 12,
                                    "§11: the user should never build a travel album by hand")
    }
}

/// §15 and §16. The graph may record that two people appear together. It may not
/// conclude what they are to each other, and it never characterises anyone.
final class MemoryRelationshipBoundaryTests: XCTestCase {

    func testCoOccurrenceIsACountAndNothingMore() {
        let g = graph(of: FixtureLibrary.make())
        let pairs = g.coOccurring("person:anna", kind: .person)
        XCTAssertEqual(1, pairs.count)
        XCTAssertEqual("person:ben", pairs.first?.0)
        XCTAssertEqual(1, pairs.first?.1)
    }

    func testThereIsNoKindForARelationship() {
        let kinds = Set(EntityKind.allCases.map { $0.rawValue })
        for forbidden in ["relationship", "partner", "family", "friend", "colleague"] {
            XCTAssertFalse(kinds.contains(forbidden))
        }
    }
}

final class MemoryHistoryTests: XCTestCase {

    private func suitcaseGraph(_ dates: [Date?]) -> MemoryGraph {
        var g = MemoryGraph()
        let e = Evidence(signal: "scene_labels", tier: .visual, weight: 0.7,
                         reason: "a suitcase was recognised")!
        g.add(Entity(entityID: "object:suitcase", kind: .object,
                     name: "Suitcase", evidence: [e])!)
        for (i, when) in dates.enumerated() {
            g.observe(Observation(entityID: "object:suitcase", assetID: "a\(i)",
                                  when: when, place: nil, confidence: 0.7, reason: "seen"))
        }
        return g
    }

    func testHistoryIsOldestFirstAndUndatedSightingsSurvive() {
        let g = suitcaseGraph([date(2025, 5, 1), nil, date(2024, 1, 1)])
        let history = g.history(of: "object:suitcase")
        XCTAssertEqual(3, history.count, "an undated sighting is still a sighting")
        XCTAssertEqual(date(2024, 1, 1), history.first?.when)
        XCTAssertNil(history.last?.when)
    }

    func testAnEntityWithNoDatedSightingHasNoLast() {
        let g = suitcaseGraph([nil])
        XCTAssertNil(g.lastSeen("object:suitcase"))
        XCTAssertTrue(g.answerWhereLastSeen("suitcase").contains("no “last”"))
    }
}

/// Two photos of one thing in one moment say one thing twice. Two photos of one thing
/// on two days say two things — and collapsing those would delete the only information
/// the memory exists to hold.
final class MemoryRepeatTests: XCTestCase {

    func testARepeatWithinAMomentIsFlaggedAndNothingIsDropped() {
        let base = date(2025, 6, 18)
        let g = graph(of: [
            asset("card-a", base) { $0.ocrRan = true; $0.ocrText = "ID CARD" },
            asset("card-b", base.addingTimeInterval(3)) {
                $0.ocrRan = true; $0.ocrText = "ID CARD"
            },
        ], momentGroups: [["card-a", "card-b"]])

        XCTAssertEqual(Set(["card-a", "card-b"]), Set(g.observations.map { $0.assetID }),
                       "no sighting is dropped — a flag is not a deletion")
        let repeats = g.observations.filter { $0.repeatsAsset != nil }
        XCTAssertFalse(repeats.isEmpty)
        XCTAssertTrue(repeats.allSatisfy { $0.assetID == "card-b" },
                      "the earliest member is the anchor, not a repeat of itself")
        XCTAssertTrue(repeats.allSatisfy { $0.repeatsAsset == "card-a" })
    }

    func testTwoOccasionsAreTwoSightingsNotARepeat() {
        let g = graph(of: [
            asset("a1", date(2025, 8, 3)) {
                $0.geo = london; $0.place = uk
                $0.faceClusters = [FaceCluster(clusterID: "c-anna", name: "Anna")]
            },
            asset("a2", date(2025, 8, 11)) {
                $0.geo = tokyo; $0.place = japan
                $0.faceClusters = [FaceCluster(clusterID: "c-anna", name: "Anna")]
            },
        ])
        let history = g.history(of: "person:anna")
        XCTAssertEqual(2, history.count)
        XCTAssertTrue(history.allSatisfy { $0.repeatsAsset == nil })
        XCTAssertTrue(g.answerWhereLastSeen("Anna").contains("Tokyo"))
    }
}

/// L1-B §4: what a video must leave behind is *"这个视频对用户个人视觉记忆真正贡献的新
/// 信息"* — Date / Place / Person / Object / Event / segment / representative frames.
final class VideoMemoryRecordTests: XCTestCase {

    private func video() -> AssetSignals {
        asset("v", date(2025, 4, 12, 9)) {
            $0.geo = tokyo; $0.place = japan
            $0.isVideo = true; $0.durationSeconds = 60
            $0.faceClusters = [FaceCluster(clusterID: "c-anna", name: "Anna")]
        }
    }

    func testRunsOfKeyframesBecomeSegmentsNotTimestamps() {
        let record = VideoMemory.record(asset: video(), keyframes: [0, 1, 2, 90, 91],
                                        frameRate: 30)
        XCTAssertEqual(2, record.segments.count,
                       "two things happened, not five frames were interesting")
        XCTAssertEqual(0.0, record.segments[0].lowerBound, accuracy: 1e-9)
        XCTAssertEqual(2.0 / 30.0, record.segments[0].upperBound, accuracy: 1e-9)
        XCTAssertEqual(3.0, record.segments[1].lowerBound, accuracy: 1e-9)
        XCTAssertEqual(91.0 / 30.0, record.segments[1].upperBound, accuracy: 1e-9)
    }

    func testASingleKeyframeIsAZeroLengthSegmentNotACrash() {
        let record = VideoMemory.record(asset: video(), keyframes: [45], frameRate: 30)
        XCTAssertEqual(1, record.segments.count)
        XCTAssertEqual(1.5, record.segments[0].lowerBound, accuracy: 1e-9)
        XCTAssertEqual(1.5, record.segments[0].upperBound, accuracy: 1e-9)
    }

    func testNoKeyframesMeansNoSegments() {
        let record = VideoMemory.record(asset: video(), keyframes: [], frameRate: 30)
        XCTAssertTrue(record.segments.isEmpty)
        XCTAssertTrue(record.representativeFrames.isEmpty)
    }

    func testTheRecordCarriesEveryFieldL1BAsksFor() {
        let context = LibraryContextBuilder.build([video()])
        let record = VideoMemory.record(asset: video(), keyframes: [0, 1, 2],
                                        frameRate: 30, context: context)
        let summary = record.summary
        for field in ["Date:", "Place:", "Person:", "Representative frames:"] {
            XCTAssertTrue(summary.contains(field), "missing \(field) in:\n\(summary)")
        }
        XCTAssertTrue(summary.contains("Anna"))
        XCTAssertTrue(summary.contains("Tokyo"))
    }

    func testTheRecordSaysHowMuchOfTheVideoItSkipped() {
        let record = VideoMemory.record(asset: video(), keyframes: [0, 1, 2], frameRate: 30)
        XCTAssertFalse(record.evidence.isEmpty)
        XCTAssertTrue(record.evidence[0].reason.contains("repeated"),
                      "the saving is part of the record, not a hidden optimisation")
    }
}

final class MemoryDeterminismTests: XCTestCase {

    func testBuildingTheSameLibraryTwiceGivesTheSameMemory() {
        let assets = FixtureLibrary.make()
        let first = graph(of: assets), second = graph(of: assets)
        XCTAssertEqual(first.stats, second.stats)
        XCTAssertEqual(first.entities.keys.sorted(), second.entities.keys.sorted())
    }
}
