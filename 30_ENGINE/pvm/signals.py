# -*- coding: utf-8 -*-
"""
THE INPUT CONTRACT.

`AssetSignals` is everything the classifier is allowed to see. The rule that makes
this file worth having: **a field may exist here only if a real iOS device can
produce it for a real photo.** PhotoKit metadata, a Vision OCR string, Vision scene
labels, Vision face clusters, a hash we computed ourselves. Nothing else.

That constraint is the whole defence against a classifier that scores beautifully in
evaluation and cannot run on a phone. If a rule needs a signal that is not in this
struct, the honest answer is that the rule cannot be implemented yet — not that the
struct should quietly grow a field the device cannot fill.

Every signal carries what it cost to acquire (`Tier`), because the engine is required
to stop escalating the moment the answer stops changing (L1-B, Minimum Necessary
Inference). A classifier that always reads every signal is not cheaper to be right
with; it is just more expensive to be wrong with.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import List, Optional, Tuple


class Tier(IntEnum):
    """What a signal costs, in ascending order — and the engine escalates in exactly
    this order, stopping as soon as the answer stops changing.

    The ordering is not alphabetical or conceptual. OCR sits last because C-1 predicts
    it dominates per-asset cost by roughly an order of magnitude over the visual
    stages, which is why the harness gates it rather than running it universally. If
    the T0-A scale sweep contradicts that, this enum is what moves."""
    METADATA = 0   # free — already in the PhotoKit row
    HASH = 1       # one thumbnail decode plus a few hundred bytes of arithmetic
    VISUAL = 2     # scene labels / feature print
    FACES = 3      # face detection and cluster lookup
    TEXT = 4       # gated OCR — the expensive one C-1 exists to ration

    @property
    def label(self) -> str:
        return {0: "metadata", 1: "hash", 2: "visual", 3: "faces", 4: "ocr"}[int(self)]


@dataclass(frozen=True)
class GeoFix:
    """A GPS fix carried by the asset itself. §11: an inferred location must declare
    lower confidence than a measured one, and the two must never be conflated."""
    lat: float
    lon: float
    accuracy_m: float = 65.0
    source: str = "exif"          # "exif" (measured) | "inferred" (from neighbours)

    @property
    def confidence(self) -> float:
        return 1.0 if self.source == "exif" else 0.6

    def km_to(self, other: "GeoFix") -> float:
        r = 6371.0
        p1, p2 = math.radians(self.lat), math.radians(other.lat)
        dp = p2 - p1
        dl = math.radians(other.lon - self.lon)
        a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
        return 2 * r * math.asin(min(1.0, math.sqrt(a)))


@dataclass(frozen=True)
class PlaceName:
    """Reverse-geocoded names. Separate from GeoFix because geocoding can fail while
    the coordinates remain perfectly good."""
    country: Optional[str] = None
    city: Optional[str] = None
    confidence: float = 0.0


@dataclass(frozen=True)
class SceneLabel:
    identifier: str
    confidence: float


@dataclass(frozen=True)
class FaceCluster:
    """Vision gives a cluster; the user gives it a name. An unnamed cluster is still
    evidence that a person is present — that alone changes the risk class."""
    cluster_id: str
    name: Optional[str] = None
    area_fraction: float = 0.0


@dataclass
class AssetSignals:
    asset_id: str

    # ---- Tier.METADATA -----------------------------------------------------
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    pixel_w: int = 0
    pixel_h: int = 0
    byte_size: int = 0
    media_type: str = "image"              # "image" | "video"
    duration_s: float = 0.0
    is_screenshot: bool = False
    is_screen_recording: bool = False
    is_panorama: bool = False
    is_live_photo: bool = False
    # Where the pixels came from. On device this is derived from PHAssetResource
    # and the absence of camera EXIF, not guessed from the filename alone.
    source: str = "unknown"                # camera | screenshot | downloaded | shared | unknown
    burst_id: Optional[str] = None
    filename: Optional[str] = None
    geo: Optional[GeoFix] = None
    place: Optional[PlaceName] = None

    # ---- Tier.HASH ---------------------------------------------------------
    content_hash: Optional[str] = None     # exact bytes
    dhash: Optional[int] = None            # 64-bit perceptual

    # ---- Tier.TEXT ---------------------------------------------------------
    ocr_ran: bool = False
    ocr_text: str = ""

    # ---- Tier.VISUAL -------------------------------------------------------
    scene_labels: List[SceneLabel] = field(default_factory=list)
    embedding: Optional[bytes] = None

    # ---- Tier.FACES --------------------------------------------------------
    face_clusters: List[FaceCluster] = field(default_factory=list)

    # ---- derived, free -----------------------------------------------------
    @property
    def aspect_ratio(self) -> float:
        return (self.pixel_h / self.pixel_w) if self.pixel_w else 0.0

    @property
    def megapixels(self) -> float:
        return self.pixel_w * self.pixel_h / 1e6

    @property
    def year(self) -> Optional[int]:
        return self.created_at.year if self.created_at else None

    @property
    def named_people(self) -> List[str]:
        return sorted({f.name for f in self.face_clusters if f.name})

    @property
    def has_usable_dhash(self) -> bool:
        """FC-1a, and this is not pedantry: `dHash` returns 0 both for a whole class
        of ordinary images and for every hash failure. Treating 0 as a value would
        link unrelated photos as duplicates and make a failed hash indistinguishable
        from a confident match. Zero is therefore not a hash here — it is a miss."""
        return self.dhash is not None and self.dhash != 0


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")
