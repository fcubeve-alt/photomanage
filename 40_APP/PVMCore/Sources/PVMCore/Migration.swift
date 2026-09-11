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
/// So the migration policy is: **rebuild the derived half, preserve the authored half,
/// never copy the file.** A file copy on a phone with a 100k-asset catalogue costs
/// storage the user may not have, to protect data that can be recomputed for free.
///
/// The failure this is written against is the ordinary one: a new column is added, the
/// old file does not have it, and `CREATE TABLE IF NOT EXISTS` — which is all the
/// schema code does — adds tables but never adds a column to an existing table. The
/// old file therefore opens cleanly and fails at the first query that names the new
/// column. That is a crash on launch, after the update, with no way back.
public enum CatalogMigration {

    /// Tables whose every row can be recomputed from the photo library.
    public static let derivedTables = [
        "assets", "assignments", "evidence", "relations", "proposals",
        "entities", "observations", "video_records",
    ]

    /// Tables holding something the user said. Never cleared by a migration.
    public static let authoredTables = ["decisions", "entity_review"]

    /// `meta` keys that are settings rather than engine state.
    public static let preferenceKeyPrefix = "pref."

    public enum Plan: Equatable {
        /// The file did not exist. Nothing to do.
        case fresh
        /// Written by this build. Nothing to do.
        case current
        /// Older. The derived half is cleared and recomputed; the authored half stays.
        case rebuildDerived(from: Int)
        /// Newer. This build cannot read the shape and will not guess at it.
        case newerThanThisBuild(Int)

        public var needsWork: Bool {
            switch self {
            case .fresh, .current: return false
            case .rebuildDerived, .newerThanThisBuild: return true
            }
        }
    }

    public static func plan(openedVersion: Int,
                            buildVersion: Int = Catalog.schemaVersion) -> Plan {
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
        public let integrity: String

        public var succeeded: Bool { integrity == "ok" || integrity == "unavailable" }
    }
}

extension Catalog {

    public var migrationPlan: CatalogMigration.Plan {
        CatalogMigration.plan(openedVersion: openedSchemaVersion)
    }

    /// Bring the file to this build's shape. Safe to call on every launch: when there
    /// is nothing to do it reads two counts and returns.
    ///
    /// The ordering matters and is the whole point. The version stamp moves **after**
    /// the clear and **inside the same transaction**, so a kill at any moment leaves
    /// the file either entirely un-migrated (and still marked as such, so the next
    /// launch retries) or entirely migrated. There is no state where the stamp says
    /// one thing and the tables say another — which is the state the previous code
    /// could produce and the reason this exists.
    @discardableResult
    public func migrate() -> CatalogMigration.Outcome {
        let plan = migrationPlan
        let kept = (scalar("SELECT COUNT(*) FROM decisions;"),
                    scalar("SELECT COUNT(*) FROM entity_review;"))

        guard case .rebuildDerived = plan else {
            return CatalogMigration.Outcome(plan: plan,
                                            decisionsKept: kept.0,
                                            entityReviewKept: kept.1,
                                            derivedRowsCleared: 0,
                                            integrity: plan == .fresh ? "ok" : integrityCheck())
        }

        var cleared = 0
        for table in CatalogMigration.derivedTables {
            cleared += scalar("SELECT COUNT(*) FROM \(table);")
        }

        begin()
        for table in CatalogMigration.derivedTables {
            exec("DELETE FROM \(table);")
        }
        // The cursor is the resume point for the indexing pass. Leaving it in place
        // after clearing the rows it points past would resume in the middle of a
        // library whose first half no longer has rows — the pass would report itself
        // complete over an index that is missing everything before the cursor.
        exec("DELETE FROM meta WHERE k = 'cursor';")
        setMeta("schema_version", String(Catalog.schemaVersion))
        commit()

        exec("VACUUM;")
        return CatalogMigration.Outcome(plan: plan,
                                        decisionsKept: kept.0,
                                        entityReviewKept: kept.1,
                                        derivedRowsCleared: cleared,
                                        integrity: integrityCheck())
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
