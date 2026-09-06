# -*- coding: utf-8 -*-
"""
What the classifier returns — and the red line it enforces.

Constitution safety red line, active since Tier 0: **every suggestion must be able to
explain why.** That is enforced here as a constructor check rather than a convention,
because a convention is exactly the thing that erodes at 2am. An `Assignment` with no
evidence cannot be built. A `Classification` cannot be finalised with an unexplained
path in it.

Confidence is combined noisy-or: independent pieces of evidence each reduce the
remaining doubt. Two weak signals that agree are worth more than either alone, and no
finite amount of weak evidence reaches certainty — which is the behaviour we want,
because certainty is what authorises destructive action.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

from .signals import Tier
from . import taxonomy

# Below this, the engine has an opinion but not a decision: the asset is filed where
# the evidence supports and flagged for the user rather than asserted.
REVIEW_FLOOR = 0.55

# No single rule may claim certainty. There is always the photo we have not seen.
MAX_CONFIDENCE = 0.99


@dataclass(frozen=True)
class Evidence:
    """One reason, in the user's language, traceable to one signal."""
    signal: str          # which field of AssetSignals this came from
    tier: Tier           # what it cost to acquire
    weight: float        # 0..1 — how much doubt this alone removes
    reason: str          # shown to the user verbatim; write it for them, not for a log

    def __post_init__(self):
        if not 0.0 < self.weight <= 1.0:
            raise ValueError(f"evidence weight must be in (0,1]: {self.weight}")
        if not self.reason.strip():
            raise ValueError("evidence without a reason is not evidence")


def combine(weights: Iterable[float]) -> float:
    doubt = 1.0
    for w in weights:
        doubt *= (1.0 - w)
    return min(MAX_CONFIDENCE, 1.0 - doubt)


@dataclass
class Assignment:
    """One place this asset belongs, with the reasons it belongs there."""
    path: str
    evidence: List[Evidence]
    is_primary: bool = False
    cross_listed_from: Optional[str] = None

    def __post_init__(self):
        taxonomy.require_node(self.path)
        if not self.evidence:
            raise ValueError(
                f"assignment to {self.path!r} carries no evidence. Every suggestion "
                "must be able to explain why — an unexplained assignment is a bug, "
                "not a low-confidence one."
            )

    @property
    def confidence(self) -> float:
        return combine(e.weight for e in self.evidence)

    @property
    def max_tier(self) -> Tier:
        return max(e.tier for e in self.evidence)

    @property
    def needs_review(self) -> bool:
        return self.confidence < REVIEW_FLOOR

    def why(self) -> str:
        """The §-red-line answer, in one line, for a human."""
        return "; ".join(e.reason for e in sorted(self.evidence, key=lambda e: -e.weight))


@dataclass
class Classification:
    asset_id: str
    assignments: List[Assignment] = field(default_factory=list)
    # The most expensive signal the engine actually needed. L1-B: if this is
    # METADATA for most of the library, the engine is cheap to run; if it is FACES
    # for everything, the design has failed regardless of its accuracy.
    tier_used: Tier = Tier.METADATA
    notes: List[str] = field(default_factory=list)

    def add(self, assignment: Assignment) -> "Classification":
        for existing in self.assignments:
            if existing.path == assignment.path:
                existing.evidence.extend(assignment.evidence)
                return self
        self.assignments.append(assignment)
        self.tier_used = max(self.tier_used, assignment.max_tier)
        return self

    @property
    def primary(self) -> Optional[Assignment]:
        primaries = [a for a in self.assignments if a.is_primary]
        if primaries:
            return max(primaries, key=lambda a: a.confidence)
        content = [a for a in self.assignments if taxonomy.root_of(a.path) != "Timeline"]
        return max(content, key=lambda a: a.confidence) if content else None

    @property
    def paths(self) -> List[str]:
        return [a.path for a in self.assignments]

    @property
    def needs_review(self) -> bool:
        p = self.primary
        return p is None or p.needs_review

    def explain(self) -> Dict[str, str]:
        return {a.path: a.why() for a in self.assignments}
