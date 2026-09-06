# -*- coding: utf-8 -*-
"""
CHANGE-DRIVEN PROCESSING — spend intelligence only where something changed.

Owner ruling (DEC-029): do not analyse every frame of a video or every shot in a
sequence. Compare frames; where almost nothing changed, do not pay again. This is
L1-B (Information-Change-First) applied to time, and it is the same idea as FC-1
generalised from duplicate stills to sequences.

THE CORRECTION THAT MATTERS, because the obvious version of this rule silently
destroys content. "Compare each frame with the one before it, skip if similar" fails
on a slow pan: every adjacent pair is similar, so nothing is ever processed, while
frame 1 and frame 500 are different scenes entirely. Drift is invisible pairwise and
obvious cumulatively.

So every comparison is against the **last frame actually processed** — the current
keyframe — never against the immediately preceding frame. Drift then accumulates until
it crosses the threshold and opens a new keyframe, which is what we want. A hard cap on
consecutive skips catches the pathological case where drift is slower than the
threshold forever.

THREE GUARDS, each one a way this rule loses data if left off:

  * **FC-1a.** `dHash` returns 0 both for a whole class of ordinary images and for
    every hash failure. A failed hash is therefore indistinguishable from a perfect
    match, and "perfect match" is exactly what authorises a skip. An unusable hash
    always processes. Skipping on a failure is the one bug in this file that would be
    invisible in testing and unrecoverable in the field.
  * **Documents.** Page 1 and page 2 of a contract are visually near-identical and
    semantically unrelated. Visual similarity may never skip text extraction on
    document-class content — the same rule `dedup.py` applies to stills.
  * **The first and last frame** are always processed. The last frame is where a video
    ends up, and a sequence whose end was never looked at is a sequence we cannot
    describe.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from .signals import hamming

# Distance from the current keyframe that means "a new scene". Generous, because a cut
# is unambiguous in a 64-bit hash and a missed cut costs a whole scene.
CUT_BITS = 18
# Distance that means "this has drifted far enough to be worth looking at again".
DRIFT_BITS = 8
# Hard cap on consecutive skips, whatever the hashes say. Insurance against drift that
# stays under the threshold forever — a very slow pan, a gradual fade.
MAX_SKIP_RUN = 30


@dataclass(frozen=True)
class Frame:
    index: int
    dhash: Optional[int]
    timestamp_s: float = 0.0

    @property
    def has_usable_dhash(self) -> bool:
        return self.dhash is not None and self.dhash != 0


@dataclass
class FrameDecision:
    index: int
    process: bool
    reason: str
    distance_from_keyframe: Optional[int] = None


@dataclass
class SelectionResult:
    decisions: List[FrameDecision] = field(default_factory=list)
    keyframes: List[int] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.decisions)

    @property
    def processed(self) -> int:
        return sum(1 for d in self.decisions if d.process)

    @property
    def skipped(self) -> int:
        return self.total - self.processed

    @property
    def processed_fraction(self) -> float:
        return self.processed / self.total if self.total else 0.0

    def reason_counts(self) -> dict:
        out: dict = {}
        for d in self.decisions:
            if d.process:
                out[d.reason] = out.get(d.reason, 0) + 1
        return out


def select_keyframes(frames: Sequence[Frame], *, is_document: bool = False,
                     cut_bits: int = CUT_BITS, drift_bits: int = DRIFT_BITS,
                     max_skip_run: int = MAX_SKIP_RUN) -> SelectionResult:
    result = SelectionResult()
    if not frames:
        return result

    keyframe: Optional[Frame] = None
    skip_run = 0
    last_index = len(frames) - 1

    for i, f in enumerate(frames):
        def take(reason: str, distance: Optional[int] = None):
            nonlocal keyframe, skip_run
            result.decisions.append(FrameDecision(f.index, True, reason, distance))
            result.keyframes.append(f.index)
            keyframe = f
            skip_run = 0

        if i == 0:
            take("first frame")
            continue
        if i == last_index:
            take("last frame — where the sequence ends up")
            continue
        if is_document:
            # Pages look alike and say different things. This is the Document-class
            # False Merge, one dimension over.
            take("document content — visual similarity may not skip text")
            continue
        if not f.has_usable_dhash:
            take("no usable hash — a failed hash is not a match (FC-1a)")
            continue
        if keyframe is None or not keyframe.has_usable_dhash:
            take("no usable keyframe to compare against")
            continue

        distance = hamming(f.dhash, keyframe.dhash)
        if distance >= cut_bits:
            take("scene change", distance)
        elif distance >= drift_bits:
            take("drifted far enough from the last frame we looked at", distance)
        elif skip_run >= max_skip_run:
            take(f"{max_skip_run} frames skipped in a row — sampling anyway", distance)
        else:
            skip_run += 1
            result.decisions.append(
                FrameDecision(f.index, False, "unchanged since the last keyframe", distance))

    return result


# --------------------------------------------------------------------------------
# Cost model — measured stage costs, so the saving is arithmetic rather than a claim.
# `20_TIER0/evidence/T0A_SCALE_SIMULATOR_2026-09-06.md`, slower of the two runs.
# --------------------------------------------------------------------------------
DECODE_MS = 12.42
HASH_MS = 0.66
DEEP_MS = 131.08 + 9.62      # embedding + amortised OCR


@dataclass
class CostEstimate:
    frames: int
    processed: int
    naive_ms: float
    delta_ms: float

    @property
    def saved_ms(self) -> float:
        return self.naive_ms - self.delta_ms

    @property
    def saved_fraction(self) -> float:
        return self.saved_ms / self.naive_ms if self.naive_ms else 0.0

    def human(self) -> str:
        return (f"{self.processed:,}/{self.frames:,} frames processed · "
                f"{self.naive_ms/1000:.1f}s -> {self.delta_ms/1000:.1f}s "
                f"({self.saved_fraction*100:.0f}% saved)")


def estimate_cost(result: SelectionResult) -> CostEstimate:
    """Every frame still pays decode + hash — that is what the gate costs, and a gate
    whose own cost is hidden is not a measurement. Only the deep stages are skipped."""
    n = result.total
    gate_ms = n * (DECODE_MS + HASH_MS)
    return CostEstimate(
        frames=n,
        processed=result.processed,
        naive_ms=n * (DECODE_MS + HASH_MS + DEEP_MS),
        delta_ms=gate_ms + result.processed * DEEP_MS,
    )
