# -*- coding: utf-8 -*-
"""
INFERRING A PLACE — Constitution §11, L1-B Minimum Necessary Inference.

    无 GPS 时可以利用相邻时间照片、地标等推断，但必须保存置信度。

Half of that clause was already built and half of it was not. `GeoFix` has carried a
`source` and a `confidence` since the first version, and `classifier._places` refuses
to treat an inferred fix as a measured one — the machinery for *holding* an inference
honestly was all there. Nothing ever produced one, so an asset without GPS simply got
no place at all, and the clause was satisfied in the way an empty room satisfies a fire
code.

**What this infers from.** The photographs either side of it in time that do carry a
fix. Nothing else: no landmarks (that needs vision), no wifi, no calendar. §11 names
相邻时间照片 first and it is the one signal a metadata pass already has.

**Minimum Necessary Inference, as a ladder.** L1-B's rule is to claim the most specific
thing the evidence supports and then stop. So this does not decide "where was this
photo taken" in one step; it decides how far down the ladder the evidence reaches:

    both anchors agree on a city      → infer the city
    they agree on a country only      → infer the country, and say so
    they disagree, or are far apart   → infer nothing

The middle rung is the one that matters. Two photographs an hour apart in Shinjuku and
Yokohama are 30 km and two cities apart; the photo between them is in Japan and is not
in either city, and an engine that picks the nearer anchor has invented a fact. Saying
"Japan" is less useful and is true.

**Why one-sided inference is weaker than bracketed.** Knowing where someone was ten
minutes *before* a photo is not the same as knowing where they were ten minutes before
and ten minutes after. The first is consistent with them having got on a train. So a
one-sided inference is allowed only over a much shorter gap and carries a lower
confidence, and the reason it gives the user says which of the two it is.

**What never gets an inferred place.** Screenshots and downloads. A screenshot taken
while its owner was in Tokyo was not taken *in* Tokyo in any sense a photo shelf should
record, and `Places` is a shelf of photographs. The same assets are excluded as
anchors, for the same reason plus a practical one: they rarely carry a fix at all.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Sequence, Tuple

from .signals import AssetSignals, GeoFix, PlaceName

#: A bracketed inference — an anchor on each side — reaches this far.
MAX_GAP = timedelta(hours=2)
#: A one-sided inference reaches much less far. Someone can board a train in the gap.
MAX_ONE_SIDED_GAP = timedelta(minutes=30)
#: Anchors further apart than this were not in the same place, whatever their names say.
AGREE_KM = 25.0
#: The best an inference is ever allowed to claim, at zero gap. A measured fix is 1.0
#: and this must never approach it: §11's whole point is that the two are not the same
#: kind of fact.
BASE_CONFIDENCE = 0.80
#: The ceiling for a one-sided inference. Applied to the ceiling rather than to the
#: result, so that the reach limits below stay the actual reach — see `_confidence`.
ONE_SIDED_PENALTY = 0.7
#: The floor, reached exactly at the limits above. Below it the inference is not worth
#: making: an engine that files a photograph on a shelf it is 40% sure about has made
#: the shelf worse, not the library better.
MIN_CONFIDENCE = 0.45


@dataclass(frozen=True)
class InferredPlace:
    """A location the engine worked out rather than read, with everything needed to
    explain it. §11: 必须保存置信度 — so the confidence is a field, not a constant
    applied downstream where it could be forgotten."""
    geo: GeoFix
    place: PlaceName
    confidence: float
    #: How specific the claim is: "city" or "country". Never finer than the evidence.
    granularity: str
    #: The assets it rests on. Kept so the user can be shown them.
    anchors: Tuple[str, ...]
    #: Seconds to the furthest anchor used.
    gap_s: float
    reason: str

    @property
    def is_bracketed(self) -> bool:
        return len(self.anchors) == 2


def _eligible_target(a: AssetSignals) -> bool:
    if a.created_at is None:
        return False
    if a.geo is not None and a.geo.source == "exif":
        return False      # it has a measured fix; there is nothing to infer
    if a.is_screenshot or a.source == "downloaded":
        return False
    return True


def _eligible_anchor(a: AssetSignals) -> bool:
    return (a.created_at is not None
            and a.geo is not None and a.geo.source == "exif"
            and a.place is not None and (a.place.city or a.place.country)
            and not a.is_screenshot and a.source != "downloaded")


def _naive(when: datetime) -> datetime:
    """Anchors and targets are sorted against each other, and a library can mix
    timezone-aware and naive timestamps — comparing those raises. Everything is
    compared in UTC-naive terms, which is what the rest of the engine already does
    when it computes an age in days."""
    return when.replace(tzinfo=None) if when.tzinfo is not None else when


def infer_places(assets: Sequence[AssetSignals]) -> Dict[str, InferredPlace]:
    """One pass over the library, metadata only. Returns only what it is willing to
    claim — an asset absent from the result got no place, which is the correct outcome
    and not a failure."""
    anchors = sorted((a for a in assets if _eligible_anchor(a)),
                     key=lambda a: _naive(a.created_at))
    if not anchors:
        return {}
    times = [_naive(a.created_at) for a in anchors]

    out: Dict[str, InferredPlace] = {}
    for target in assets:
        if not _eligible_target(target):
            continue
        when = _naive(target.created_at)
        before, after = _neighbours(anchors, times, when, target.asset_id)
        inferred = _decide(when, before, after)
        if inferred is not None:
            out[target.asset_id] = inferred
    return out


def _neighbours(anchors, times, when: datetime, target_id: str):
    """The nearest anchor on each side. Linear scan from a bisect, so an anchor that is
    the target itself (possible only if the caller passed duplicates) is stepped over
    rather than used to confirm itself."""
    import bisect
    i = bisect.bisect_left(times, when)

    before = None
    j = i - 1
    while j >= 0:
        if anchors[j].asset_id != target_id:
            before = anchors[j]
            break
        j -= 1

    after = None
    j = i
    while j < len(anchors):
        if anchors[j].asset_id != target_id:
            after = anchors[j]
            break
        j += 1
    return before, after


def _decide(when: datetime, before, after) -> Optional[InferredPlace]:
    usable = []
    for anchor in (before, after):
        if anchor is None:
            continue
        gap = abs((_naive(anchor.created_at) - when).total_seconds())
        usable.append((anchor, gap))

    if len(usable) == 2:
        (a, gap_a), (b, gap_b) = usable
        if max(gap_a, gap_b) <= MAX_GAP.total_seconds():
            return _from_pair(a, b, max(gap_a, gap_b))
        # One side is too far away to help. Fall through and try the other alone —
        # a distant anchor must not veto a close one.
        usable = [(x, g) for x, g in usable if g <= MAX_ONE_SIDED_GAP.total_seconds()]
        if len(usable) == 2:
            usable = [min(usable, key=lambda t: t[1])]

    if len(usable) == 1:
        anchor, gap = usable[0]
        if gap <= MAX_ONE_SIDED_GAP.total_seconds():
            return _from_single(anchor, gap)
    return None


def _confidence(gap_s: float, limit_s: float, ceiling: float = BASE_CONFIDENCE) -> float:
    """Linear from `ceiling` at no gap down to `MIN_CONFIDENCE` at the limit.

    The first version decayed towards zero and then refused anything under
    `MIN_CONFIDENCE`, which meant `MAX_GAP = 2 hours` was not the reach: the real
    cut-off was 52 minutes, and a one-sided inference was refused at every gap
    including zero. The constants did not describe the behaviour — which is the same
    defect as a comment that lies, in a file whose whole subject is not claiming more
    than the evidence supports. Interpolating to the floor makes each limit the limit.
    """
    span = max(0.0, min(1.0, gap_s / limit_s))
    raw = ceiling - (ceiling - MIN_CONFIDENCE) * span
    # Half away from zero, spelled out, because the two implementations must agree to
    # the digit. Python's `round` is banker's and Swift's `.rounded()` is half-away —
    # this project has already shipped one cross-implementation divergence from exactly
    # that pair (190.5 seconds formatting as 03:10 on one side and 03:11 on the other).
    return math.floor(raw * 1000 + 0.5) / 1000


def _from_pair(a: AssetSignals, b: AssetSignals, gap_s: float) -> Optional[InferredPlace]:
    if a.geo.km_to(b.geo) > AGREE_KM:
        # The subject was moving. A photo between London and Paris is in neither, and
        # picking the nearer one would be an invention.
        return None
    confidence = _confidence(gap_s, MAX_GAP.total_seconds())
    if confidence < MIN_CONFIDENCE:
        return None

    lat = (a.geo.lat + b.geo.lat) / 2
    lon = (a.geo.lon + b.geo.lon) / 2
    geo = GeoFix(lat=lat, lon=lon, accuracy_m=max(a.geo.accuracy_m, b.geo.accuracy_m),
                 source="inferred")
    minutes = int(round(gap_s / 60))

    if a.place.city and a.place.city == b.place.city and a.place.country == b.place.country:
        place = PlaceName(country=a.place.country, city=a.place.city, confidence=confidence)
        reason = (f"no location was saved with this photo; the photos taken within "
                  f"{minutes} minutes either side were both in {a.place.city}")
        return InferredPlace(geo, place, confidence, "city",
                             (a.asset_id, b.asset_id), gap_s, reason)

    if a.place.country and a.place.country == b.place.country:
        # The middle rung of the ladder: the country is supported, the city is not.
        place = PlaceName(country=a.place.country, city=None, confidence=confidence)
        cities = " and ".join(sorted({c for c in (a.place.city, b.place.city) if c}))
        detail = f" — they were in {cities}, so the city is not certain" if cities else ""
        reason = (f"no location was saved with this photo; the photos taken within "
                  f"{minutes} minutes either side were both in {a.place.country}{detail}")
        return InferredPlace(geo, place, confidence, "country",
                             (a.asset_id, b.asset_id), gap_s, reason)
    return None


def _from_single(anchor: AssetSignals, gap_s: float) -> Optional[InferredPlace]:
    confidence = _confidence(gap_s, MAX_ONE_SIDED_GAP.total_seconds(),
                             ceiling=BASE_CONFIDENCE * ONE_SIDED_PENALTY)
    if confidence < MIN_CONFIDENCE:
        return None
    geo = GeoFix(lat=anchor.geo.lat, lon=anchor.geo.lon,
                 accuracy_m=anchor.geo.accuracy_m, source="inferred")
    where = anchor.place.city or anchor.place.country
    place = PlaceName(country=anchor.place.country,
                      city=anchor.place.city, confidence=confidence)
    minutes = int(round(gap_s / 60))
    reason = (f"no location was saved with this photo; the nearest photo that has one "
              f"was taken {minutes} minutes away, in {where}")
    return InferredPlace(geo, place, confidence, "city" if anchor.place.city else "country",
                         (anchor.asset_id,), gap_s, reason)
