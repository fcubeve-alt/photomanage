# -*- coding: utf-8 -*-
"""
MANIFEST -> AssetSignals, with the honesty boundary enforced in code.

The 10,000-asset test library was built for the T0-B retrieval study, not for
classifier evaluation. It carries ground-truth labels, which makes it the only
labelled corpus this project has — and makes it very easy to cheat with by accident.

So the boundary is a guard, not a comment. `_Row` raises on any field that is an
ANSWER rather than a SIGNAL. If a mapping rule ever reaches for `category_path`, the
adapter crashes instead of quietly producing a perfect score.

ALLOWED — each of these is a thing a real iPhone genuinely produces:
    id                  the asset's local identifier
    captured_at         EXIF capture date
    is_screenshot       PHAssetMediaSubtype.photoScreenshot
    place               a GPS fix, plus reverse geocoding
    people              Vision face clusters the user has named
    placeholder_text    the text actually drawn into the generated image, which is
                        what an OCR pass would read back
    exact_duplicate_of  byte identity — a content hash reproduces it exactly
    same_moment_group   PHAsset.burstIdentifier

FORBIDDEN — every one of these is the answer:
    category, category_path, paths, same_entity_group, hard_negative, task_target,
    note, source_query, requires_real_imagery

TWO SIGNALS THIS CORPUS SIMPLY DOES NOT CARRY, and they are not faked here:

  * **Provenance.** Nothing in the manifest says an asset was saved from another app
    rather than taken with the camera. On a device `PHAssetResource` says so plainly.
    Without it the `Downloads` branch cannot be reached, so those assets come out
    unfiled — and that is reported as a missing signal, not as a classifier error.
  * **Scene labels.** The background images are flat placeholder rectangles; there is
    no visual content for a scene classifier to recognise. So `Objects` and
    `Clothing` are unreachable here too.

Both rules exist in the engine and are covered by unit tests built from explicit
signals. What cannot be done is measure them on this corpus, and inventing a scene
label from the label would measure nothing but the adapter.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from pvm.signals import AssetSignals, FaceCluster, GeoFix, PlaceName

ALLOWED_KEYS = frozenset({
    "id", "captured_at", "is_screenshot", "place", "people",
    "placeholder_text", "exact_duplicate_of", "same_moment_group",
})
FORBIDDEN_KEYS = frozenset({
    "category", "category_path", "paths", "same_entity_group", "hard_negative",
    "task_target", "note", "source_query", "requires_real_imagery",
})


class LabelLeak(RuntimeError):
    pass


class _Row:
    """A manifest row that will not hand over the answers."""

    __slots__ = ("_d",)

    def __init__(self, d: dict):
        self._d = d

    def __getitem__(self, key):
        if key in FORBIDDEN_KEYS:
            raise LabelLeak(
                f"{key!r} is ground truth, not a signal. The adapter may not read it — "
                "a classifier evaluated on its own answers measures nothing."
            )
        if key not in ALLOWED_KEYS:
            raise LabelLeak(f"{key!r} is not on the allow-list; add it deliberately or not at all")
        return self._d.get(key)


def _stable_hash(text: str, bits: int = 64) -> int:
    return int.from_bytes(hashlib.sha256(text.encode()).digest()[: bits // 8], "big")


def _flip(value: int, n: int, salt: str) -> int:
    """Flip n bits deterministically — a near-duplicate, not an identical one."""
    out = value
    seed = _stable_hash(salt)
    for i in range(n):
        out ^= 1 << ((seed >> (i * 6)) % 64)
    return out


def load_manifest(path: str) -> List[AssetSignals]:
    with open(path, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    places: Dict[str, dict] = manifest.get("places", {})

    # Burst frames share a base appearance; one frame per burst is deliberately far
    # from the rest, because a burst where every frame is identical would never test
    # the §8 rule that protects the frame which differs.
    burst_base: Dict[str, int] = {}

    out: List[AssetSignals] = []
    for raw in manifest["assets"]:
        row = _Row(raw)
        aid = row["id"]

        created = None
        if row["captured_at"]:
            created = datetime.fromisoformat(row["captured_at"])

        geo = place_name = None
        place_key = row["place"]
        if place_key and place_key in places:
            p = places[place_key]
            geo = GeoFix(lat=p["lat"], lon=p["lon"], source="exif")
            place_name = PlaceName(country=p.get("country"), city=p.get("city"), confidence=0.9)

        faces = [FaceCluster(cluster_id=f"cluster::{name}", name=name, area_fraction=0.25)
                 for name in (row["people"] or [])]

        # Byte identity: a duplicate literally shares the original's bytes, so it
        # shares the original's content hash. Nothing modelled about that.
        dup_of = row["exact_duplicate_of"]
        content_hash = f"sha::{dup_of or aid}"

        burst = row["same_moment_group"]
        if burst:
            base = burst_base.setdefault(burst, _stable_hash("burst::" + burst))
            index = sum(1 for a in out if a.burst_id == burst)
            dhash = base if index == 0 else _flip(base, 2, f"{burst}:{index}")
            if index == 4:
                dhash = _flip(base, 22, f"{burst}:distinct")
        elif dup_of:
            dhash = _stable_hash("img::" + dup_of)
        else:
            dhash = _stable_hash("img::" + aid)

        ocr_text = row["placeholder_text"] or ""
        is_shot = bool(row["is_screenshot"])

        out.append(AssetSignals(
            asset_id=aid,
            created_at=created,
            modified_at=created,
            pixel_w=1170 if is_shot else 4032,
            pixel_h=2532 if is_shot else 3024,
            byte_size=520_000,
            media_type="image",
            is_screenshot=is_shot,
            # Not modelled: see the module docstring. The corpus carries no provenance.
            source="screenshot" if is_shot else "unknown",
            burst_id=burst,
            geo=geo,
            place=place_name,
            content_hash=content_hash,
            dhash=dhash,
            # The OCR gate that would run on device: screenshots and text-bearing
            # documents get a pass, ordinary photography does not. Mirrors OCRGate.swift.
            ocr_ran=True,
            ocr_text=ocr_text,
            scene_labels=[],       # not modelled: the corpus has no visual content
            face_clusters=faces,
        ))
    return out


def ground_truth(path: str) -> Dict[str, dict]:
    """Read separately, and only by the scorer. Keeping it out of `load_manifest`'s
    return value is what stops an accidental join between signals and answers."""
    with open(path, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    return {a["id"]: {"category": a["category"], "category_path": a["category_path"],
                      "paths": a["paths"], "hard_negative": a.get("hard_negative"),
                      "exact_duplicate_of": a.get("exact_duplicate_of"),
                      "same_entity_group": a.get("same_entity_group"),
                      # False for the ~9,864 filler assets whose leaf the generator
                      # picked with random.choice. The scorer needs this to know
                      # which labels are answers and which are coin flips.
                      "is_foreground": bool(a.get("requires_real_imagery")) and
                                       bool(a.get("source_query"))}
            for a in manifest["assets"]}
