import XCTest
@testable import PVMCore

/// A migration is only testable if you can make an old file, and the only honest way
/// to make one is to write the old stamp into a real database and reopen it. These
/// tests do that rather than testing `plan()` in isolation, because every bug this
/// code exists for lives in the open/stamp/migrate ordering, not in the arithmetic.
final class MigrationTests: XCTestCase {

    private var directory: URL!
    private var path: String!

    override func setUpWithError() throws {
        directory = URL(fileURLWithPath: NSTemporaryDirectory())
            .appendingPathComponent("pvm-migration-" + UUID().uuidString)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        path = directory.appendingPathComponent("c.sqlite").path
    }

    override func tearDownWithError() throws {
        try? FileManager.default.removeItem(at: directory)
    }

    /// Writes a database, stamps it with `version`, and returns a freshly opened
    /// handle — i.e. what the app sees on the launch after an update.
    private func reopen(stampedAs version: Int) throws -> Catalog {
        let seed = try XCTUnwrap(Catalog(path: path))
        seed.recordDecision(assetID: "A1", path: "/文档", verb: .keep)
        seed.writeEntityReview([("A1", "A2", "too close to call")])
        seed.exec("INSERT OR REPLACE INTO assets(asset_id, signals_fp, engine_fp) "
                  + "VALUES('A1','fp','swift-1');")
        seed.checkpoint("A1")
        seed.setMeta("schema_version", String(version))
        seed.setMeta("pref.tone", "quiet")
        seed.commit()
        return try XCTUnwrap(Catalog(path: path))
    }

    func testAFreshFileNeedsNothing() throws {
        let catalog = try XCTUnwrap(Catalog(path: path))
        XCTAssertEqual(catalog.openedSchemaVersion, 0)
        XCTAssertFalse(catalog.needsMigration)
        XCTAssertEqual(catalog.migrationPlan, .fresh)
        XCTAssertFalse(catalog.migrationPlan.needsWork)
    }

    func testAFileFromThisBuildNeedsNothing() throws {
        _ = try XCTUnwrap(Catalog(path: path))
        let second = try XCTUnwrap(Catalog(path: path))
        XCTAssertEqual(second.openedSchemaVersion, Catalog.schemaVersion)
        XCTAssertEqual(second.migrationPlan, .current)
    }

    /// The bug this file was written for. Opening an old database used to stamp it
    /// "current" immediately, so a kill before the migration ran left a file that
    /// claimed to be the new shape while still being the old one — unrecoverable,
    /// because the evidence of the old version was the thing that got overwritten.
    func testOpeningAnOldFileDoesNotClaimItIsCurrent() throws {
        let old = try reopen(stampedAs: Catalog.schemaVersion - 1)
        XCTAssertTrue(old.needsMigration)
        XCTAssertEqual(old.meta("schema_version"), String(Catalog.schemaVersion - 1))

        // Simulate the kill: drop the handle without migrating, open again.
        let afterKill = try XCTUnwrap(Catalog(path: path))
        XCTAssertTrue(afterKill.needsMigration, "the migration must still be pending")
        XCTAssertEqual(afterKill.migrationPlan, .rebuildDerived(from: Catalog.schemaVersion - 1))
    }

    func testMigrationClearsDerivedRowsAndKeepsWhatTheUserSaid() throws {
        let catalog = try reopen(stampedAs: Catalog.schemaVersion - 1)
        let outcome = catalog.migrate()

        XCTAssertEqual(outcome.plan, .rebuildDerived(from: Catalog.schemaVersion - 1))
        XCTAssertTrue(outcome.succeeded)
        XCTAssertEqual(outcome.decisionsKept, 1)
        XCTAssertEqual(outcome.entityReviewKept, 1)
        XCTAssertEqual(outcome.derivedRowsCleared, 1)

        XCTAssertEqual(catalog.scalar("SELECT COUNT(*) FROM assets;"), 0)
        XCTAssertEqual(catalog.decisions().count, 1, "§14: the Personal Policy's evidence")
        XCTAssertEqual(catalog.entityReviewQueue().count, 1, "§24 Gate 2's open questions")
        XCTAssertEqual(catalog.meta("pref.tone"), "quiet", "a setting is not engine state")
        XCTAssertNil(catalog.cursor, "a resume point into rows that no longer exist")
        XCTAssertEqual(catalog.meta("schema_version"), String(Catalog.schemaVersion))
    }

    func testMigrationIsIdempotent() throws {
        let catalog = try reopen(stampedAs: Catalog.schemaVersion - 1)
        _ = catalog.migrate()
        let second = catalog.migrate()
        XCTAssertEqual(second.derivedRowsCleared, 0)
        XCTAssertEqual(second.decisionsKept, 1)
    }

    /// A downgrade — TestFlight, or a restore from a newer backup. This build does not
    /// know what the newer shape means, so the only correct behaviours are "refuse"
    /// and "set aside". Guessing is not on the list.
    func testAFileFromANewerBuildIsNotMigrated() throws {
        let future = try reopen(stampedAs: Catalog.schemaVersion + 1)
        XCTAssertTrue(future.isFromANewerBuild)
        XCTAssertFalse(future.needsMigration)
        XCTAssertEqual(future.migrationPlan, .newerThanThisBuild(Catalog.schemaVersion + 1))

        let outcome = future.migrate()
        XCTAssertEqual(outcome.derivedRowsCleared, 0)
        XCTAssertEqual(future.scalar("SELECT COUNT(*) FROM assets;"), 1,
                       "a newer file must come through untouched")
    }

    func testQuarantineMovesTheFileAndItsSiblingsAside() throws {
        _ = try reopen(stampedAs: Catalog.schemaVersion + 1)
        let moved = try XCTUnwrap(Catalog.quarantine(path: path))
        XCTAssertFalse(FileManager.default.fileExists(atPath: path))
        XCTAssertTrue(FileManager.default.fileExists(atPath: moved))
        for sibling in ["-wal", "-shm"] {
            XCTAssertFalse(FileManager.default.fileExists(atPath: path + sibling),
                           "a newer write-ahead log must not attach to a fresh database")
        }

        let replacement = try XCTUnwrap(Catalog(path: path))
        XCTAssertEqual(replacement.openedSchemaVersion, 0)
    }

    func testQuarantineOfAMissingFileIsNotAnError() {
        XCTAssertNil(Catalog.quarantine(path: directory.appendingPathComponent("nope").path))
    }

    func testIntegrityCheckReportsOkOnAHealthyFile() throws {
        let catalog = try XCTUnwrap(Catalog(path: path))
        XCTAssertEqual(catalog.integrityCheck(), "ok")
    }
}
