import XCTest
@testable import PVMCore

/// Migration tests, written against databases in genuinely OLD SHAPES.
///
/// The first version of these tests took a current database, wrote an older number
/// into `schema_version`, and migrated that. A second audit on 2026-09-12 pointed out
/// that this proves only that the version arithmetic runs: the table being migrated
/// already had every column the new build wanted, so "the migration worked" and "the
/// migration did nothing" produced identical results.
///
/// So the fixtures here are built by taking the current schema apart — dropping
/// `assets` and recreating it without the columns that were added later, and in the
/// worst case dropping `meta` so no version is recorded at all, which is the state of
/// every catalogue written by a Swift build before 2026-09-11. The assertion that
/// matters is not a version number: it is that **a write naming a new column
/// succeeds afterwards**, because failing that write is the actual crash.
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

    /// The `assets` table as an earlier build wrote it: no `media_type` (added with
    /// video), no `importance`, `asset_class` or `importance_why` (added with the
    /// Importance axis). Everything else the same.
    private static let legacyAssets = """
        CREATE TABLE assets(
          asset_id TEXT PRIMARY KEY,
          signals_fp TEXT NOT NULL,
          engine_fp TEXT NOT NULL,
          created_at REAL,
          content_hash TEXT,
          dhash INTEGER,
          tier_used INTEGER,
          risk INTEGER,
          needs_review INTEGER,
          notes TEXT,
          classified_at REAL
        );
        CREATE INDEX idx_assets_risk ON assets(risk);
        INSERT INTO assets(asset_id, signals_fp, engine_fp) VALUES('A1','fp','swift-0');
        """

    /// Builds a real old-shaped file and returns a freshly opened handle to it — what
    /// the app sees on the first launch after the update.
    ///
    /// `version` nil means no `meta` table at all, which is the unversioned legacy
    /// case and the one that used to look identical to a brand-new database.
    private func makeLegacyFile(version: Int?) throws -> Catalog {
        do {
            let seed = try XCTUnwrap(Catalog(path: path))
            seed.recordDecision(assetID: "A1", path: "/文档", verb: .keep)
            seed.writeEntityReview([("A1", "A2", "too close to call")])
            seed.checkpoint("A1")
            seed.setMeta("pref.tone", "quiet")

            seed.exec("DROP TABLE assets;")
            seed.exec(Self.legacyAssets)
            if let version {
                seed.setMeta("schema_version", String(version))
            } else {
                seed.exec("DROP TABLE meta;")
            }
            seed.commit()
        }
        return try XCTUnwrap(Catalog(path: path))
    }

    /// A file in THIS build's shape carrying a LATER version number — a TestFlight
    /// downgrade, or a restore from a newer backup. Separate from the legacy fixture
    /// on purpose: a genuinely newer file has every column this build knows and more,
    /// so the thing being tested is the refusal, not a missing column.
    private func makeFileFromTheFuture() throws -> Catalog {
        do {
            let seed = try XCTUnwrap(Catalog(path: path))
            seed.exec("INSERT INTO assets(asset_id,signals_fp,engine_fp) VALUES('A1','fp','swift-9');")
            seed.setMeta("schema_version", String(Catalog.schemaVersion + 1))
            seed.commit()
        }
        return try XCTUnwrap(Catalog(path: path))
    }

    /// The write that fails on an un-migrated old file, and is the whole point.
    private func writeNamingTheNewColumns(_ catalog: Catalog) -> Bool {
        catalog.exec("""
            INSERT INTO assets(asset_id, signals_fp, engine_fp, asset_class, media_type, importance)
            VALUES('B1','fp','swift-1','document','image',3);
            """)
    }

    // MARK: - nothing to do

    func testAFreshFileNeedsNothing() throws {
        let catalog = try XCTUnwrap(Catalog(path: path))
        XCTAssertEqual(catalog.openedSchemaVersion, 0)
        XCTAssertFalse(catalog.isUnversionedLegacyFile)
        XCTAssertFalse(catalog.needsMigration)
        XCTAssertEqual(catalog.migrationPlan, .fresh)
        XCTAssertTrue(catalog.missingColumns().isEmpty)
    }

    func testAFileFromThisBuildNeedsNothing() throws {
        _ = try XCTUnwrap(Catalog(path: path))
        let second = try XCTUnwrap(Catalog(path: path))
        XCTAssertEqual(second.openedSchemaVersion, Catalog.schemaVersion)
        XCTAssertEqual(second.migrationPlan, .current)
    }

    // MARK: - the unversioned legacy file

    /// The defect the second audit found. `createSchema()` manufactures `meta`, so
    /// reading the version afterwards reported 0 — the same value a brand-new file
    /// reports — and an old database was stamped current and never migrated.
    func testAnUnversionedOldFileIsNotMistakenForANewOne() throws {
        let legacy = try makeLegacyFile(version: nil)
        XCTAssertTrue(legacy.isUnversionedLegacyFile)
        XCTAssertTrue(legacy.needsMigration)
        XCTAssertEqual(legacy.migrationPlan, .unversionedLegacy)
        XCTAssertNotEqual(legacy.migrationPlan, .fresh)
        XCTAssertFalse(legacy.missingColumns().isEmpty,
                       "the file really is missing columns this build writes")
    }

    /// The assertion that the version arithmetic cannot fake.
    func testMigratingAnUnversionedOldFileMakesTheNewColumnsWritable() throws {
        let legacy = try makeLegacyFile(version: nil)
        XCTAssertFalse(writeNamingTheNewColumns(legacy),
                       "precondition: this write must fail before the migration")

        let outcome = legacy.migrate()
        XCTAssertEqual(outcome.plan, .unversionedLegacy)
        XCTAssertTrue(outcome.succeeded, "\(outcome.missingColumns) / \(outcome.integrity)")
        XCTAssertTrue(outcome.missingColumns.isEmpty)
        XCTAssertTrue(writeNamingTheNewColumns(legacy),
                      "a migration that leaves the old columns in place did nothing")
    }

    func testMigrationKeepsWhatTheUserSaidAndDropsWhatCanBeRecomputed() throws {
        let legacy = try makeLegacyFile(version: nil)
        let outcome = legacy.migrate()

        XCTAssertEqual(outcome.decisionsKept, 1, "§14: the Personal Policy's evidence")
        XCTAssertEqual(outcome.entityReviewKept, 1, "§24 Gate 2's open questions")
        XCTAssertEqual(legacy.decisions().count, 1)
        XCTAssertEqual(legacy.decisions().first?.path, "/文档",
                       "the carried-across row must keep its columns, not its fallbacks")
        XCTAssertEqual(legacy.entityReviewQueue().count, 1)
        XCTAssertEqual(legacy.meta("pref.tone"), "quiet", "a setting is not engine state")

        XCTAssertEqual(legacy.scalar("SELECT COUNT(*) FROM assets;"), 0)
        XCTAssertEqual(outcome.derivedRowsCleared, 1)
        XCTAssertNil(legacy.cursor, "a resume point into rows that no longer exist")
        XCTAssertEqual(legacy.meta("schema_version"), String(Catalog.schemaVersion))
    }

    /// Renaming a table takes its indexes with it, so the first `createSchema()` call
    /// found `idx_decisions_path` already taken and skipped it. Without the second
    /// call the rebuilt table would come out unindexed and nothing would say so.
    func testTheRebuiltTablesKeepTheirIndexes() throws {
        let legacy = try makeLegacyFile(version: nil)
        _ = legacy.migrate()
        for index in ["idx_decisions_path", "idx_assets_risk", "idx_assign_path"] {
            XCTAssertEqual(
                legacy.scalar("SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name='\(index)';"),
                1, "\(index) did not survive the rebuild")
        }
    }

    // MARK: - the versioned old file

    func testAVersionedOldFileIsAlsoRebuiltStructurally() throws {
        let legacy = try makeLegacyFile(version: Catalog.schemaVersion - 1)
        XCTAssertEqual(legacy.migrationPlan, .rebuildDerived(from: Catalog.schemaVersion - 1))
        XCTAssertFalse(writeNamingTheNewColumns(legacy))

        let outcome = legacy.migrate()
        XCTAssertTrue(outcome.succeeded)
        XCTAssertTrue(writeNamingTheNewColumns(legacy))
        XCTAssertEqual(outcome.decisionsKept, 1)
    }

    /// Simulate the kill: drop the handle without migrating, then open again.
    func testAMigrationInterruptedBeforeItRanIsStillPending() throws {
        _ = try makeLegacyFile(version: Catalog.schemaVersion - 1)
        let afterKill = try XCTUnwrap(Catalog(path: path))
        XCTAssertTrue(afterKill.needsMigration, "the migration must still be pending")
        XCTAssertEqual(afterKill.meta("schema_version"), String(Catalog.schemaVersion - 1))
    }

    /// Kill it in the middle instead: migrate, then open a second handle and migrate
    /// again. The second pass must be a no-op rather than a second rebuild.
    func testMigrationIsIdempotentAcrossRestarts() throws {
        let first = try makeLegacyFile(version: nil)
        _ = first.migrate()

        let second = try XCTUnwrap(Catalog(path: path))
        XCTAssertEqual(second.migrationPlan, .current)
        let outcome = second.migrate()
        XCTAssertEqual(outcome.derivedRowsCleared, 0)
        XCTAssertTrue(outcome.tablesRebuilt.isEmpty)
        XCTAssertEqual(outcome.decisionsKept, 1)
        XCTAssertTrue(outcome.succeeded)
    }

    // MARK: - the downgrade

    func testAFileFromANewerBuildIsNotMigrated() throws {
        let future = try makeFileFromTheFuture()
        XCTAssertTrue(future.isFromANewerBuild)
        XCTAssertFalse(future.isUnversionedLegacyFile)
        XCTAssertEqual(future.migrationPlan, .newerThanThisBuild(Catalog.schemaVersion + 1))

        let outcome = future.migrate()
        XCTAssertTrue(outcome.tablesRebuilt.isEmpty)
        XCTAssertEqual(future.scalar("SELECT COUNT(*) FROM assets;"), 1,
                       "a newer file must come through untouched")
        XCTAssertEqual(future.meta("schema_version"), String(Catalog.schemaVersion + 1),
                       "and its version stamp must not be overwritten by an older build")
    }

    func testQuarantineMovesTheFileAndItsSiblingsAside() throws {
        _ = try makeFileFromTheFuture()
        let moved = try XCTUnwrap(Catalog.quarantine(path: path))
        XCTAssertFalse(FileManager.default.fileExists(atPath: path))
        XCTAssertTrue(FileManager.default.fileExists(atPath: moved))
        for sibling in ["-wal", "-shm"] {
            XCTAssertFalse(FileManager.default.fileExists(atPath: path + sibling),
                           "a newer write-ahead log must not attach to a fresh database")
        }
        let replacement = try XCTUnwrap(Catalog(path: path))
        XCTAssertEqual(replacement.openedSchemaVersion, 0)
        XCTAssertFalse(replacement.isUnversionedLegacyFile)
    }

    func testQuarantineOfAMissingFileIsNotAnError() {
        XCTAssertNil(Catalog.quarantine(path: directory.appendingPathComponent("nope").path))
    }

    func testIntegrityCheckReportsOkOnAHealthyFile() throws {
        let catalog = try XCTUnwrap(Catalog(path: path))
        XCTAssertEqual(catalog.integrityCheck(), "ok")
    }
}
