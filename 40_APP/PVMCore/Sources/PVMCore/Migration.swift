import Foundation

/// WHAT SURVIVES AN UPGRADE, AND WHY THAT IS A SHORT LIST.
///
/// Most apps migrate a database because the database is the only copy of the user's
/// data. This one is the opposite case and the design follows from it:
///
///  * **Almost every row is derived.** `assets`, `assignments`, `evidence`,
///    `relations`, `proposals`, `entities`, `observations`, `video_records` are all
///    recomputed from the photo library by the same deterministic engine. Throwing
///    them away costs an indexing pass and nothing else.
///  * **Two tables are not.** `decisions` is the user's Keep/Delete/Protect/Restore
///    log — §14 says the Personal Policy is *derived from* it, so the log is the
///    durable thing and losing it silently rewrites who the system thinks the user is.
///    `entity_review` is the set of questions the system has already decided to ask
///    (§24 Gate 2); dropping it re-asks questions the user may have already answered.
///  * **User preferences are not.** Any `meta` key under the `pref.` prefix is
///    something the user set, not something the engine computed.
///
/// So the policy is: **recreate the derived half at this build's shape, carry the
/// authored half across, never copy the file.** A file copy on a phone with a
/// 100k-asset catalogue costs storage the user may not have, to protect data that can
/// be recomputed for free.
///
/// ## The defect this file was rewritten for
///
/// The first version of this migration deleted rows and moved the version stamp. A
/// second audit on 2026-09-12 pointed out that this cannot work, and it is right:
/// **`DELETE FROM assets` does not add a missing column.** The failure a migration
/// exists to prevent is a schema change — a new column, a new index, a changed
/// constraint — and clearing rows leaves every one of those exactly as it was. An old
/// file would come through "migrated", empty, and still the wrong shape, failing at
/// the first insert that named the new column.
///
/// What actually fixes a changed shape is dropping the table and letting
/// `createSchema()` build it again. That is available here, and is not available to
/// most apps, for the same reason the rest of this file is short: the derived tables
/// hold nothing that cannot be recomputed. The authored tables cannot be dropped and
/// are carried across column by column instead — see `rescue`.
public enum CatalogMigration {

    /// Tables whose every row can be recomputed from the photo library. Dropped and
    /// rebuilt, so a column, index or constraint change in any of them is handled.
    public static let derivedTables = [
        "assets", "assignments", "evidence", "relations", "proposals",
        "entities", "observations", "video_records",
    ]

    /// Tables holding something the user said, and the columns this build needs from
    /// them. Each column carries the SQL literal to use when the OLD table does not
    /// have it — required because these columns are `NOT NULL` with no default, so a
    /// straight `INSERT … SELECT` over a missing column fails the whole migration.
    public static let authoredTables: [(name: String, columns: [(String, fallback: String)])] = [
        ("decisions", [("asset_id", "''"), ("path", "''"),
                       ("action", "'keep'"), ("decided_at", "0.0")]),
        ("entity_review", [("asset_a", "''"), ("asset_b", "''"),
                           ("reason", "'carried across a schema upgrade'")]),
    ]

    /// `meta` keys that are settings rather than engine state. Survive untouched.
    public static let preferenceKeyPrefix = "pref."

    /// The columns `upsert` names. These are the ones whose absence is the actual
    /// crash — "table assets has no column named asset_class" at the first write after
    /// an update — so a migration that claims to have succeeded is checked against
    /// them rather than against its own version stamp.
    public static let requiredColumns: [String: [String]] = [
        "assets": ["asset_id", "signals_fp", "engine_fp", "created_at", "content_hash",
                   "dhash", "media_type", "tier_used", "risk", "importance",
                   "asset_class", "importance_why", "needs_review", "notes",
                   "classified_at"],
        "assignments": ["asset_id", "path", "confidence", "is_primary", "cross_listed_from"],
        "observations": ["entity_id", "asset_id", "seen_at", "place", "confidence",
                         "reason", "source", "place_source", "repeats"],
        "decisions": ["asset_id", "path", "action", "decided_at"],
        "entity_review": ["asset_a", "asset_b", "reason"],
    ]

    public enum Plan: Equatable {
        /// The file did not exist. Nothing to do.
        case fresh
        /// Written by this build. Nothing to do.
        case current
        /// Older, and it says so. Derived tables rebuilt; authored rows carried across.
        case rebuildDerived(from: Int)
        /// Pre-existing tables, no version recorded — every catalogue written by a
        /// Swift build before 2026-09-11. Treated as older than everything, because
        /// that is what it is.
        case unversionedLegacy
        /// Newer. This build cannot read the shape and will not guess at it.
        case newerThanThisBuild(Int)

        public var needsWork: Bool {
            switch self {
            case .fresh, .current: return false
            case .rebuildDerived, .unversionedLegacy, .newerThanThisBuild: return true
            }
        }

        /// Whether this plan rebuilds. `newerThanThisBuild` needs work and is not it.
        var rebuilds: Bool {
            switch self {
            case .rebuildDerived, .unversionedLegacy: return true
            default: return false
            }
        }
    }

    public static func plan(openedVersion: Int,
                            unversionedLegacy: Bool = false,
                            buildVersion: Int = Catalog.schemaVersion) -> Plan {
        if unversionedLegacy { return .unversionedLegacy }
        if openedVersion == 0 { return .fresh }
        if openedVersion == buildVersion { return .current }
        if openedVersion > buildVersion { return .newerThanThisBuild(openedVersion) }
        return .rebuildDerived(from: openedVersion)
    }

    /// What a migration actually did, so the app can say it rather than imply it.
    public struct Outcome: Equatable {
        public let plan: Plan
        public let decisionsKept: Int
        public let entityReviewKept: Int
        public let derivedRowsCleared: Int
        /// Tables whose structure was actually rebuilt. Empty when nothing was done.
        public let tablesRebuilt: [String]
        /// Columns this build writes that the file still does not have, as
        /// `table.column`. A migration that leaves this non-empty did not work,
        /// whatever its version stamp says.
        public let missingColumns: [String]
        public let integrity: String

        public var succeeded: Bool {
            missingColumns.isEmpty && (integrity == "ok" || integrity == "unavailable")
        }
    }
}

extension Catalog {

    public var migrationPlan: CatalogMigration.Plan {
        CatalogMigration.plan(openedVersion: openedSchemaVersion,
                              unversionedLegacy: isUnversionedLegacyFile)
    }

    /// The columns a table actually has on disk, which is the only thing that decides
    /// whether a migration can read it.
    public func columnNames(of table: String) -> Set<String> {
        var out: Set<String> = []
        var st: OpaquePointer?
        // `PRAGMA table_info` takes no bound parameters, and the table names here are
        // compile-time constants from `CatalogMigration`, never user input.
        sqlite3_prepare_v2(db, "PRAGMA table_info(\(table));", -1, &st, nil)
        while sqlite3_step(st) == SQLITE_ROW {
            if let c = sqlite3_column_text(st, 1) { out.insert(String(cString: c)) }
        }
        sqlite3_finalize(st)
        return out
    }

    func tableExists(_ table: String) -> Bool {
        !columnNames(of: table).isEmpty
    }

    /// Columns this build writes that the file does not have, as `table.column`.
    ///
    /// This is the check the first migration was missing. It asks the FILE what shape
    /// it is, rather than asking the version stamp what shape it claims to be, and
    /// those are exactly the two things a broken migration makes disagree.
    public func missingColumns() -> [String] {
        var out: [String] = []
        for (table, required) in CatalogMigration.requiredColumns.sorted(by: { $0.key < $1.key }) {
            let present = columnNames(of: table)
            guard !present.isEmpty else { out.append("\(table).*"); continue }
            for column in required where !present.contains(column) {
                out.append("\(table).\(column)")
            }
        }
        return out
    }

    /// Bring the file to this build's shape. Safe to call on every launch: when there
    /// is nothing to do it reads two counts and returns.
    ///
    /// The ordering matters and is the whole point. Every drop, recreate and carry-over
    /// happens inside one transaction, and the version stamp moves **after** the work
    /// and **inside the same transaction**. A kill at any moment leaves the file either
    /// entirely un-migrated (and still marked as such, so the next launch retries) or
    /// entirely migrated. There is no state where the stamp says one thing and the
    /// tables say another — which is the state the first version of this code could
    /// produce and the reason it was rewritten.
    @discardableResult
    public func migrate() -> CatalogMigration.Outcome {
        let plan = migrationPlan
        let kept = (scalar("SELECT COUNT(*) FROM decisions;"),
                    scalar("SELECT COUNT(*) FROM entity_review;"))

        guard plan.rebuilds else {
            return CatalogMigration.Outcome(plan: plan,
                                            decisionsKept: kept.0,
                                            entityReviewKept: kept.1,
                                            derivedRowsCleared: 0,
                                            tablesRebuilt: [],
                                            missingColumns: missingColumns(),
                                            integrity: plan == .fresh ? "ok" : integrityCheck())
        }

        var cleared = 0
        for table in CatalogMigration.derivedTables where tableExists(table) {
            cleared += scalar("SELECT COUNT(*) FROM \(table);")
        }

        // Foreign keys are ON (`observations` and `video_records` reference `assets`).
        // Dropping a referenced table inside a transaction with enforcement live is a
        // constraint failure, so enforcement is suspended for the rebuild — the tables
        // are being recreated whole, not edited, and it is switched back immediately.
        exec("PRAGMA foreign_keys=OFF;")
        begin()

        var rebuilt: [String] = []
        for table in CatalogMigration.derivedTables {
            exec("DROP TABLE IF EXISTS \(table);")
            rebuilt.append(table)
        }
        for (name, _) in CatalogMigration.authoredTables where tableExists(name) {
            rescue(table: name)
            rebuilt.append(name)
        }

        // `createSchema` is `CREATE TABLE IF NOT EXISTS`, so this rebuilds exactly what
        // was dropped — at this build's column set, indexes and constraints — and
        // leaves everything else alone.
        createSchema()

        for (name, columns) in CatalogMigration.authoredTables {
            restore(table: name, columns: columns)
        }

        // Called a SECOND time, deliberately. Renaming a table takes its indexes with
        // it, so at the first call `idx_decisions_path` still existed — attached to
        // `decisions_migrating` — and `CREATE INDEX IF NOT EXISTS` skipped it, leaving
        // the rebuilt table unindexed. `restore` has since dropped the old table and
        // its index with it, so this call is what actually creates the index. Cheap,
        // because every statement in it is `IF NOT EXISTS`.
        createSchema()

        // The cursor is the resume point for the indexing pass. Leaving it in place
        // after clearing the rows it points past would resume in the middle of a
        // library whose first half no longer has rows — the pass would report itself
        // complete over an index that is missing everything before the cursor.
        exec("DELETE FROM meta WHERE k = 'cursor';")
        setMeta("schema_version", String(Catalog.schemaVersion))
        commit()
        exec("PRAGMA foreign_keys=ON;")

        exec("VACUUM;")
        return CatalogMigration.Outcome(plan: plan,
                                        decisionsKept: scalar("SELECT COUNT(*) FROM decisions;"),
                                        entityReviewKept: scalar("SELECT COUNT(*) FROM entity_review;"),
                                        derivedRowsCleared: cleared,
                                        tablesRebuilt: rebuilt,
                                        missingColumns: missingColumns(),
                                        integrity: integrityCheck())
    }

    /// Move an authored table aside so `createSchema()` can build the current one.
    ///
    /// Renaming rather than reading into memory: the rows stay in SQLite, so a
    /// catalogue with a long decision history does not have to fit in RAM on a phone,
    /// and the whole thing stays inside the transaction.
    private func rescue(table: String) {
        exec("DROP TABLE IF EXISTS \(table)_migrating;")
        exec("ALTER TABLE \(table) RENAME TO \(table)_migrating;")
    }

    /// Carry the rescued rows into the rebuilt table, column by column.
    ///
    /// A column the old table did not have becomes its fallback literal rather than
    /// NULL. Every column here is `NOT NULL` with no default — §14's decision log has
    /// no meaningful empty value — so selecting a missing column would abort the whole
    /// migration, and that is the one outcome worse than a carried-over row with a
    /// placeholder in it.
    private func restore(table: String, columns: [(String, fallback: String)]) {
        let old = "\(table)_migrating"
        guard tableExists(old) else { return }
        let available = columnNames(of: old)
        let names = columns.map { $0.0 }.joined(separator: ",")
        let selects = columns
            .map { available.contains($0.0) ? $0.0 : $0.fallback }
            .joined(separator: ",")
        exec("INSERT OR REPLACE INTO \(table)(\(names)) SELECT \(selects) FROM \(old);")
        exec("DROP TABLE \(old);")
    }

    /// Move a file this build cannot read out of the way and return where it went, so
    /// the caller can open a fresh one at the original path.
    ///
    /// Renamed rather than deleted: the file belongs to a later build the user may go
    /// back to, and deleting the newer build's state to let an older build launch is a
    /// decision nobody asked for. The WAL and shared-memory siblings move with it —
    /// leaving them behind would attach a newer write-ahead log to a fresh database.
    @discardableResult
    public static func quarantine(path: String,
                                  suffix: String = "quarantined") -> String? {
        let manager = FileManager.default
        guard manager.fileExists(atPath: path) else { return nil }
        let destination = path + "." + suffix
        try? manager.removeItem(atPath: destination)
        do { try manager.moveItem(atPath: path, toPath: destination) } catch { return nil }
        for sibling in ["-wal", "-shm"] where manager.fileExists(atPath: path + sibling) {
            try? manager.removeItem(atPath: destination + sibling)
            try? manager.moveItem(atPath: path + sibling, toPath: destination + sibling)
        }
        return destination
    }
}
