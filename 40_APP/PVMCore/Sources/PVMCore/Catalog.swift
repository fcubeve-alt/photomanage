import Foundation
#if canImport(SQLite3)
import SQLite3          // Apple platforms ship it as a module
#else
import CSQLite          // Linux: declared by the system-library target
#endif

/// THE CATALOGUE — where the engine's conclusions live, and how they survive being
/// killed. Schema identical to `30_ENGINE/pvm/catalog.py`, so the reference
/// implementation and the app read the same rows.
///
///  * **C-3 checkpointing.** Work commits every `batchSize` assets and the cursor is
///    written in the same transaction. A process death costs at most one batch. The
///    cursor is not a progress bar; it is the resume point, and writing it outside the
///    transaction would make it a lie.
///  * **A4 incrementality.** Every asset stores a fingerprint of the signals it was
///    classified from and the version of the engine that did it. Re-running skips what
///    has not changed and reclassifies what has — including when the *rules* moved, so
///    a rule change reclassifies the library with no flag for anyone to forget.
///  * **Explanations are stored, not regenerated.** The reason shown to the user is the
///    reason the engine actually used. Recomputing it later against newer rules would
///    quietly rewrite history.
///
/// `@unchecked Sendable` is a claim, so here is the basis for it: the connection is
/// opened with `SQLITE_OPEN_FULLMUTEX`, which serialises every call into SQLite itself,
/// and the class holds no other mutable state. That is what lets the indexing work run
/// off the main thread — without it the depth pass would block the UI for minutes.
public final class Catalog: @unchecked Sendable {

    public static let batchSize = 200
    private static let SQLITE_TRANSIENT = unsafeBitCast(-1, to: sqlite3_destructor_type.self)

    private var db: OpaquePointer?
    public let path: String
    private let engineFingerprint: String

    public init?(path: String, engineFingerprint: String = Catalog.defaultFingerprint) {
        self.path = path
        self.engineFingerprint = engineFingerprint
        guard sqlite3_open_v2(path, &db,
                              SQLITE_OPEN_READWRITE | SQLITE_OPEN_CREATE | SQLITE_OPEN_FULLMUTEX,
                              nil) == SQLITE_OK else { return nil }
        exec("PRAGMA journal_mode=WAL;")
        exec("PRAGMA synchronous=NORMAL;")
        exec("PRAGMA foreign_keys=ON;")
        createSchema()
        setMeta("engine_fingerprint", engineFingerprint)
        commit()
    }

    deinit { if db != nil { sqlite3_close(db) } }

    /// Identity of the decision-making code. Bumped by hand when the ported rules
    /// change, because Swift cannot hash its own source at runtime the way the Python
    /// engine does — so `SharedFingerprintTests` compares it against the generated
    /// files, which is what actually moves.
    public static let defaultFingerprint = "swift-1"

    // MARK: - schema

    private func createSchema() {
        exec("""
        CREATE TABLE IF NOT EXISTS assets(
          asset_id TEXT PRIMARY KEY,
          signals_fp TEXT NOT NULL,
          engine_fp TEXT NOT NULL,
          created_at REAL,
          content_hash TEXT,
          dhash INTEGER,
          -- Needed to answer "找视频" without opening every asset. A retrieval path
          -- that has to re-derive what something is has not been indexed.
          media_type TEXT NOT NULL DEFAULT 'image',
          tier_used INTEGER,
          risk INTEGER,
          needs_review INTEGER,
          notes TEXT,
          classified_at REAL
        );
        CREATE INDEX IF NOT EXISTS idx_assets_risk ON assets(risk);
        CREATE TABLE IF NOT EXISTS assignments(
          asset_id TEXT NOT NULL,
          path TEXT NOT NULL,
          confidence REAL NOT NULL,
          is_primary INTEGER NOT NULL,
          cross_listed_from TEXT,
          PRIMARY KEY(asset_id, path)
        );
        CREATE INDEX IF NOT EXISTS idx_assign_path ON assignments(path);
        CREATE TABLE IF NOT EXISTS evidence(
          asset_id TEXT NOT NULL,
          path TEXT NOT NULL,
          signal TEXT NOT NULL,
          tier INTEGER NOT NULL,
          weight REAL NOT NULL,
          reason TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_evidence_asset ON evidence(asset_id);
        CREATE TABLE IF NOT EXISTS relations(
          kind TEXT NOT NULL, group_key TEXT NOT NULL, asset_id TEXT NOT NULL,
          is_distinct INTEGER NOT NULL DEFAULT 0, reason TEXT NOT NULL,
          PRIMARY KEY(kind, group_key, asset_id)
        );
        CREATE TABLE IF NOT EXISTS proposals(
          asset_id TEXT PRIMARY KEY,
          action TEXT NOT NULL, risk INTEGER NOT NULL,
          reversible INTEGER NOT NULL, requires_confirmation INTEGER NOT NULL,
          auto_applicable INTEGER NOT NULL, note TEXT NOT NULL, why TEXT NOT NULL
        );
        -- The visual memory (§2 Remember, §15). Entities are things in the world;
        -- observations are sightings of them. Beside the catalogue rather than inside
        -- it because they answer different questions: `assignments` says which shelf a
        -- photo is on, `observations` says where a thing was and when.
        CREATE TABLE IF NOT EXISTS entities(
          entity_id TEXT PRIMARY KEY,
          kind TEXT NOT NULL,
          name TEXT NOT NULL,
          category_path TEXT,
          confidence REAL NOT NULL,
          why TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_entities_kind ON entities(kind);

        CREATE TABLE IF NOT EXISTS observations(
          entity_id TEXT NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
          asset_id TEXT NOT NULL REFERENCES assets(asset_id) ON DELETE CASCADE,
          seen_at TEXT,
          place TEXT,
          confidence REAL NOT NULL,
          reason TEXT NOT NULL,
          -- §11 travels with the row. A place column with no provenance column is a
          -- guess that storage has promoted to a fact.
          source TEXT NOT NULL,
          place_source TEXT NOT NULL,
          repeats TEXT,
          PRIMARY KEY(entity_id, asset_id, reason)
        );
        CREATE INDEX IF NOT EXISTS idx_obs_entity ON observations(entity_id, seen_at);
        CREATE INDEX IF NOT EXISTS idx_obs_asset ON observations(asset_id);

        -- L1-B §4: what a video leaves behind is a record, not a pile of frames —
        -- 这个视频对用户个人视觉记忆真正贡献的新信息. One row per video, holding the
        -- shape §4 names, plus what the delta gate skipped so the saving is auditable
        -- rather than asserted.
        CREATE TABLE IF NOT EXISTS video_records(
          asset_id TEXT PRIMARY KEY REFERENCES assets(asset_id) ON DELETE CASCADE,
          date TEXT,
          place TEXT,
          people TEXT NOT NULL,          -- JSON array
          objects TEXT NOT NULL,         -- JSON array
          event TEXT,
          segments TEXT NOT NULL,        -- JSON array of [start_s, end_s]
          frames TEXT NOT NULL,          -- JSON array of representative frame indices
          frames_seen INTEGER NOT NULL,
          why TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT);
        """)
    }

    @discardableResult
    public func exec(_ sql: String) -> Bool {
        sqlite3_exec(db, sql, nil, nil, nil) == SQLITE_OK
    }

    // MARK: - meta / cursor

    public func setMeta(_ key: String, _ value: String) {
        var st: OpaquePointer?
        sqlite3_prepare_v2(db, "INSERT OR REPLACE INTO meta(k,v) VALUES(?,?);", -1, &st, nil)
        sqlite3_bind_text(st, 1, key, -1, Catalog.SQLITE_TRANSIENT)
        sqlite3_bind_text(st, 2, value, -1, Catalog.SQLITE_TRANSIENT)
        sqlite3_step(st); sqlite3_finalize(st)
    }

    public func meta(_ key: String) -> String? {
        var st: OpaquePointer?
        sqlite3_prepare_v2(db, "SELECT v FROM meta WHERE k=?;", -1, &st, nil)
        sqlite3_bind_text(st, 1, key, -1, Catalog.SQLITE_TRANSIENT)
        defer { sqlite3_finalize(st) }
        if sqlite3_step(st) == SQLITE_ROW, let c = sqlite3_column_text(st, 0) {
            return String(cString: c)
        }
        return nil
    }

    public var cursor: String? { meta("cursor") }

    /// Cursor and work commit together. Separately would mean a cursor pointing past
    /// work that was rolled back.
    public func checkpoint(_ cursorValue: String) {
        setMeta("cursor", cursorValue)
        commit()
    }

    public func begin() { exec("BEGIN IMMEDIATE;") }
    public func commit() { exec("COMMIT;") }

    // MARK: - incrementality

    /// What the classifier could see. Includes the OCR text and the scene labels: a
    /// re-run after a better OCR pass must reclassify, and a re-run after nothing
    /// changed must not.
    public static func signalsFingerprint(_ a: AssetSignals) -> String {
        var parts: [String] = [
            a.createdAt.map { String(format: "%.0f", $0.timeIntervalSince1970) } ?? "-",
            a.modifiedAt.map { String(format: "%.0f", $0.timeIntervalSince1970) } ?? "-",
            "\(a.pixelW)x\(a.pixelH)", "\(a.byteSize)",
            a.isVideo ? "v" : "i", a.isScreenshot ? "s" : "-", a.isScreenRecording ? "r" : "-",
            a.source, a.burstID ?? "-",
            a.geo.map { String(format: "%.5f,%.5f,%@", $0.lat, $0.lon, $0.source.rawValue) } ?? "-",
            "\(a.place?.country ?? "")|\(a.place?.city ?? "")",
            a.contentHash ?? "-", a.dhash.map { String($0) } ?? "-",
            a.ocrRan ? "1" : "0", a.ocrText
        ]
        parts.append(a.sceneLabels
            .map { "\($0.identifier):\(String(format: "%.3f", $0.confidence))" }
            .sorted().joined(separator: ","))
        parts.append(a.faceClusters
            .map { "\($0.clusterID):\($0.name ?? "")" }
            .sorted().joined(separator: ","))
        return String(stableHash(parts.joined(separator: "\u{1F}")), radix: 16)
    }

    /// FNV-1a. Not cryptographic and does not need to be — it answers "did anything
    /// change", and a collision costs one asset a re-classification it did not need.
    private static func stableHash(_ text: String) -> UInt64 {
        var h: UInt64 = 0xcbf29ce484222325
        for byte in text.utf8 {
            h ^= UInt64(byte)
            h = h &* 0x100000001b3
        }
        return h
    }

    public func needsClassification(_ a: AssetSignals) -> Bool {
        var st: OpaquePointer?
        sqlite3_prepare_v2(db, "SELECT signals_fp, engine_fp FROM assets WHERE asset_id=?;",
                           -1, &st, nil)
        sqlite3_bind_text(st, 1, a.assetID, -1, Catalog.SQLITE_TRANSIENT)
        defer { sqlite3_finalize(st) }
        guard sqlite3_step(st) == SQLITE_ROW,
              let fp = sqlite3_column_text(st, 0), let ep = sqlite3_column_text(st, 1)
        else { return true }
        return String(cString: fp) != Catalog.signalsFingerprint(a)
            || String(cString: ep) != engineFingerprint
    }

    public func knownIDs() -> Set<String> {
        var out = Set<String>()
        var st: OpaquePointer?
        sqlite3_prepare_v2(db, "SELECT asset_id FROM assets;", -1, &st, nil)
        while sqlite3_step(st) == SQLITE_ROW {
            if let c = sqlite3_column_text(st, 0) { out.insert(String(cString: c)) }
        }
        sqlite3_finalize(st)
        return out
    }

    /// Deletions must drop out of the catalogue, or it stops describing the library it
    /// claims to describe.
    @discardableResult
    public func forget(_ ids: Set<String>) -> Int {
        guard !ids.isEmpty else { return 0 }
        begin()
        for table in ["assets", "assignments", "evidence", "proposals", "relations"] {
            for id in ids {
                var st: OpaquePointer?
                sqlite3_prepare_v2(db, "DELETE FROM \(table) WHERE asset_id=?;", -1, &st, nil)
                sqlite3_bind_text(st, 1, id, -1, Catalog.SQLITE_TRANSIENT)
                sqlite3_step(st); sqlite3_finalize(st)
            }
        }
        commit()
        return ids.count
    }

    // MARK: - writes

    public func upsert(_ a: AssetSignals, _ c: Classification,
                       risk: Risk, proposal: Proposal?) {
        deleteRows("assignments", a.assetID)
        deleteRows("evidence", a.assetID)

        var st: OpaquePointer?
        sqlite3_prepare_v2(db, """
            INSERT OR REPLACE INTO assets
            (asset_id,signals_fp,engine_fp,created_at,content_hash,dhash,
             media_type,tier_used,risk,needs_review,notes,classified_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?);
            """, -1, &st, nil)
        sqlite3_bind_text(st, 1, a.assetID, -1, Catalog.SQLITE_TRANSIENT)
        sqlite3_bind_text(st, 2, Catalog.signalsFingerprint(a), -1, Catalog.SQLITE_TRANSIENT)
        sqlite3_bind_text(st, 3, engineFingerprint, -1, Catalog.SQLITE_TRANSIENT)
        if let d = a.createdAt { sqlite3_bind_double(st, 4, d.timeIntervalSince1970) }
        else { sqlite3_bind_null(st, 4) }
        sqlite3_bind_text(st, 5, a.contentHash ?? "", -1, Catalog.SQLITE_TRANSIENT)
        sqlite3_bind_int64(st, 6, Int64(bitPattern: a.dhash ?? 0))
        sqlite3_bind_text(st, 7, a.isVideo ? "video" : "image", -1, Catalog.SQLITE_TRANSIENT)
        sqlite3_bind_int(st, 8, Int32(c.tierUsed.rawValue))
        sqlite3_bind_int(st, 9, Int32(risk.rawValue))
        sqlite3_bind_int(st, 10, c.needsReview ? 1 : 0)
        sqlite3_bind_text(st, 11, c.notes.joined(separator: " | "), -1, Catalog.SQLITE_TRANSIENT)
        sqlite3_bind_double(st, 12, Date().timeIntervalSince1970)
        sqlite3_step(st); sqlite3_finalize(st)

        for assignment in c.assignments {
            var s2: OpaquePointer?
            sqlite3_prepare_v2(db, """
                INSERT OR REPLACE INTO assignments
                (asset_id,path,confidence,is_primary,cross_listed_from) VALUES(?,?,?,?,?);
                """, -1, &s2, nil)
            sqlite3_bind_text(s2, 1, a.assetID, -1, Catalog.SQLITE_TRANSIENT)
            sqlite3_bind_text(s2, 2, assignment.path, -1, Catalog.SQLITE_TRANSIENT)
            sqlite3_bind_double(s2, 3, assignment.confidence)
            sqlite3_bind_int(s2, 4, assignment.isPrimary ? 1 : 0)
            sqlite3_bind_text(s2, 5, assignment.crossListedFrom ?? "", -1, Catalog.SQLITE_TRANSIENT)
            sqlite3_step(s2); sqlite3_finalize(s2)

            for e in assignment.evidence {
                var s3: OpaquePointer?
                sqlite3_prepare_v2(db, """
                    INSERT INTO evidence(asset_id,path,signal,tier,weight,reason)
                    VALUES(?,?,?,?,?,?);
                    """, -1, &s3, nil)
                sqlite3_bind_text(s3, 1, a.assetID, -1, Catalog.SQLITE_TRANSIENT)
                sqlite3_bind_text(s3, 2, assignment.path, -1, Catalog.SQLITE_TRANSIENT)
                sqlite3_bind_text(s3, 3, e.signal, -1, Catalog.SQLITE_TRANSIENT)
                sqlite3_bind_int(s3, 4, Int32(e.tier.rawValue))
                sqlite3_bind_double(s3, 5, e.weight)
                sqlite3_bind_text(s3, 6, e.reason, -1, Catalog.SQLITE_TRANSIENT)
                sqlite3_step(s3); sqlite3_finalize(s3)
            }
        }

        guard let p = proposal else { return }
        var s4: OpaquePointer?
        sqlite3_prepare_v2(db, """
            INSERT OR REPLACE INTO proposals
            (asset_id,action,risk,reversible,requires_confirmation,auto_applicable,note,why)
            VALUES(?,?,?,?,?,?,?,?);
            """, -1, &s4, nil)
        sqlite3_bind_text(s4, 1, a.assetID, -1, Catalog.SQLITE_TRANSIENT)
        sqlite3_bind_text(s4, 2, p.action.rawValue, -1, Catalog.SQLITE_TRANSIENT)
        sqlite3_bind_int(s4, 3, Int32(p.factors.risk.rawValue))
        sqlite3_bind_int(s4, 4, p.reversible ? 1 : 0)
        sqlite3_bind_int(s4, 5, p.requiresConfirmation ? 1 : 0)
        sqlite3_bind_int(s4, 6, p.autoApplicable ? 1 : 0)
        sqlite3_bind_text(s4, 7, p.note, -1, Catalog.SQLITE_TRANSIENT)
        sqlite3_bind_text(s4, 8, p.why, -1, Catalog.SQLITE_TRANSIENT)
        sqlite3_step(s4); sqlite3_finalize(s4)
    }

    private func deleteRows(_ table: String, _ assetID: String) {
        var st: OpaquePointer?
        sqlite3_prepare_v2(db, "DELETE FROM \(table) WHERE asset_id=?;", -1, &st, nil)
        sqlite3_bind_text(st, 1, assetID, -1, Catalog.SQLITE_TRANSIENT)
        sqlite3_step(st); sqlite3_finalize(st)
    }

    /// Replace the stored memory with this one.
    ///
    /// Rebuilt wholesale rather than merged. An entity is a conclusion drawn from the
    /// whole library — who appears often enough to be a person, which runs of days are
    /// a trip — so a partial update would leave conclusions standing on assets that
    /// have since been deleted. The catalogue rows are the durable thing; the memory is
    /// derived from them and cheap to derive again.
    /// Prepare a statement, and refuse to fail quietly.
    ///
    /// This is the lesson from the `media_type` bug. `Intent.search` built a WHERE
    /// clause naming a column the app's schema did not have; `sqlite3_prepare_v2`
    /// returned an error, the unchecked `st` stayed nil, `sqlite3_step(nil)` returned
    /// something that is not SQLITE_ROW, and the search reported "no matches" to a
    /// question it had never asked. A wrong answer that looks like a valid one is the
    /// failure mode this whole project keeps running into.
    ///
    /// In debug and in tests this trips an assertion, so a schema mismatch is loud
    /// where it is cheap to find. In release it returns nil and the caller yields an
    /// empty result — a search that cannot run must not take the app down with it.
    func prepared(_ sql: String) -> OpaquePointer? {
        var st: OpaquePointer?
        let rc = sqlite3_prepare_v2(db, sql, -1, &st, nil)
        if rc != SQLITE_OK {
            let message = String(cString: sqlite3_errmsg(db))
            assertionFailure("SQL did not prepare: \(message)\n\(sql)")
            return nil
        }
        return st
    }

    /// A text column, or "" when it is NULL. Callers that need to tell those apart
    /// check `sqlite3_column_type` first — this is only for the columns declared
    /// NOT NULL, where an empty string would already mean the row is wrong.
    static func text(_ st: OpaquePointer?, _ column: Int32) -> String {
        guard let c = sqlite3_column_text(st, column) else { return "" }
        return String(cString: c)
    }

    public func writeMemory(_ graph: MemoryGraph) {
        exec("DELETE FROM observations;")
        exec("DELETE FROM entities;")
        begin()
        for e in graph.entities.values {
            var st: OpaquePointer?
            sqlite3_prepare_v2(db, """
                INSERT OR REPLACE INTO entities(entity_id,kind,name,category_path,
                                                confidence,why) VALUES(?,?,?,?,?,?);
                """, -1, &st, nil)
            sqlite3_bind_text(st, 1, e.entityID, -1, Catalog.SQLITE_TRANSIENT)
            sqlite3_bind_text(st, 2, e.kind.rawValue, -1, Catalog.SQLITE_TRANSIENT)
            sqlite3_bind_text(st, 3, e.name, -1, Catalog.SQLITE_TRANSIENT)
            if let path = e.categoryPath {
                sqlite3_bind_text(st, 4, path, -1, Catalog.SQLITE_TRANSIENT)
            } else {
                sqlite3_bind_null(st, 4)
            }
            sqlite3_bind_double(st, 5, e.confidence)
            sqlite3_bind_text(st, 6, e.why, -1, Catalog.SQLITE_TRANSIENT)
            sqlite3_step(st); sqlite3_finalize(st)
        }
        let formatter = ISO8601DateFormatter()
        for o in graph.observations where graph.entities[o.entityID] != nil {
            var st: OpaquePointer?
            sqlite3_prepare_v2(db, """
                INSERT OR REPLACE INTO observations(entity_id,asset_id,seen_at,place,
                    confidence,reason,source,place_source,repeats)
                VALUES(?,?,?,?,?,?,?,?,?);
                """, -1, &st, nil)
            sqlite3_bind_text(st, 1, o.entityID, -1, Catalog.SQLITE_TRANSIENT)
            sqlite3_bind_text(st, 2, o.assetID, -1, Catalog.SQLITE_TRANSIENT)
            if let when = o.when {
                sqlite3_bind_text(st, 3, formatter.string(from: when), -1, Catalog.SQLITE_TRANSIENT)
            } else {
                sqlite3_bind_null(st, 3)
            }
            if let place = o.place {
                sqlite3_bind_text(st, 4, place, -1, Catalog.SQLITE_TRANSIENT)
            } else {
                sqlite3_bind_null(st, 4)
            }
            sqlite3_bind_double(st, 5, o.confidence)
            sqlite3_bind_text(st, 6, o.reason, -1, Catalog.SQLITE_TRANSIENT)
            sqlite3_bind_text(st, 7, o.source.rawValue, -1, Catalog.SQLITE_TRANSIENT)
            sqlite3_bind_text(st, 8, o.placeSource.rawValue, -1, Catalog.SQLITE_TRANSIENT)
            if let repeats = o.repeatsAsset {
                sqlite3_bind_text(st, 9, repeats, -1, Catalog.SQLITE_TRANSIENT)
            } else {
                sqlite3_bind_null(st, 9)
            }
            sqlite3_step(st); sqlite3_finalize(st)
        }
        commit()
    }

    public struct EntityRow {
        public let entityID: String
        public let kind: String
        public let name: String
        public let categoryPath: String?
        public let confidence: Double
        public let why: String
    }

    public func entities(kind: String? = nil, limit: Int = 200) -> [EntityRow] {
        var sql = "SELECT entity_id,kind,name,category_path,confidence,why FROM entities"
        if kind != nil { sql += " WHERE kind=?" }
        sql += " ORDER BY kind, confidence DESC, name LIMIT ?;"
        var st: OpaquePointer?
        sqlite3_prepare_v2(db, sql, -1, &st, nil)
        var index: Int32 = 1
        if let kind {
            sqlite3_bind_text(st, index, kind, -1, Catalog.SQLITE_TRANSIENT)
            index += 1
        }
        sqlite3_bind_int(st, index, Int32(limit))
        var out: [EntityRow] = []
        while sqlite3_step(st) == SQLITE_ROW {
            out.append(EntityRow(
                entityID: Catalog.text(st, 0), kind: Catalog.text(st, 1),
                name: Catalog.text(st, 2),
                categoryPath: sqlite3_column_type(st, 3) == SQLITE_NULL
                    ? nil : Catalog.text(st, 3),
                confidence: sqlite3_column_double(st, 4), why: Catalog.text(st, 5)))
        }
        sqlite3_finalize(st)
        return out
    }

    public struct SightingRow {
        public let assetID: String
        public let seenAt: String?
        public let place: String?
        public let reason: String
        public let placeIsInferred: Bool
        public let repeatsAsset: String?
    }

    /// Oldest first, undated last — the same order `MemoryGraph.history` gives, so the
    /// two cannot disagree about what "last seen" means.
    public func sightings(of entityID: String, limit: Int = 200) -> [SightingRow] {
        var st: OpaquePointer?
        sqlite3_prepare_v2(db, """
            SELECT asset_id,seen_at,place,reason,place_source,repeats FROM observations
            WHERE entity_id=? ORDER BY seen_at IS NULL, seen_at LIMIT ?;
            """, -1, &st, nil)
        sqlite3_bind_text(st, 1, entityID, -1, Catalog.SQLITE_TRANSIENT)
        sqlite3_bind_int(st, 2, Int32(limit))
        var out: [SightingRow] = []
        while sqlite3_step(st) == SQLITE_ROW {
            out.append(SightingRow(
                assetID: Catalog.text(st, 0),
                seenAt: sqlite3_column_type(st, 1) == SQLITE_NULL ? nil : Catalog.text(st, 1),
                place: sqlite3_column_type(st, 2) == SQLITE_NULL ? nil : Catalog.text(st, 2),
                reason: Catalog.text(st, 3),
                placeIsInferred: Catalog.text(st, 4) != "measured",
                repeatsAsset: sqlite3_column_type(st, 5) == SQLITE_NULL
                    ? nil : Catalog.text(st, 5)))
        }
        sqlite3_finalize(st)
        return out
    }

    public func writeVideoRecord(_ record: VideoMemoryRecord, framesSeen: Int) {
        let encoder = JSONEncoder()
        func json<T: Encodable>(_ value: T) -> String {
            guard let data = try? encoder.encode(value),
                  let text = String(data: data, encoding: .utf8) else { return "[]" }
            return text
        }
        let formatter = ISO8601DateFormatter()

        var st: OpaquePointer?
        sqlite3_prepare_v2(db, """
            INSERT OR REPLACE INTO video_records(asset_id,date,place,people,objects,
                event,segments,frames,frames_seen,why) VALUES(?,?,?,?,?,?,?,?,?,?);
            """, -1, &st, nil)
        sqlite3_bind_text(st, 1, record.assetID, -1, Catalog.SQLITE_TRANSIENT)
        if let date = record.date {
            sqlite3_bind_text(st, 2, formatter.string(from: date), -1, Catalog.SQLITE_TRANSIENT)
        } else { sqlite3_bind_null(st, 2) }
        if let place = record.place {
            sqlite3_bind_text(st, 3, place, -1, Catalog.SQLITE_TRANSIENT)
        } else { sqlite3_bind_null(st, 3) }
        sqlite3_bind_text(st, 4, json(record.people), -1, Catalog.SQLITE_TRANSIENT)
        sqlite3_bind_text(st, 5, json(record.objects), -1, Catalog.SQLITE_TRANSIENT)
        if let event = record.event {
            sqlite3_bind_text(st, 6, event, -1, Catalog.SQLITE_TRANSIENT)
        } else { sqlite3_bind_null(st, 6) }
        let spans = record.segments.map { [($0.lowerBound * 1000).rounded() / 1000,
                                           ($0.upperBound * 1000).rounded() / 1000] }
        sqlite3_bind_text(st, 7, json(spans), -1, Catalog.SQLITE_TRANSIENT)
        sqlite3_bind_text(st, 8, json(record.representativeFrames), -1, Catalog.SQLITE_TRANSIENT)
        sqlite3_bind_int(st, 9, Int32(framesSeen))
        sqlite3_bind_text(st, 10, record.evidence.map { $0.reason }.joined(separator: "; "),
                          -1, Catalog.SQLITE_TRANSIENT)
        sqlite3_step(st); sqlite3_finalize(st)
        commit()
    }

    public struct VideoRow {
        public let assetID: String
        public let date: String?
        public let place: String?
        public let people: [String]
        public let objects: [String]
        public let event: String?
        public let segments: [[Double]]
        public let frames: [Int]
        public let framesSeen: Int
        public let why: String
    }

    public func videoRecords(limit: Int = 50) -> [VideoRow] {
        let decoder = JSONDecoder()
        func decode<T: Decodable>(_ text: String, _ fallback: T) -> T {
            guard let data = text.data(using: .utf8),
                  let value = try? decoder.decode(T.self, from: data) else { return fallback }
            return value
        }
        var st: OpaquePointer?
        sqlite3_prepare_v2(db, """
            SELECT asset_id,date,place,people,objects,event,segments,frames,frames_seen,why
            FROM video_records ORDER BY date DESC LIMIT ?;
            """, -1, &st, nil)
        sqlite3_bind_int(st, 1, Int32(limit))
        var out: [VideoRow] = []
        while sqlite3_step(st) == SQLITE_ROW {
            out.append(VideoRow(
                assetID: Catalog.text(st, 0),
                date: sqlite3_column_type(st, 1) == SQLITE_NULL ? nil : Catalog.text(st, 1),
                place: sqlite3_column_type(st, 2) == SQLITE_NULL ? nil : Catalog.text(st, 2),
                people: decode(Catalog.text(st, 3), []),
                objects: decode(Catalog.text(st, 4), []),
                event: sqlite3_column_type(st, 5) == SQLITE_NULL ? nil : Catalog.text(st, 5),
                segments: decode(Catalog.text(st, 6), []),
                frames: decode(Catalog.text(st, 7), []),
                framesSeen: Int(sqlite3_column_int64(st, 8)),
                why: Catalog.text(st, 9)))
        }
        sqlite3_finalize(st)
        return out
    }

    public func writeRelations(_ groups: [RelationGroup]) {
        exec("DELETE FROM relations;")
        begin()
        for (i, g) in groups.enumerated() {
            let key = "\(g.kind):\(i)"
            for member in g.members {
                var st: OpaquePointer?
                sqlite3_prepare_v2(db, """
                    INSERT OR REPLACE INTO relations(kind,group_key,asset_id,is_distinct,reason)
                    VALUES(?,?,?,?,?);
                    """, -1, &st, nil)
                sqlite3_bind_text(st, 1, g.kind, -1, Catalog.SQLITE_TRANSIENT)
                sqlite3_bind_text(st, 2, key, -1, Catalog.SQLITE_TRANSIENT)
                sqlite3_bind_text(st, 3, member, -1, Catalog.SQLITE_TRANSIENT)
                sqlite3_bind_int(st, 4, g.distinctMembers.contains(member) ? 1 : 0)
                sqlite3_bind_text(st, 5, g.reason, -1, Catalog.SQLITE_TRANSIENT)
                sqlite3_step(st); sqlite3_finalize(st)
            }
        }
        commit()
    }

    // MARK: - reads

    public func scalar(_ sql: String) -> Int {
        var st: OpaquePointer?
        sqlite3_prepare_v2(db, sql, -1, &st, nil)
        defer { sqlite3_finalize(st) }
        return sqlite3_step(st) == SQLITE_ROW ? Int(sqlite3_column_int64(st, 0)) : 0
    }

    public func countsByPath() -> [String: Int] {
        var out: [String: Int] = [:]
        var st: OpaquePointer?
        sqlite3_prepare_v2(db, "SELECT path, COUNT(*) FROM assignments GROUP BY path;", -1, &st, nil)
        while sqlite3_step(st) == SQLITE_ROW {
            if let c = sqlite3_column_text(st, 0) {
                out[String(cString: c)] = Int(sqlite3_column_int64(st, 1))
            }
        }
        sqlite3_finalize(st)
        return out
    }

    /// Counts with every ancestor rolled up, which is what a browse tree shows.
    public func rolledCounts() -> [String: Int] {
        var rolled: [String: Int] = [:]
        for (path, n) in countsByPath() {
            rolled[path, default: 0] += n
            for ancestor in TaxonomyRuntime.ancestors(of: path) {
                rolled[ancestor, default: 0] += n
            }
        }
        return rolled
    }

    public struct AssetRow {
        public let assetID: String
        public let primaryPath: String
        public let confidence: Double
        public let risk: Risk
        public let needsReview: Bool
    }

    /// §10 Intent Search, executed against rows that already exist.
    ///
    /// Takes the resolved constraints rather than a sentence: parsing belongs in
    /// `Intent`, and a catalogue that parsed language would be a second place for the
    /// vocabulary to live. Every clause is ANDed, and results are grouped per asset —
    /// one photo filed on three shelves is one result, not three.
    public func search(paths: [String] = [], entityNameGroups: [[String]] = [],
                       mediaType: String? = nil, yearRange: (Double, Double)? = nil,
                       limit: Int = 50) -> [(assetID: String, paths: String)] {
        var clauses: [String] = []
        var texts: [String] = []          // bound in order, after the LIKE pairs
        if !paths.isEmpty {
            let ors = paths.map { _ in "(a2.path = ? OR a2.path LIKE ?)" }
            clauses.append("(" + ors.joined(separator: " OR ") + ")")
            for path in paths { texts.append(path); texts.append(path + Taxonomy.separator + "%") }
        }
        for group in entityNameGroups where !group.isEmpty {
            let marks = group.map { _ in "?" }.joined(separator: ",")
            clauses.append("""
                assets.asset_id IN (SELECT o.asset_id FROM observations o \
                JOIN entities e ON e.entity_id = o.entity_id WHERE e.name IN (\(marks)))
                """)
            texts.append(contentsOf: group)
        }
        if let mediaType {
            clauses.append("assets.media_type = ?")
            texts.append(mediaType)
        }
        var sql = """
            SELECT assets.asset_id, GROUP_CONCAT(a2.path, ' | ') FROM assets
            JOIN assignments a2 ON a2.asset_id = assets.asset_id
            """
        if yearRange != nil { clauses.append("assets.created_at >= ? AND assets.created_at < ?") }
        if !clauses.isEmpty { sql += " WHERE " + clauses.joined(separator: " AND ") }
        sql += " GROUP BY assets.asset_id ORDER BY assets.created_at DESC LIMIT ?;"

        guard let st = prepared(sql) else { return [] }
        var index: Int32 = 1
        for text in texts {
            sqlite3_bind_text(st, index, text, -1, Catalog.SQLITE_TRANSIENT)
            index += 1
        }
        if let yearRange {
            sqlite3_bind_double(st, index, yearRange.0); index += 1
            sqlite3_bind_double(st, index, yearRange.1); index += 1
        }
        sqlite3_bind_int(st, index, Int32(limit))

        var out: [(assetID: String, paths: String)] = []
        while sqlite3_step(st) == SQLITE_ROW {
            out.append((assetID: Catalog.text(st, 0), paths: Catalog.text(st, 1)))
        }
        sqlite3_finalize(st)
        return out
    }

    /// The other sides or pages of the same document.
    ///
    /// Read from the relations the Category-Specific Entity Resolver already wrote,
    /// never recomputed here — 正反面 is a question about entity identity, and §24
    /// Gate 2 says that answer has exactly one home.
    public func sameEntityGroups(containing assetIDs: [String]) -> [[String]] {
        guard !assetIDs.isEmpty else { return [] }
        let marks = assetIDs.map { _ in "?" }.joined(separator: ",")
        var st: OpaquePointer?
        sqlite3_prepare_v2(db, """
            SELECT group_key, asset_id FROM relations
            WHERE kind = 'same_entity' AND group_key IN (
              SELECT group_key FROM relations
              WHERE kind = 'same_entity' AND asset_id IN (\(marks)));
            """, -1, &st, nil)
        for (i, id) in assetIDs.enumerated() {
            sqlite3_bind_text(st, Int32(i + 1), id, -1, Catalog.SQLITE_TRANSIENT)
        }
        var groups: [String: [String]] = [:]
        while sqlite3_step(st) == SQLITE_ROW {
            groups[Catalog.text(st, 0), default: []].append(Catalog.text(st, 1))
        }
        sqlite3_finalize(st)
        return groups.values.filter { $0.count > 1 }.map { $0.sorted() }
    }

    public func assets(under path: String, limit: Int = 300) -> [AssetRow] {
        var out: [AssetRow] = []
        var st: OpaquePointer?
        let sql = """
            SELECT a.asset_id, s.path, s.confidence, a.risk, a.needs_review
            FROM assignments s JOIN assets a ON a.asset_id = s.asset_id
            WHERE s.path = ? OR s.path LIKE ?
            ORDER BY a.created_at DESC LIMIT ?;
            """
        sqlite3_prepare_v2(db, sql, -1, &st, nil)
        sqlite3_bind_text(st, 1, path, -1, Catalog.SQLITE_TRANSIENT)
        sqlite3_bind_text(st, 2, path + Taxonomy.separator + "%", -1, Catalog.SQLITE_TRANSIENT)
        sqlite3_bind_int(st, 3, Int32(limit))
        while sqlite3_step(st) == SQLITE_ROW {
            guard let id = sqlite3_column_text(st, 0), let p = sqlite3_column_text(st, 1) else { continue }
            out.append(AssetRow(assetID: String(cString: id),
                                primaryPath: String(cString: p),
                                confidence: sqlite3_column_double(st, 2),
                                risk: Risk(rawValue: Int(sqlite3_column_int(st, 3))) ?? .r2Normal,
                                needsReview: sqlite3_column_int(st, 4) == 1))
        }
        sqlite3_finalize(st)
        return out
    }

    /// The §-red-line answer: why is this here?
    public func why(_ assetID: String) -> [(path: String, reasons: [String])] {
        var grouped: [String: [String]] = [:]
        var order: [String] = []
        var st: OpaquePointer?
        sqlite3_prepare_v2(db,
            "SELECT path, reason FROM evidence WHERE asset_id=? ORDER BY weight DESC;",
            -1, &st, nil)
        sqlite3_bind_text(st, 1, assetID, -1, Catalog.SQLITE_TRANSIENT)
        while sqlite3_step(st) == SQLITE_ROW {
            guard let p = sqlite3_column_text(st, 0), let r = sqlite3_column_text(st, 1) else { continue }
            let path = String(cString: p)
            if grouped[path] == nil { order.append(path) }
            grouped[path, default: []].append(String(cString: r))
        }
        sqlite3_finalize(st)
        return order.map { (path: $0, reasons: grouped[$0] ?? []) }
    }

    public struct ReviewItem {
        public let assetID: String
        public let action: String
        public let note: String
        public let why: String
    }

    public func reviewQueue(limit: Int = 100) -> [ReviewItem] {
        var out: [ReviewItem] = []
        var st: OpaquePointer?
        sqlite3_prepare_v2(db, """
            SELECT a.asset_id, p.action, p.note, p.why
            FROM assets a JOIN proposals p ON p.asset_id = a.asset_id
            WHERE a.needs_review = 1 OR p.action = 'review'
            ORDER BY a.created_at DESC LIMIT ?;
            """, -1, &st, nil)
        sqlite3_bind_int(st, 1, Int32(limit))
        while sqlite3_step(st) == SQLITE_ROW {
            guard let a = sqlite3_column_text(st, 0), let b = sqlite3_column_text(st, 1),
                  let c = sqlite3_column_text(st, 2), let d = sqlite3_column_text(st, 3)
            else { continue }
            out.append(ReviewItem(assetID: String(cString: a), action: String(cString: b),
                                  note: String(cString: c), why: String(cString: d)))
        }
        sqlite3_finalize(st)
        return out
    }

    /// The stored decisions for one asset. Used by the conformance test, which needs
    /// the exact row rather than whatever a browse query happens to return first.
    public func decision(for assetID: String) -> (risk: Risk, action: String?)? {
        var st: OpaquePointer?
        sqlite3_prepare_v2(db, """
            SELECT a.risk, p.action FROM assets a
            LEFT JOIN proposals p ON p.asset_id = a.asset_id
            WHERE a.asset_id = ?;
            """, -1, &st, nil)
        sqlite3_bind_text(st, 1, assetID, -1, Catalog.SQLITE_TRANSIENT)
        defer { sqlite3_finalize(st) }
        guard sqlite3_step(st) == SQLITE_ROW else { return nil }
        let risk = Risk(rawValue: Int(sqlite3_column_int(st, 0))) ?? .r2Normal
        var action: String?
        if let c = sqlite3_column_text(st, 1) { action = String(cString: c) }
        return (risk: risk, action: action)
    }

    public func paths(for assetID: String) -> [String] {
        var out: [String] = []
        var st: OpaquePointer?
        sqlite3_prepare_v2(db,
            "SELECT path FROM assignments WHERE asset_id=? ORDER BY path;", -1, &st, nil)
        sqlite3_bind_text(st, 1, assetID, -1, Catalog.SQLITE_TRANSIENT)
        while sqlite3_step(st) == SQLITE_ROW {
            if let c = sqlite3_column_text(st, 0) { out.append(String(cString: c)) }
        }
        sqlite3_finalize(st)
        return out
    }

    public func sizeOnDisk() -> Int64 {
        var total: Int64 = 0
        for suffix in ["", "-wal", "-shm"] {
            if let attrs = try? FileManager.default.attributesOfItem(atPath: path + suffix),
               let s = attrs[.size] as? Int64 { total += s }
        }
        return total
    }
}
