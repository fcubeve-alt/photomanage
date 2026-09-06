# -*- coding: utf-8 -*-
"""
RISK POLICY — what the engine is allowed to do with an asset once it knows what it is.

The Constitution's automation argument (§5–§7) is a bet: tolerate cheap, recoverable
mistakes in exchange for the library maintaining itself. That bet is only valid where
the mistake really is cheap and really is recoverable, so the policy is written from
the cost of being wrong, never from the confidence of being right.

R0 … R6, in increasing cost-of-error:

    R0  byte-identical duplicate            being wrong costs nothing — the bytes survive
    R1  near-duplicate inside one moment    being wrong loses one frame of many
    R2  transient, expires by design        being wrong loses a code that no longer works
    R3  ordinary capture                    being wrong loses a photo the user chose to take
    R4  a person is in it                   being wrong loses a memory
    R5  identity / contract / money / health  being wrong loses a document that is hard or
                                            impossible to replace
    R6  not understood                      unknown is not empty. Unknown is protected.

Three properties are enforced here rather than trusted:

* **Nothing is ever deleted by this engine.** The strongest action it can produce is a
  proposal, and `Action.DELETE` does not exist. Deletion is the platform's to perform
  and the user's to confirm (V-2), and it must land somewhere recoverable (V-5).
* **Auto-apply is R0 only**, and only for an exact-byte duplicate where an identical
  copy demonstrably remains.
* **A proposal without evidence cannot be constructed** — same red line as
  `Assignment`, enforced the same way.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from . import taxonomy
from .verdict import Classification, Evidence, REVIEW_FLOOR


class Risk(int, Enum):
    R0_EXACT_DUPLICATE = 0
    R1_NEAR_DUPLICATE = 1
    R2_TRANSIENT = 2
    R3_ORDINARY = 3
    R4_PEOPLE = 4
    R5_CRITICAL_DOCUMENT = 5
    R6_UNKNOWN = 6


class Action(str, Enum):
    """Note what is absent: there is no DELETE. The engine proposes; the platform
    deletes; the user confirms. That ordering is the safety red line, and removing a
    member from this enum is how you would have to break it."""
    KEEP = "keep"
    REVIEW = "review"                    # ask the user, we are not sure
    PROPOSE_ARCHIVE = "propose_archive"  # out of the way, still there
    PROPOSE_REMOVE = "propose_remove"    # offered for removal, always confirmable


# Roots whose contents are Protect by default, whatever else the evidence says.
PROTECTED_ROOTS = frozenset({"People"})
PROTECTED_PATHS_PREFIX = (
    "Documents > Identity",
    "Documents > Contracts",
    "Documents > Financial",
    "Documents > Medical",
)
TRANSIENT_PREFIX = ("Screenshots > Temporary",)

# A transient asset is only transient once it has expired. A verification code
# screenshot taken this morning is the most useful photo in the library; the same
# screenshot in two months is clutter. Proposing to tidy it away on the day it was
# taken is exactly the over-eager automation §7's bet does NOT cover, because the cost
# of being wrong there is the user missing the thing they screenshotted it for.
TRANSIENT_GRACE_DAYS = 30


@dataclass
class Proposal:
    asset_id: str
    action: Action
    risk: Risk
    evidence: List[Evidence]
    reversible: bool = True
    requires_confirmation: bool = True
    note: str = ""

    def __post_init__(self):
        if not self.evidence:
            raise ValueError(
                f"proposal {self.action.value} for {self.asset_id} carries no evidence. "
                "Every suggestion must be able to explain why."
            )
        if self.action in (Action.PROPOSE_REMOVE, Action.PROPOSE_ARCHIVE) and not self.reversible:
            raise ValueError(
                "an irreversible removal proposal is a safety red-line violation "
                "(no silent permanent deletion)"
            )
        if self.risk >= Risk.R4_PEOPLE and self.action == Action.PROPOSE_REMOVE:
            raise ValueError(
                f"risk {self.risk.name} may never be proposed for removal — the cost "
                "of being wrong is a memory or an irreplaceable document"
            )
        if self.action == Action.PROPOSE_REMOVE and self.risk != Risk.R0_EXACT_DUPLICATE:
            # Everything above R0 keeps its confirmation. R0 keeps it too by default;
            # `auto_applicable` below is the only thing that may drop it.
            self.requires_confirmation = True

    @property
    def auto_applicable(self) -> bool:
        """The single case the Constitution's automation bet actually covers: an exact
        byte-duplicate, where an identical copy is demonstrably still there."""
        return self.risk == Risk.R0_EXACT_DUPLICATE and self.reversible

    def why(self) -> str:
        return "; ".join(e.reason for e in self.evidence)


def classify_risk(c: Classification, *, is_exact_duplicate: bool = False,
                  is_near_duplicate_in_moment: bool = False,
                  has_unnamed_person: bool = False) -> Risk:
    """Risk is read off the classification, and the escalations are checked BEFORE the
    de-escalations. An exact duplicate of a passport is still a passport."""
    paths = c.paths

    for p in paths:
        if any(p.startswith(prefix) for prefix in PROTECTED_PATHS_PREFIX):
            return Risk.R5_CRITICAL_DOCUMENT
    if any(taxonomy.root_of(p) in PROTECTED_ROOTS for p in paths) or has_unnamed_person:
        return Risk.R4_PEOPLE

    if is_exact_duplicate:
        return Risk.R0_EXACT_DUPLICATE
    if is_near_duplicate_in_moment:
        return Risk.R1_NEAR_DUPLICATE
    for p in paths:
        if any(p.startswith(prefix) for prefix in TRANSIENT_PREFIX):
            return Risk.R2_TRANSIENT

    if c.needs_review:
        return Risk.R6_UNKNOWN
    return Risk.R3_ORDINARY


def propose(c: Classification, risk: Risk, *, extra_evidence: Optional[List[Evidence]] = None,
            duplicate_of: Optional[str] = None,
            age_days: Optional[float] = None) -> Proposal:
    """One asset, one proposal. The wording is what the user reads, so it says what
    would happen and what would survive it."""
    evidence = list(extra_evidence or [])
    primary = c.primary
    if primary:
        evidence.extend(primary.evidence[:2])
    elif c.assignments:
        # An asset the engine could only put on the timeline still gets a proposal,
        # and the date is the honest reason for it. Refusing to speak about the assets
        # we understand least is exactly backwards: those are the ones the user most
        # needs shown to them.
        evidence.extend(c.assignments[0].evidence[:1])
    if not evidence:
        raise ValueError("cannot propose anything for an asset with no evidence at all")

    if risk == Risk.R0_EXACT_DUPLICATE:
        return Proposal(c.asset_id, Action.PROPOSE_REMOVE, risk, evidence,
                        note=(f"byte-for-byte identical to {duplicate_of}, which stays. "
                              "Removal goes to Recently Deleted and is undoable for 30 days."
                              if duplicate_of else
                              "an identical copy remains in the library"))
    if risk == Risk.R1_NEAR_DUPLICATE:
        return Proposal(c.asset_id, Action.PROPOSE_ARCHIVE, risk, evidence,
                        note="one of several near-identical frames from the same moment; "
                             "the frames that differ are kept")
    if risk == Risk.R2_TRANSIENT:
        # An unknown age is not an old age. Absent evidence must never read as evidence
        # for acting, so an asset with no capture date stays put.
        if age_days is None:
            return Proposal(c.asset_id, Action.KEEP, risk, evidence,
                            note="a code or ticket with no capture date — kept, because "
                                 "there is no evidence it has expired")
        if age_days < TRANSIENT_GRACE_DAYS:
            return Proposal(c.asset_id, Action.KEEP, risk, evidence,
                            note=(f"a code or ticket — still recent ({age_days:.0f} days old), "
                                  f"so it stays put until it is {TRANSIENT_GRACE_DAYS} days old"))
        return Proposal(c.asset_id, Action.PROPOSE_ARCHIVE, risk, evidence,
                        note=f"a code or ticket that has stopped being useful — {age_days:.0f} days old")
    if risk == Risk.R6_UNKNOWN:
        return Proposal(c.asset_id, Action.REVIEW, risk, evidence,
                        note="not understood well enough to file confidently — kept and shown to you")
    return Proposal(c.asset_id, Action.KEEP, risk, evidence,
                    note="kept" if risk == Risk.R3_ORDINARY else "protected")
