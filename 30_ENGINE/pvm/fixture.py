# -*- coding: utf-8 -*-
"""
THE SHARED FIXTURE — one library, both implementations.

The engine here is the reference implementation and the Swift in `40_APP` is what
ships. Both have tests. Neither test suite proves they *agree*, and that is the
failure that matters: the app files a passport somewhere the engine would not, both
suites stay green, and every number measured on the engine quietly stops describing
the product.

So the fixture is defined once, here, and emitted as JSON. `generate_shared.py` writes
it into the Swift package along with this engine's classification of it, and a Swift
conformance test replays it and compares. A divergence fails the build on the side
that moved.

The library is deliberately shaped like the hard cases rather than the easy ones — a
passport, four near-identical contract pages, an expired pickup code, a burst whose
fifth frame differs, a byte-identical re-download, a twelve-day trip. If the two
implementations agree on these, they agree where it counts.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

from .signals import AssetSignals, FaceCluster, GeoFix, PlaceName, SceneLabel

LONDON = (51.5074, -0.1278)
TOKYO = (35.6762, 139.6503)
UK = ("United Kingdom", "London")
JAPAN = ("Japan", "Tokyo")


def _fnv1a(text: str) -> int:
    """The same hash the Swift fixture uses, so both sides get identical dHashes.
    Python's own `hash()` is salted per process and would make the fixture
    non-deterministic — a mistake already made once on the Swift side."""
    h = 0xCBF29CE484222325
    for byte in text.encode("utf-8"):
        h ^= byte
        h = (h * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return h


def _at(y: int, m: int, d: int, h: int = 12) -> datetime:
    return datetime(y, m, d, h)


def build() -> List[AssetSignals]:
    out: List[AssetSignals] = []

    def add(asset_id: str, **kw) -> None:
        s = AssetSignals(asset_id)
        s.pixel_w, s.pixel_h, s.byte_size = 4032, 3024, 520_000
        s.content_hash = f"sha::{asset_id}"
        s.dhash = _fnv1a(asset_id) | 1
        for key, value in kw.items():
            setattr(s, key, value)
        out.append(s)

    # Documents — where being wrong is most expensive (§6 R5).
    add("doc-passport", created_at=_at(2025, 6, 18), source="camera", ocr_ran=True,
        ocr_text="PASSPORT", geo=GeoFix(*LONDON), place=PlaceName(*UK, 0.9))
    add("doc-id-front", created_at=_at(2025, 6, 18, 14), source="camera", ocr_ran=True,
        ocr_text="ID CARD — FRONT", geo=GeoFix(*LONDON), place=PlaceName(*UK, 0.9))
    # Contract pages: near-identical to look at, unrelated in content.
    for page in range(1, 5):
        add(f"doc-contract-{page}", created_at=_at(2025, 3, 2, 9 + page), source="camera",
            ocr_ran=True, ocr_text=f"CONTRACT — PAGE {page} OF 4",
            dhash=0x99AABBCCDDEEFF00 | page)

    # Purchases — cross-listed into Documents by the tree: one asset, two entries.
    add("buy-receipt", created_at=_at(2026, 3, 15), source="camera", ocr_ran=True,
        ocr_text="RECEIPT — HEADPHONES £129.00")
    add("buy-order", created_at=_at(2026, 3, 14), is_screenshot=True, source="screenshot",
        pixel_w=1170, pixel_h=2532, ocr_ran=True, ocr_text="ORDER CONFIRMATION — HEADPHONES")

    # Screenshots: one expired, two not.
    add("shot-pickup-old", created_at=_at(2025, 1, 6), is_screenshot=True, source="screenshot",
        pixel_w=1170, pixel_h=2532, ocr_ran=True, ocr_text="PICKUP CODE 4417 — LOCKER B12")
    add("shot-chat", created_at=_at(2026, 2, 2), is_screenshot=True, source="screenshot",
        pixel_w=1170, pixel_h=2532, ocr_ran=True, ocr_text="delivered  read 14:02  whatsapp")
    add("shot-plain", created_at=_at(2026, 2, 3), is_screenshot=True, source="screenshot",
        pixel_w=1170, pixel_h=2532, ocr_ran=True, ocr_text="SCREENSHOT")

    # People. §6 puts these at R3 Personal — conservative, never auto-removed.
    for i in range(6):
        add(f"person-anna-{i}", created_at=_at(2025, 8, 3 + i), source="camera",
            geo=GeoFix(*LONDON), place=PlaceName(*UK, 0.9),
            face_clusters=[FaceCluster("c-anna", "Anna", 0.3)])
    add("person-group", created_at=_at(2025, 9, 9), source="camera",
        face_clusters=[FaceCluster("c-anna", "Anna"), FaceCluster("c-ben", "Ben")])

    # Enough evening captures in London for it to be learned as home...
    for i in range(40):
        add(f"home-{i}", created_at=_at(2025, 1, 1) + timedelta(days=i, hours=21),
            source="camera", geo=GeoFix(*LONDON), place=PlaceName(*UK, 0.9))
    # ...and a run of days in Tokyo long enough to be a trip rather than a day out.
    for i in range(12):
        add(f"tokyo-{i}", created_at=_at(2025, 4, 11 + i // 2, 10 + i % 8), source="camera",
            geo=GeoFix(*TOKYO), place=PlaceName(*JAPAN, 0.9))

    # A burst where frame 4 is genuinely different (§8) — it must survive.
    for i in range(5):
        add(f"burst-{i}", created_at=_at(2026, 4, 24, 16) + timedelta(seconds=i),
            source="camera", geo=GeoFix(*LONDON), place=PlaceName(*UK, 0.9),
            burst_id="burst-A",
            dhash=0x0F0F0F0F0F0F0F0F if i == 4 else (0xF0F0F0F0F0F0F0F0 | i))

    # A byte-identical re-download. §6 R0 — the one case that may be tidied
    # automatically, because an identical copy demonstrably remains.
    add("meme-original", created_at=_at(2025, 10, 16), source="downloaded",
        content_hash="sha::meme", scene_labels=[SceneLabel("meme", 0.9)])
    add("meme-copy", created_at=_at(2025, 11, 20), source="downloaded",
        content_hash="sha::meme", scene_labels=[SceneLabel("meme", 0.9)])

    # An asset nothing can place. The engine must say so rather than invent a home.
    add("mystery", created_at=_at(2026, 5, 5))
    return out


def to_json() -> List[Dict[str, Any]]:
    """The wire format both implementations read. Kept flat and explicit — a fixture
    whose serialisation needs interpreting is a second place for the two sides to
    disagree."""
    rows = []
    for a in build():
        rows.append({
            "assetID": a.asset_id,
            "createdAt": a.created_at.isoformat() if a.created_at else None,
            "pixelW": a.pixel_w, "pixelH": a.pixel_h, "byteSize": a.byte_size,
            "isScreenshot": a.is_screenshot,
            "source": a.source,
            "burstID": a.burst_id,
            "lat": a.geo.lat if a.geo else None,
            "lon": a.geo.lon if a.geo else None,
            "country": a.place.country if a.place else None,
            "city": a.place.city if a.place else None,
            "contentHash": a.content_hash,
            "dhash": str(a.dhash) if a.dhash is not None else None,
            "ocrRan": a.ocr_ran, "ocrText": a.ocr_text,
            "sceneLabels": [{"identifier": s.identifier, "confidence": s.confidence}
                            for s in a.scene_labels],
            "faceClusters": [{"clusterID": f.cluster_id, "name": f.name}
                             for f in a.face_clusters],
        })
    return rows
