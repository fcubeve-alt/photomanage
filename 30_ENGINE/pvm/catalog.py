# -*- coding: utf-8 -*-
"""
THE CATALOGUE — where the engine's conclusions live, and how they survive interruption.

Design constraints that come straight from T0-A, because the classifier will run in
the same hostile place the indexer does — a phone, in the background, being killed:

* **C-3 checkpointing.** Work is committed every `BATCH` assets and a cursor is
  written in the same transaction. A process death costs at most one batch. The
  cursor is not a progress bar; it is the resume point, and writing it outside the
  transaction would make it a lie.
* **A4 incrementality.** Every asset stores a fingerprint of the signals it was
  classified from, together with the version of the engine that did it. Re-running
  skips assets whose fingerprint is unchanged and reclassifies the ones where either
  the photo or the rules moved. Changing a rule therefore reclassifies the library
  without a flag being remembered, which is the only version of this that stays
  correct.
* **Explanations are stored, not regenerated.** The reason shown to the user is the
  reason the engine actually used at the time. Recomputing it later against newer
  rules would quietly rewrite history.

SQLite with no ORM: this schema has to be portable to the Swift side unchanged, and
`IndexStore.swift` already established the pattern.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence

from .risk import NEVER_DELETE_AT_OR_ABOVE, Proposal, Risk
from .verdict import Classification

BATCH = 200          # C-3: one checkpoint batch, matching the indexer
SCHEMA_VERSION = 3


def _sqlite_int64(value):
    """A dHash is 64 unsigned bits; SQLite integers are signed. Store the bit pattern,
    exactly as `IndexStore.swift` does with `Int64(bitPattern:)`, so the two sides read
    the same rows."""
    if value is None:
        return None
    value &= (1 << 64) - 1
    return value - (1 << 64) if value >= (1 << 63) else value


def engine_fingerprint() -> str:
    """Identity of the decision-making code. If any of it changes, every conclusion
    it produced is stale by definition."""
    h = hashlib.sha256()
    here = os.path.dirname(os.path.abspath(__file__))
    for name in ("classifier.py", "rules.py", "risk.py", "dedup.py", "context.py", "verdict.py"):
        with open(os.path.join(here, name), "rb") as fh:
            h.update(fh.read())
    return h.hexdigest()[:16]


def signals_fingerprint(a) -> str:
    """What the classifier could see. Deliberately includes the OCR text and the
    scene labels: a re-run after a better OCR pass must reclassify, and a re-run after
    nothing changed must not."""
    payload = json.dumps({
        "created": a.created_at.isoformat() if a.created_at else None,
        "modified": a.modified_at.isoformat() if a.modified_at else None,
        "px": [a.pixel_w, a.pixel_h], "bytes": a.byte_size,
        "media": a.media_type, "shot": a.is_screenshot, "rec": a.is_screen_recording,
        "src": a.source, "burst": a.burst_id,
        "geo": [round(a.geo.lat, 5), round(a.geo.lon, 5), a.geo.source] if a.geo else None,
        "place": [a.place.country, a.place.city] if a.place else None,
        "hash": a.content_hash, "dhash": a.dhash,
        "ocr": a.ocr_text, "ocr_ran": a.ocr_ran,
        "scene": sorted((s.identifier, round(s.confidence, 3)) for s in a.scene_labels),
        "faces": sorted((f.cluster_id, f.name or "") for f in a.face_clusters),
    }, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


class Catalog:
    def __init__(self, path: str = "pvm_catalog.sqlite"):
        self.path = path
        self.db = sqlite3.connect(path)
        self.db.execute("PRAGMA journal_mode=WAL;")
        self.db.execute("PRAGMA synchronous=NORMAL;")
        self.db.execute("PRAGMA foreign_keys=ON;")
        self._schema()
        self._engine = engine_fingerprint()
        self.set_meta("schema_version", str(SCHEMA_VERSION))
        self.set_meta("engine_fingerprint", self._engine)

    # -- schema ------------------------------------------------------------
    def _schema(self) -> None:
        c = self.db
        c.executescript("""
        CREATE TABLE IF NOT EXISTS assets(
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
        CREATE INDEX IF NOT EXISTS idx_assets_hash ON assets(content_hash);
        CREATE INDEX IF NOT EXISTS idx_assets_risk ON assets(risk);

        CREATE TABLE IF NOT EXISTS assignments(
          asset_id TEXT NOT NULL REFERENCES assets(asset_id) ON DELETE CASCADE,
          path TEXT NOT NULL,
          confidence REAL NOT NULL,
          is_primary INTEGER NOT NULL,
          cross_listed_from TEXT,
          PRIMARY KEY(asset_id, path)
        );
        CREATE INDEX IF NOT EXISTS idx_assign_path ON assignments(path);

        -- The user-facing answer to "why is this here?". Stored as written, never
        -- regenerated: a newer rule set must not be able to rewrite the reason an
        -- older one gave.
        CREATE TABLE IF NOT EXISTS evidence(
          asset_id TEXT NOT NULL REFERENCES assets(asset_id) ON DELETE CASCADE,
          path TEXT NOT NULL,
          signal TEXT NOT NULL,
          tier INTEGER NOT NULL,
          weight REAL NOT NULL,
          reason TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_evidence_asset ON evidence(asset_id);

        CREATE TABLE IF NOT EXISTS relations(
          kind TEXT NOT NULL,
          group_key TEXT NOT NULL,
          asset_id TEXT NOT NULL,
          is_distinct INTEGER NOT NULL DEFAULT 0,
          reason TEXT NOT NULL,
          PRIMARY KEY(kind, group_key, asset_id)
        );

        CREATE TABLE IF NOT EXISTS proposals(
          asset_id TEXT PRIMARY KEY REFERENCES assets(asset_id) ON DELETE CASCADE,
          action TEXT NOT NULL,
          risk INTEGER NOT NULL,
          reversible INTEGER NOT NULL,
          requires_confirmation INTEGER NOT NULL,
          auto_applicable INTEGER NOT NULL,
          note TEXT NOT NULL,
          why TEXT NOT NULL
        );

        -- The visual memory (§2 Remember, §15). Entities are things in the world;
        -- observations are sightings of them. Kept beside the catalogue rather than
        -- inside it because they answer different questions: `assignments` says which
        -- shelf a photo is on, `observations` says where a thing was and when.
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
          -- guess that has been promoted to a fact by storage.
          source TEXT NOT NULL,
          place_source TEXT NOT NULL,
          -- The anchor asset when this sighting repeats another from the same moment.
          -- A flag, not a deletion: the row stays and a view may fold it.
          repeats TEXT,
          PRIMARY KEY(entity_id, asset_id, reason)
        );
        CREATE INDEX IF NOT EXISTS idx_obs_entity ON observations(entity_id, seen_at);
        CREATE INDEX IF NOT EXISTS idx_obs_asset ON observations(asset_id);

        -- §24 Gate 2: 低置信度只能进入 Review Queue，不自动合并/删除. A pair the
        -- Category-Specific Entity Resolver would not decide is a question for the
        -- user, and a question nobody is shown is the same as a merge nobody agreed to.
        CREATE TABLE IF NOT EXISTS entity_review(
          asset_a TEXT NOT NULL REFERENCES assets(asset_id) ON DELETE CASCADE,
          asset_b TEXT NOT NULL REFERENCES assets(asset_id) ON DELETE CASCADE,
          reason TEXT NOT NULL,
          PRIMARY KEY(asset_a, asset_b)
        );

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
        self.db.commit()

    # -- meta / cursor -----------------------------------------------------
    def set_meta(self, k: str, v: str) -> None:
        self.db.execute("INSERT OR REPLACE INTO meta(k,v) VALUES(?,?)", (k, v))

    def meta(self, k: str) -> Optional[str]:
        row = self.db.execute("SELECT v FROM meta WHERE k=?", (k,)).fetchone()
        return row[0] if row else None

    @property
    def cursor(self) -> Optional[str]:
        return self.meta("cursor")

    # -- incrementality ----------------------------------------------------
    def needs_classification(self, asset) -> bool:
        row = self.db.execute(
            "SELECT signals_fp, engine_fp FROM assets WHERE asset_id=?",
            (asset.asset_id,)).fetchone()
        if row is None:
            return True
        return row[0] != signals_fingerprint(asset) or row[1] != self._engine

    def known_ids(self) -> set:
        return {r[0] for r in self.db.execute("SELECT asset_id FROM assets")}

    def forget(self, asset_ids: Iterable[str]) -> int:
        """Deletions must drop out of the catalogue, or it stops describing the
        library it claims to describe."""
        ids = list(asset_ids)
        if not ids:
            return 0
        self.db.executemany("DELETE FROM assets WHERE asset_id=?", [(i,) for i in ids])
        self.db.executemany("DELETE FROM relations WHERE asset_id=?", [(i,) for i in ids])
        self.db.commit()
        return len(ids)

    # -- writes ------------------------------------------------------------
    def upsert(self, asset, c: Classification, risk: Risk, proposal: Optional[Proposal]) -> None:
        aid = c.asset_id
        self.db.execute("DELETE FROM assignments WHERE asset_id=?", (aid,))
        self.db.execute("DELETE FROM evidence WHERE asset_id=?", (aid,))
        self.db.execute(
            """INSERT OR REPLACE INTO assets
               (asset_id,signals_fp,engine_fp,created_at,content_hash,dhash,
                tier_used,risk,needs_review,notes,classified_at)
               VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (aid, signals_fingerprint(asset), self._engine,
             asset.created_at.timestamp() if asset.created_at else None,
             asset.content_hash, _sqlite_int64(asset.dhash), int(c.tier_used), int(risk),
             int(c.needs_review), json.dumps(c.notes, ensure_ascii=False), time.time()))

        for a in c.assignments:
            self.db.execute(
                """INSERT OR REPLACE INTO assignments
                   (asset_id,path,confidence,is_primary,cross_listed_from) VALUES(?,?,?,?,?)""",
                (aid, a.path, a.confidence, int(a.is_primary), a.cross_listed_from))
            for e in a.evidence:
                self.db.execute(
                    "INSERT INTO evidence(asset_id,path,signal,tier,weight,reason) VALUES(?,?,?,?,?,?)",
                    (aid, a.path, e.signal, int(e.tier), e.weight, e.reason))

        if proposal is not None:
            self.db.execute(
                """INSERT OR REPLACE INTO proposals
                   (asset_id,action,risk,reversible,requires_confirmation,auto_applicable,note,why)
                   VALUES(?,?,?,?,?,?,?,?)""",
                (aid, proposal.action.value, int(proposal.factors.risk), int(proposal.reversible),
                 int(proposal.requires_confirmation), int(proposal.auto_applicable),
                 proposal.note, proposal.why()))

    def write_relations(self, groups) -> None:
        self.db.execute("DELETE FROM relations")
        for i, g in enumerate(groups):
            key = f"{g.kind}:{i}"
            for member in g.members:
                self.db.execute(
                    """INSERT OR REPLACE INTO relations(kind,group_key,asset_id,is_distinct,reason)
                       VALUES(?,?,?,?,?)""",
                    (g.kind, key, member, int(member in g.distinct_members), g.reason))
        self.db.commit()

    def write_memory(self, graph) -> None:
        """Replace the stored memory with this one.

        Rebuilt wholesale rather than merged. An entity is a conclusion drawn from the
        whole library — who appears often enough to be a person, which runs of days are
        a trip — so a partial update would leave conclusions standing on assets that
        have since been deleted. The catalogue rows are the durable thing; the memory
        is derived from them and is cheap to derive again.
        """
        self.db.execute("DELETE FROM observations")
        self.db.execute("DELETE FROM entities")
        for e in graph.entities.values():
            self.db.execute(
                """INSERT OR REPLACE INTO entities(entity_id,kind,name,category_path,
                                                   confidence,why) VALUES(?,?,?,?,?,?)""",
                (e.entity_id, e.kind.value, e.name, e.category_path,
                 float(e.confidence), e.why()))
        known = set(graph.entities)
        for o in graph.observations:
            if o.entity_id not in known:
                continue
            self.db.execute(
                """INSERT OR REPLACE INTO observations(entity_id,asset_id,seen_at,place,
                       confidence,reason,source,place_source,repeats)
                   VALUES(?,?,?,?,?,?,?,?,?)""",
                (o.entity_id, o.asset_id, o.when.isoformat() if o.when else None,
                 o.place, float(o.confidence), o.reason, o.source, o.place_source,
                 o.repeats))
        self.db.commit()

    def entities(self, kind: Optional[str] = None, limit: int = 200):
        sql = "SELECT entity_id,kind,name,category_path,confidence,why FROM entities"
        args: tuple = ()
        if kind:
            sql += " WHERE kind=?"
            args = (kind,)
        sql += " ORDER BY kind, confidence DESC, name LIMIT ?"
        return self.db.execute(sql, args + (limit,)).fetchall()

    def sightings(self, entity_id: str, limit: int = 200):
        """Oldest first, undated last — the same order `MemoryGraph.history` gives, so
        the two cannot disagree about what "last seen" means."""
        return self.db.execute(
            """SELECT asset_id,seen_at,place,confidence,reason,source,place_source,repeats
               FROM observations WHERE entity_id=?
               ORDER BY seen_at IS NULL, seen_at LIMIT ?""",
            (entity_id, limit)).fetchall()

    def write_video_record(self, record, frames_seen: int) -> None:
        self.db.execute(
            """INSERT OR REPLACE INTO video_records(asset_id,date,place,people,objects,
                   event,segments,frames,frames_seen,why)
               VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (record.asset_id,
             record.date.isoformat() if record.date else None,
             record.place,
             json.dumps(record.people),
             json.dumps(record.objects),
             record.event,
             json.dumps([[round(a, 3), round(b, 3)] for a, b in record.segments]),
             json.dumps(record.representative_frames),
             frames_seen,
             "; ".join(e.reason for e in record.evidence)))

    def video_records(self, limit: int = 50):
        return self.db.execute(
            """SELECT asset_id,date,place,people,objects,event,segments,frames,
                      frames_seen,why FROM video_records ORDER BY date DESC LIMIT ?""",
            (limit,)).fetchall()

    def write_entity_review(self, pairs) -> None:
        self.db.execute("DELETE FROM entity_review")
        for a, b, reason in pairs:
            self.db.execute(
                "INSERT OR REPLACE INTO entity_review(asset_a,asset_b,reason) VALUES(?,?,?)",
                (a, b, reason))
        self.db.commit()

    def entity_review_queue(self, limit: int = 50):
        return self.db.execute(
            "SELECT asset_a, asset_b, reason FROM entity_review LIMIT ?",
            (limit,)).fetchall()

    def checkpoint(self, cursor_value: str) -> None:
        """Cursor and work commit together. Separately would mean a cursor that points
        past work that was rolled back."""
        self.set_meta("cursor", cursor_value)
        self.db.commit()

    def commit(self) -> None:
        self.db.commit()

    # -- reads -------------------------------------------------------------
    def counts_by_path(self) -> Dict[str, int]:
        return {p: n for p, n in self.db.execute(
            "SELECT path, COUNT(*) FROM assignments GROUP BY path ORDER BY 2 DESC")}

    def why(self, asset_id: str) -> Dict[str, List[str]]:
        out: Dict[str, List[str]] = {}
        for path, reason in self.db.execute(
                "SELECT path, reason FROM evidence WHERE asset_id=? ORDER BY weight DESC",
                (asset_id,)):
            out.setdefault(path, []).append(reason)
        return out

    def review_queue(self, limit: int = 50):
        return self.db.execute(
            """SELECT a.asset_id, p.action, p.risk, p.note, p.why
               FROM assets a JOIN proposals p USING(asset_id)
               WHERE a.needs_review=1 OR p.action='review'
               ORDER BY a.created_at DESC LIMIT ?""", (limit,)).fetchall()

    def stats(self) -> Dict[str, int]:
        one = lambda sql: self.db.execute(sql).fetchone()[0]
        return {
            "assets": one("SELECT COUNT(*) FROM assets"),
            "assignments": one("SELECT COUNT(*) FROM assignments"),
            "needs_review": one("SELECT COUNT(*) FROM assets WHERE needs_review=1"),
            "auto_applicable": one("SELECT COUNT(*) FROM proposals WHERE auto_applicable=1"),
            "protected": one(f"SELECT COUNT(*) FROM assets WHERE risk>={int(NEVER_DELETE_AT_OR_ABOVE)}"),
            "relations": one("SELECT COUNT(DISTINCT group_key) FROM relations"),
        }

    def size_bytes(self) -> int:
        total = 0
        for suffix in ("", "-wal", "-shm"):
            try:
                total += os.path.getsize(self.path + suffix)
            except OSError:
                pass
        return total

    def close(self) -> None:
        self.db.commit()
        self.db.close()
