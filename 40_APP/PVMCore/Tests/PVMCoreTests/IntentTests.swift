import XCTest
@testable import PVMCore

/// Tests for Intent Search — §10's third retrieval path.
/// Ported from `30_ENGINE/tests/test_intent.py`.
///
/// The Constitution gives two worked examples and they are not the same problem:
///
///     Intent Search：用户直接说“找我的身份证正反面”“找所有有气球的照片”。
///
/// The first the library can answer. The second it cannot — 气球 is not a label
/// anything in this build produces — and **that is the case these tests are mostly
/// about.** A search that silently returns everything, or silently returns nothing,
/// turns a missing capability into a false statement about the user's own photos.
final class IntentTests: XCTestCase {

    private var directory: URL!
    private var catalog: Catalog!

    override func setUpWithError() throws {
        directory = URL(fileURLWithPath: NSTemporaryDirectory())
            .appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        catalog = try XCTUnwrap(Catalog(path: directory.appendingPathComponent("c.sqlite").path))
        _ = Pipeline.run(assets: FixtureLibrary.make(), catalog: catalog)
    }

    override func tearDownWithError() throws {
        catalog = nil
        try? FileManager.default.removeItem(at: directory)
    }

    // MARK: - 找我的身份证正反面 — the one it can answer

    func testItResolvesTheCategoryAndTheAspect() {
        let q = Intent.parse("找我的身份证正反面")
        XCTAssertTrue(q.paths.contains("Documents > Identity > ID Cards"))
        XCTAssertTrue(q.wantsMultipleSides)
        XCTAssertEqual([], q.unresolved)
    }

    func testTheEnglishFormResolvesTheSameWay() {
        let q = Intent.parse("find the front and back of my id card")
        XCTAssertTrue(q.paths.contains("Documents > Identity > ID Cards"))
        XCTAssertTrue(q.wantsMultipleSides)
    }

    func testItFindsTheIDCard() {
        let results = Intent.search(catalog, "找我的身份证正反面")
        XCTAssertFalse(results.hits.isEmpty)
        XCTAssertTrue(results.hits.allSatisfy { $0.why.contains("ID Cards") })
    }

    // MARK: - 找所有有气球的照片 — the one it cannot, and must not pretend to

    func testTheUnsearchableTermIsNamed() {
        let q = Intent.parse("找所有有气球的照片")
        XCTAssertTrue(q.unresolved.contains("气球"),
                      "Chinese runs together; a matched sub-phrase used to swallow the "
                      + "whole sentence and the balloon was never reported at all")
    }

    func testItRefusesRatherThanReturningTheWholeLibrary() {
        let results = Intent.search(catalog, "找所有有气球的照片")
        XCTAssertTrue(results.hits.isEmpty,
                      "“照片” alone resolves to every image, so answering broadly would "
                      + "present the entire library as the answer to a question about "
                      + "balloons")
        XCTAssertTrue(results.summary.contains("cannot search for"))
        XCTAssertTrue(results.summary.contains("气球"))
    }

    func testTheRefusalSaysItIsAboutTheSearchNotThePhotos() {
        XCTAssertTrue(Intent.search(catalog, "找所有有气球的照片").summary
            .contains("not a statement about your photos"))
    }

    func testAMediaTypeAloneDoesNotCountAsNarrowing() {
        let q = Intent.parse("找所有有气球的照片")
        XCTAssertEqual("image", q.mediaType)
        XCTAssertFalse(q.narrows)
        XCTAssertFalse(q.answerable)
    }

    func testAPartlyUnderstoodQueryStillAnswersAndStillWarns() {
        let results = Intent.search(catalog, "找 Anna 的气球照片")
        XCTAssertFalse(results.hits.isEmpty, "Anna is indexed, so the query narrows")
        XCTAssertTrue(results.summary.contains("气球"))
        XCTAssertTrue(results.summary.contains("Anna"))
    }

    // MARK: - it searches the user's own library

    func testPeopleComeFromTheStoredMemory() {
        let results = Intent.search(catalog, "Anna")
        XCTAssertFalse(results.hits.isEmpty)
        XCTAssertTrue(results.query.people.contains("Anna"))
    }

    /// "Anna in Tokyo" means both. A single list over people and places meant either,
    /// and answered a one-photo question with nineteen.
    func testTwoKindsOfConstraintIntersectRatherThanUnion() {
        let both = Intent.search(catalog, "Anna in Tokyo")
        let anna = Intent.search(catalog, "Anna")
        XCTAssertTrue(both.query.people.contains("Anna"))
        XCTAssertTrue(both.query.places.contains("Tokyo"))
        XCTAssertLessThan(both.hits.count, anna.hits.count,
                          "adding a place must narrow, never widen")
    }

    /// Counting (asset, path) rows made a seven-photo answer announce itself as fifty.
    func testOneAssetOnThreeShelvesIsOneResult() {
        let ids = Intent.search(catalog, "找 Anna 的照片").hits.map { $0.assetID }
        XCTAssertEqual(ids.count, Set(ids).count)
    }

    // MARK: - time is an exact window or no window

    func testAYearNarrows() {
        let all = Intent.search(catalog, "截图")
        let in2026 = Intent.search(catalog, "2026 年的截图")
        XCTAssertEqual(2026, in2026.query.year)
        XCTAssertLessThan(in2026.hits.count, all.hits.count)
    }

    /// `created_at` is stored as epoch seconds. Comparing it as text matches nothing,
    /// silently.
    func testAYearIsARangeNotAStringPrefix() {
        XCTAssertFalse(Intent.search(catalog, "screenshots 2026").hits.isEmpty)
    }

    func testAVagueTimeIsNotGuessedIntoAWindow() {
        let q = Intent.parse("最近拍的护照")
        XCTAssertNil(q.year)
        XCTAssertTrue(q.paths.contains("Documents > Identity > Passports"))
    }

    // MARK: - noise is not reported as a missing capability

    func testFillerWordsAreNotUnresolvedTerms() {
        XCTAssertEqual([], Intent.parse("show me all my receipts from 2026").unresolved,
                       "reporting “from” as unsearchable is noise that discredits the "
                       + "real cases")
    }

    func testAPluralLeftoverIsNotATerm() {
        XCTAssertEqual([], Intent.parse("my passports").unresolved,
                       "consuming “passport” out of “passports” leaves an “s”")
    }

    /// The vocabulary is generated from the engine for the same reason the scene map
    /// is: a search that recognises 身份证 on one side and not the other is two
    /// products, and nobody would notice until a user typed it into the wrong one.
    func testTheVocabularyIsShared() {
        XCTAssertEqual("Documents > Identity > ID Cards", Rules.categoryWords["身份证"])
        XCTAssertEqual("Documents > Identity > ID Cards", Rules.categoryWords["id card"])
        XCTAssertFalse(Rules.searchFillerCJK.isEmpty)
    }
}
