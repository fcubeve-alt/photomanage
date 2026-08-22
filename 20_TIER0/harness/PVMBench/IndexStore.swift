import Foundation
import SQLite3

/// Raw SQLite3 — no SPM dependency, so the cloud-Mac block is not spent
/// resolving packages. Also gives a realistic index-size-on-disk number (§8).
final class IndexStore {

    private var db: OpaquePointer?
    private let path: URL
    private static let SQLITE_TRANSIENT = unsafeBitCast(-1, to: sqlite3_destructor_type.self)

    init() {
        let dir = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        path = dir.appendingPathComponent("pvm_index.sqlite")
        open()
    }

    private func open() {
        guard sqlite3_open_v2(path.path, &db,
              SQLITE_OPEN_READWRITE | SQLITE_OPEN_CREATE | SQLITE_OPEN_FULLMUTEX, nil) == SQLITE_OK else {
            fatalError("cannot open index db")
        }
        exec("PRAGMA journal_mode=WAL;")
        exec("PRAGMA synchronous=NORMAL;")
        exec("""
        CREATE TABLE IF NOT EXISTS assets(
          local_id TEXT PRIMARY KEY,
          created_at REAL, modified_at REAL,
          lat REAL, lon REAL, loc_confidence REAL,
          media_type INTEGER, is_screenshot INTEGER, is_synthetic INTEGER,
          px_w INTEGER, px_h INTEGER, byte_size INTEGER,
          dhash INTEGER,
          ocr_ran INTEGER, ocr_text TEXT,
          embedding BLOB,
          icloud_only INTEGER,
          indexed_at REAL
        );
        """)
        exec("CREATE INDEX IF NOT EXISTS idx_dhash ON assets(dhash);")
        exec("CREATE INDEX IF NOT EXISTS idx_created ON assets(created_at);")
        exec("CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT);")
        // DEC-009: synthetic assets we created, tracked so cleanup can NEVER
        // touch anything pre-existing.
        exec("CREATE TABLE IF NOT EXISTS synthetic(local_id TEXT PRIMARY KEY, created_at REAL);")
    }

    func exec(_ sql: String) {
        var err: UnsafeMutablePointer<CChar>?
        if sqlite3_exec(db, sql, nil, nil, &err) != SQLITE_OK, let e = err {
            print("[IndexStore] SQL error: \(String(cString: e))"); sqlite3_free(err)
        }
    }

    // MARK: - checkpointing (C-3)

    func beginBatch() { exec("BEGIN IMMEDIATE;") }
    func commitBatch() { exec("COMMIT;") }

    func setCursor(_ value: String) { setMeta("cursor", value) }
    func cursor() -> String? { meta("cursor") }

    func setMeta(_ k: String, _ v: String) {
        var st: OpaquePointer?
        sqlite3_prepare_v2(db, "INSERT OR REPLACE INTO meta(k,v) VALUES(?,?);", -1, &st, nil)
        sqlite3_bind_text(st, 1, k, -1, IndexStore.SQLITE_TRANSIENT)
        sqlite3_bind_text(st, 2, v, -1, IndexStore.SQLITE_TRANSIENT)
        sqlite3_step(st); sqlite3_finalize(st)
    }

    func meta(_ k: String) -> String? {
        var st: OpaquePointer?
        sqlite3_prepare_v2(db, "SELECT v FROM meta WHERE k=?;", -1, &st, nil)
        sqlite3_bind_text(st, 1, k, -1, IndexStore.SQLITE_TRANSIENT)
        defer { sqlite3_finalize(st) }
        if sqlite3_step(st) == SQLITE_ROW, let c = sqlite3_column_text(st, 0) {
            return String(cString: c)
        }
        return nil
    }

    // MARK: - assets

    func upsert(_ r: AssetRecord) {
        var st: OpaquePointer?
        let sql = """
        INSERT OR REPLACE INTO assets
        (local_id,created_at,modified_at,lat,lon,loc_confidence,media_type,is_screenshot,is_synthetic,
         px_w,px_h,byte_size,dhash,ocr_ran,ocr_text,embedding,icloud_only,indexed_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);
        """
        sqlite3_prepare_v2(db, sql, -1, &st, nil)
        sqlite3_bind_text(st, 1, r.localID, -1, IndexStore.SQLITE_TRANSIENT)
        sqlite3_bind_double(st, 2, r.createdAt)
        sqlite3_bind_double(st, 3, r.modifiedAt)
        sqlite3_bind_double(st, 4, r.lat); sqlite3_bind_double(st, 5, r.lon)
        sqlite3_bind_double(st, 6, r.locConfidence)
        sqlite3_bind_int(st, 7, Int32(r.mediaType))
        sqlite3_bind_int(st, 8, r.isScreenshot ? 1 : 0)
        sqlite3_bind_int(st, 9, r.isSynthetic ? 1 : 0)
        sqlite3_bind_int(st, 10, Int32(r.pxW)); sqlite3_bind_int(st, 11, Int32(r.pxH))
        sqlite3_bind_int64(st, 12, r.byteSize)
        sqlite3_bind_int64(st, 13, Int64(bitPattern: r.dhash))
        sqlite3_bind_int(st, 14, r.ocrRan ? 1 : 0)
        sqlite3_bind_text(st, 15, r.ocrText, -1, IndexStore.SQLITE_TRANSIENT)
        if let e = r.embedding {
            _ = e.withUnsafeBytes { sqlite3_bind_blob(st, 16, $0.baseAddress, Int32(e.count), IndexStore.SQLITE_TRANSIENT) }
        } else { sqlite3_bind_null(st, 16) }
        sqlite3_bind_int(st, 17, r.icloudOnly ? 1 : 0)
        sqlite3_bind_double(st, 18, Date().timeIntervalSince1970)
        sqlite3_step(st); sqlite3_finalize(st)
    }

    func contains(_ localID: String) -> Bool {
        var st: OpaquePointer?
        sqlite3_prepare_v2(db, "SELECT 1 FROM assets WHERE local_id=?;", -1, &st, nil)
        sqlite3_bind_text(st, 1, localID, -1, IndexStore.SQLITE_TRANSIENT)
        defer { sqlite3_finalize(st) }
        return sqlite3_step(st) == SQLITE_ROW
    }

    /// Deletions must drop out of the index, or A4 reports a library that no
    /// longer matches reality.
    func remove(_ localID: String) {
        var st: OpaquePointer?
        sqlite3_prepare_v2(db, "DELETE FROM assets WHERE local_id=?;", -1, &st, nil)
        sqlite3_bind_text(st, 1, localID, -1, IndexStore.SQLITE_TRANSIENT)
        sqlite3_step(st); sqlite3_finalize(st)
    }

    func count() -> Int { scalar("SELECT COUNT(*) FROM assets;") }
    func syntheticCount() -> Int { scalar("SELECT COUNT(*) FROM synthetic;") }

    private func scalar(_ sql: String) -> Int {
        var st: OpaquePointer?
        sqlite3_prepare_v2(db, sql, -1, &st, nil)
        defer { sqlite3_finalize(st) }
        return sqlite3_step(st) == SQLITE_ROW ? Int(sqlite3_column_int64(st, 0)) : 0
    }

    // MARK: - synthetic tracking (DEC-009)

    func recordSynthetic(_ localID: String) {
        var st: OpaquePointer?
        sqlite3_prepare_v2(db, "INSERT OR REPLACE INTO synthetic(local_id,created_at) VALUES(?,?);", -1, &st, nil)
        sqlite3_bind_text(st, 1, localID, -1, IndexStore.SQLITE_TRANSIENT)
        sqlite3_bind_double(st, 2, Date().timeIntervalSince1970)
        sqlite3_step(st); sqlite3_finalize(st)
    }

    /// The ONLY source of ids the cleanup path is allowed to delete.
    func syntheticIDs() -> [String] {
        var out: [String] = []
        var st: OpaquePointer?
        sqlite3_prepare_v2(db, "SELECT local_id FROM synthetic;", -1, &st, nil)
        while sqlite3_step(st) == SQLITE_ROW {
            if let c = sqlite3_column_text(st, 0) { out.append(String(cString: c)) }
        }
        sqlite3_finalize(st)
        return out
    }

    func forgetSynthetic(_ ids: [String]) {
        beginBatch()
        for id in ids {
            var st: OpaquePointer?
            sqlite3_prepare_v2(db, "DELETE FROM synthetic WHERE local_id=?;", -1, &st, nil)
            sqlite3_bind_text(st, 1, id, -1, IndexStore.SQLITE_TRANSIENT)
            sqlite3_step(st); sqlite3_finalize(st)
        }
        commitBatch()
    }

    // MARK: - size on disk (§8 budget: <= 2 KB/asset)

    func sizeOnDisk() -> Int64 {
        let fm = FileManager.default
        var total: Int64 = 0
        for suffix in ["", "-wal", "-shm"] {
            let p = path.path + suffix
            if let a = try? fm.attributesOfItem(atPath: p), let s = a[.size] as? Int64 { total += s }
        }
        return total
    }

    func reset() {
        exec("DELETE FROM assets;"); exec("DELETE FROM meta;")
        exec("VACUUM;")
    }
}

struct AssetRecord {
    var localID: String
    var createdAt: Double = 0
    var modifiedAt: Double = 0
    var lat: Double = 0
    var lon: Double = 0
    var locConfidence: Double = 0
    var mediaType: Int = 0
    var isScreenshot = false
    var isSynthetic = false
    var pxW = 0
    var pxH = 0
    var byteSize: Int64 = 0
    var dhash: UInt64 = 0
    var ocrRan = false
    var ocrText = ""
    var embedding: Data? = nil
    var icloudOnly = false
}
