# -*- coding: utf-8 -*-
"""
INGESTION PLANNING — how a large library gets catalogued without taking the phone away.

Owner ruling (DEC-029): a new user with 100k photos does not have to wait for one long
run. Pace it, tell them what is happening, offer choices, and stop when they pick the
phone up. That reframes A1 from a pass/fail physics question into a scheduling one.

The measured data says the idea works, and says something better than the version it
was proposed as. Breadth is nearly free and depth is what costs:

  * A **breadth pass** reads PhotoKit metadata only — capture date, GPS, media subtype.
    No pixel is decoded, so the per-asset cost is a SQLite write: 0.18-0.28 ms measured.
    100k assets in under 30 seconds. That alone yields Timeline, Places, Travel and
    Screenshots-by-subtype, which is a browsable library on the first screen.
  * A **depth pass** decodes a thumbnail and runs OCR, embedding and faces: 105-154 ms
    measured, three to four orders of magnitude more. That is the part worth pacing.

So the plan is never "wait N days for your library". It is "your library is there in a
minute, and it gets deeper while you use the phone".

WHAT THIS DOES NOT SOLVE, and the point must not be lost: pacing makes **A3
(survivability) more critical, not less.** A 90-minute run that loses its place costs
90 minutes. A fifty-day plan that loses its place is a product that never finishes. And
`BGProcessingTask` is scheduled at the system's discretion — "2,000 a day" is a request,
not a guarantee, so the plan must be written to survive days when the system grants
nothing. Every number here is a projection from a resumable cursor, never a promise.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional

# Measured on the iOS Simulator, 2026-09-06, both runs.
# `20_TIER0/evidence/T0A_SCALE_SIMULATOR_2026-09-06.md`. A range, not a figure: two
# runs of identical code came back 1.47x apart, so the planner carries the band and
# quotes the pessimistic end to the user.
BREADTH_MS = (0.18, 0.28)
DEPTH_MS = (104.7, 154.1)

# How much uninterrupted work is reasonable to ask of a phone in one background grant.
# Not measured — a product judgement, and the one most worth arguing with.
COMFORTABLE_SESSION_MIN = 6
# What the system might actually grant in a day, pessimistically. Also a judgement.
SESSIONS_PER_DAY = 2


@dataclass(frozen=True)
class Phase:
    name: str
    assets: int
    per_asset_ms: float
    what_the_user_gets: str

    @property
    def seconds(self) -> float:
        return self.assets * self.per_asset_ms / 1000

    def human(self) -> str:
        s = self.seconds
        if s < 90:
            return f"{s:.0f} seconds"
        if s < 5400:
            return f"{s/60:.0f} minutes"
        return f"{s/3600:.1f} hours"


@dataclass
class Option:
    """One way to finish, offered to the user rather than chosen for them."""
    key: str
    label: str
    daily_assets: int
    days: int
    daily_work_min: float
    caveat: str = ""


@dataclass
class Plan:
    library_size: int
    breadth: Phase
    depth_assets: int
    options: List[Option] = field(default_factory=list)
    recommended: str = ""
    notes: List[str] = field(default_factory=list)

    def user_message(self) -> str:
        """What the user is actually told. Written for them, not for a log — and it
        leads with what they get, not with what we are doing to their phone."""
        lines = [
            f"Your library has {self.library_size:,} photos.",
            f"The shelves are ready in about {self.breadth.human()} — dates, places, "
            "trips and screenshots are sorted straight away.",
            "Recognising what is inside them takes longer, so it happens in the "
            "background while you use your phone. You can change or pause this any time.",
        ]
        return "\n".join(lines)

    def option(self, key: str) -> Optional[Option]:
        for o in self.options:
            if o.key == key:
                return o
        return None


def plan_ingestion(library_size: int, *, pessimistic: bool = True,
                   daily_assets: Optional[int] = None) -> Plan:
    """Build a plan from measured costs. `pessimistic` quotes the slower of the two
    measured runs, which is what a user should be promised."""
    idx = 1 if pessimistic else 0
    breadth_ms, depth_ms = BREADTH_MS[idx], DEPTH_MS[idx]

    breadth = Phase(
        "breadth", library_size, breadth_ms,
        "dates, places, trips and screenshots — a library you can browse")

    per_session = int(COMFORTABLE_SESSION_MIN * 60_000 / depth_ms)
    gentle_daily = per_session * SESSIONS_PER_DAY

    def opt(key, label, daily, caveat=""):
        daily = max(1, daily)
        return Option(key, label, daily, math.ceil(library_size / daily),
                      daily * depth_ms / 60_000, caveat)

    options = [
        opt("gentle", "Quietly in the background", daily_assets or gentle_daily,
            "Uses only the time the system gives us. Some days it gives us none."),
        opt("overnight", "Overnight while charging", gentle_daily * 4,
            "Needs the phone on charge and idle. Fastest hands-off option."),
        opt("now", "All at once, now",
            max(1, int(library_size)),
            "The phone will be busy and will warm up. Best left plugged in."),
    ]

    plan = Plan(library_size=library_size, breadth=breadth,
                depth_assets=library_size, options=options)

    one_go_h = library_size * depth_ms / 3.6e6
    plan.recommended = "now" if one_go_h <= 0.5 else ("overnight" if one_go_h <= 8 else "gentle")

    plan.notes.append(
        f"depth pass in one go would be {one_go_h:.1f} h at {depth_ms:.0f} ms/asset "
        f"({'slower' if pessimistic else 'faster'} of the two measured runs)")
    if one_go_h > 1.5:
        plan.notes.append(
            "too long for a foreground run — this library must be paced, and pacing "
            "means the resume cursor is load-bearing (A3)")
    plan.notes.append(
        "every figure is a projection from a resumable cursor, never a promise: "
        "background time is granted by the system, not scheduled by us")
    return plan


def progress_report(done: int, total: int, per_asset_ms: Optional[float] = None) -> str:
    """What to show while it runs. Percentages alone are a progress bar; what a user
    wants to know is whether their library is usable yet and when it will be done."""
    per_asset_ms = per_asset_ms or DEPTH_MS[1]
    if total <= 0:
        return "nothing to do"
    pct = done / total * 100
    remaining_h = (total - done) * per_asset_ms / 3.6e6
    if done >= total:
        return f"All {total:,} photos have been looked at."
    when = (f"{remaining_h*60:.0f} minutes" if remaining_h < 1.5
            else f"about {remaining_h:.0f} hours of background time")
    return (f"{done:,} of {total:,} photos looked at ({pct:.0f}%). "
            f"Everything is already findable by date, place and trip; "
            f"the rest needs {when}.")
