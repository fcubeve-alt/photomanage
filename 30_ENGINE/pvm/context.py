# -*- coding: utf-8 -*-
"""
Library-level context — the facts no single photo contains.

"Is this a travel photo?" cannot be answered from one asset. It needs to know where
this person usually is, and whether this capture sits inside a run of days spent
somewhere else. Same for "is this an unusual place?" and "who is in most of my
photos?". Those are properties of the library, so they are computed once from the
cheapest signals available (Tier.METADATA only) and handed to the per-asset rules.

Two design commitments:

1. **Home is learned, never asked.** The Constitution's premise is a library that
   catalogues itself; a setup wizard asking "where do you live?" fails that on the
   first screen. Home is the densest cluster of night-and-weekend captures.

2. **Learned facts carry confidence and provenance.** A trip window derived from
   nine photos is not the same claim as one derived from nine hundred, and §11 says
   an inference must say which it is. `sample_size` travels with every fact so a
   downstream rule can refuse to lean on a thin one.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Dict, Iterable, List, Optional, Tuple

from .signals import AssetSignals, GeoFix

# A capture this far from the home cluster is somewhere else, not a longer walk.
AWAY_KM = 120.0
# Below this many days away, it is a day out, not a trip worth its own entry.
MIN_TRIP_DAYS = 2
# Coordinates are rounded to a grid before clustering. ~1 km is coarse enough that a
# phone's GPS jitter does not split one home into four, and fine enough that the next
# town does not merge into it.
GRID = 0.01


@dataclass(frozen=True)
class Trip:
    city: Optional[str]
    country: Optional[str]
    start: date
    end: date
    asset_count: int

    @property
    def label(self) -> str:
        """`Travel > Tokyo · Apr 2025` — the shape the canonical tree already uses."""
        where = self.city or self.country or "Away"
        return f"{where} · {self.start.strftime('%b %Y')}"

    def contains(self, when: datetime) -> bool:
        return self.start <= when.date() <= self.end


@dataclass
class LibraryContext:
    home: Optional[GeoFix] = None
    home_city: Optional[str] = None
    home_country: Optional[str] = None
    home_sample_size: int = 0
    trips: List[Trip] = field(default_factory=list)
    known_people: List[str] = field(default_factory=list)
    year_range: Tuple[Optional[int], Optional[int]] = (None, None)
    asset_count: int = 0

    @property
    def home_confidence(self) -> float:
        """Thin evidence must not read as a confident home. 20 captures is a guess;
        several hundred is a residence."""
        if not self.home_sample_size:
            return 0.0
        return min(0.95, 0.4 + self.home_sample_size / 400.0)

    def is_away(self, geo: Optional[GeoFix]) -> bool:
        if geo is None or self.home is None:
            return False
        return geo.km_to(self.home) > AWAY_KM

    def trip_for(self, when: Optional[datetime], geo: Optional[GeoFix]) -> Optional[Trip]:
        if when is None or not self.is_away(geo):
            return None
        for t in self.trips:
            if t.contains(when):
                return t
        return None


def build_context(assets: Iterable[AssetSignals]) -> LibraryContext:
    """One pass, metadata only. Nothing here decodes a pixel."""
    ctx = LibraryContext()

    cells: Counter = Counter()
    cell_names: Dict[Tuple[float, float], Counter] = defaultdict(Counter)
    home_candidates: Counter = Counter()
    people: Counter = Counter()
    years: List[int] = []
    located: List[Tuple[datetime, GeoFix, Optional[str], Optional[str]]] = []

    for a in assets:
        ctx.asset_count += 1
        if a.created_at:
            years.append(a.created_at.year)
        for f in a.face_clusters:
            if f.name:
                people[f.name] += 1
        if a.geo is None or a.geo.source != "exif":
            continue

        cell = (round(a.geo.lat / GRID) * GRID, round(a.geo.lon / GRID) * GRID)
        cells[cell] += 1
        if a.place:
            cell_names[cell][(a.place.country, a.place.city)] += 1
        # Home is where the evenings and weekends are. Daytime weekday captures are
        # where the office is, and an office is not home.
        if a.created_at:
            off_hours = a.created_at.hour >= 19 or a.created_at.hour <= 7
            weekend = a.created_at.weekday() >= 5
            if off_hours or weekend:
                home_candidates[cell] += 1
            located.append((a.created_at, a.geo, a.place.country if a.place else None,
                            a.place.city if a.place else None))

    if years:
        ctx.year_range = (min(years), max(years))
    ctx.known_people = [n for n, _ in people.most_common()]

    pool = home_candidates or cells
    if pool:
        cell, count = pool.most_common(1)[0]
        ctx.home = GeoFix(lat=cell[0], lon=cell[1], source="inferred")
        ctx.home_sample_size = count
        if cell_names[cell]:
            (country, city), _ = cell_names[cell].most_common(1)[0]
            ctx.home_country, ctx.home_city = country, city

    ctx.trips = _find_trips(located, ctx)
    return ctx


def _find_trips(located, ctx: LibraryContext) -> List[Trip]:
    """A trip is a run of consecutive days spent away from home. Gaps of a day are
    tolerated — a trip does not end because nobody took a photo on the Tuesday."""
    if ctx.home is None:
        return []

    away_days: Dict[date, Counter] = defaultdict(Counter)
    for when, geo, country, city in located:
        if geo.km_to(ctx.home) > AWAY_KM:
            away_days[when.date()][(country, city)] += 1
    if not away_days:
        return []

    trips: List[Trip] = []
    run: List[date] = []

    def close(run_days: List[date]):
        if len(run_days) < MIN_TRIP_DAYS:
            return
        names: Counter = Counter()
        total = 0
        for d in run_days:
            names.update(away_days[d])
            total += sum(away_days[d].values())
        (country, city), _ = names.most_common(1)[0]
        trips.append(Trip(city=city, country=country, start=run_days[0],
                          end=run_days[-1], asset_count=total))

    for d in sorted(away_days):
        if run and (d - run[-1]).days > 2:
            close(run)
            run = []
        run.append(d)
    close(run)
    return trips
