# -*- coding: utf-8 -*-
"""
RISK, LIFECYCLE AND POLICY — Constitution §5, §6, §7, §8; L2 Tier 2-A.

**Rewritten 2026-09-06 after the audit found the previous version had invented its own
meanings for R0–R6.** The Constitution and Tier 2-A both name this scale explicitly,
and the old code used the same identifiers for different things — R6 meant "not
understood" where the Constitution means "irreplaceable, highest protection", receipts
were filed one level below where §6 puts them, and people one level above. Anyone
reading the catalogue against the Constitution would have misread every row. The scale
below is the Constitution's, verbatim, and `CONSTRAINTS.md` cites it.

§5 is explicit that the action is not a function of the category alone:

    Category × Importance × Lifecycle × Confidence × Recoverability × Personal
    Preference → Action Policy

So confidence is **not** a risk level. The old code had an `R6_UNKNOWN` that conflated
"we do not know what this is" with a place on a scale of consequence; they are
different axes, and merging them is what let an unknown asset outrank a passport.
Low confidence now routes to Review through the policy table, leaving the risk scale
to mean only what §6 says it means.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import List, Optional

from . import taxonomy
from .verdict import Classification, Evidence, REVIEW_FLOOR


class Risk(IntEnum):
    """§6 风险等级与默认动作 — verbatim scale, verbatim order."""
    R0_DISPOSABLE = 0        # 几乎无长期价值 · 完全重复下载、重复 Meme · 激进自动处理
    R1_LOW_VALUE = 1         # 通常短期/低价值 · 过期临时截图、验证码 · 自动处理或批量处理
    R2_NORMAL = 2            # 普通生活内容 · 风景、食物、普通物品 · 按相似度/生命周期处理
    R3_PERSONAL = 3          # 具有个人意义 · 人物、旅行、生活事件 · 保守精选
    R4_IMPORTANT = 4         # 可能承担交易/工作价值 · 收据、订单、工作资料 · Protect/Archive 优先
    R5_CRITICAL = 5          # 法律/身份/金融价值 · 身份证、护照、合同、银行卡 · 默认 Protect
    R6_IRREPLACEABLE = 6     # 可能不可替代 · 老照片、特殊家庭影像 · 最高保护

    @property
    def meaning(self) -> str:
        return _MEANING[self]

    @property
    def default_policy(self) -> str:
        return _DEFAULT_POLICY[self]


_MEANING = {
    Risk.R0_DISPOSABLE: "几乎无长期价值",
    Risk.R1_LOW_VALUE: "通常短期/低价值",
    Risk.R2_NORMAL: "普通生活内容",
    Risk.R3_PERSONAL: "具有个人意义",
    Risk.R4_IMPORTANT: "可能承担交易/工作价值",
    Risk.R5_CRITICAL: "法律/身份/金融价值",
    Risk.R6_IRREPLACEABLE: "可能不可替代",
}
_DEFAULT_POLICY = {
    Risk.R0_DISPOSABLE: "激进自动处理",
    Risk.R1_LOW_VALUE: "自动处理或批量处理",
    Risk.R2_NORMAL: "按相似度/生命周期处理",
    Risk.R3_PERSONAL: "保守精选",
    Risk.R4_IMPORTANT: "Protect/Archive 优先",
    Risk.R5_CRITICAL: "默认 Protect",
    Risk.R6_IRREPLACEABLE: "最高保护",
}


class Lifecycle(str, Enum):
    """§3 index dimension: Temporary / Active / Expired / Long-term. It decides *when*
    something may be acted on, which is a different question from how much it matters."""
    TEMPORARY = "temporary"
    ACTIVE = "active"
    EXPIRED = "expired"
    LONG_TERM = "long_term"


class Recoverability(str, Enum):
    """§7's whole argument rests on this: tolerating cheap mistakes is only valid where
    the mistake is genuinely recoverable. V-5 must confirm on a device that app-deleted
    assets really do land in Recently Deleted for 30 days."""
    RECOVERABLE = "recoverable"
    HARD_TO_REPLACE = "hard_to_replace"
    IRREPLACEABLE = "irreplaceable"


class Action(str, Enum):
    """§25 Layer 6: Protect / Keep / Archive / Select Best / Auto-Clean / Review, plus
    Suggest Delete from Tier 1-C.

    There is deliberately no member meaning *permanent* deletion. `AUTO_CLEAN` is the
    aggressive R0 action §6 calls for, and it is constrained below to recoverable
    assets only — the deletion itself is the platform's, lands in Recently Deleted, and
    stays undoable for 30 days."""
    AUTO_CLEAN = "auto_clean"
    SUGGEST_DELETE = "suggest_delete"
    SELECT_BEST = "select_best"
    ARCHIVE = "archive"
    KEEP = "keep"
    PROTECT = "protect"
    REVIEW = "review"


# Risk levels at which §6 forbids automated removal outright. Tier 2-A PASS criterion:
# "高风险类别（R4-R6）零自动删除".
NEVER_DELETE_AT_OR_ABOVE = Risk.R4_IMPORTANT

# Actions that can cost the user content. ARCHIVE is deliberately NOT one: §6 makes
# "Protect/Archive 优先" the *correct* default for R4, and archiving moves an asset out
# of the way while keeping it fully present and searchable. Counting it as a lossy
# action would have made the Constitution's own prescription look like a violation.
ACTING_ACTIONS = {Action.AUTO_CLEAN, Action.SUGGEST_DELETE, Action.SELECT_BEST}
REMOVING_ACTIONS = {Action.AUTO_CLEAN, Action.SUGGEST_DELETE}

# --------------------------------------------------------------------------------
# Category → risk, straight from §4 and §6.
# --------------------------------------------------------------------------------
RISK_BY_PATH_PREFIX = [
    ("Documents > Identity", Risk.R5_CRITICAL),
    ("Documents > Contracts", Risk.R5_CRITICAL),
    ("Documents > Financial", Risk.R5_CRITICAL),
    ("Documents > Medical", Risk.R5_CRITICAL),
    ("Documents > Receipts", Risk.R4_IMPORTANT),
    ("Documents > Warranty", Risk.R4_IMPORTANT),
    ("Documents", Risk.R4_IMPORTANT),
    ("Purchases", Risk.R4_IMPORTANT),
    ("Work", Risk.R4_IMPORTANT),
    ("People", Risk.R3_PERSONAL),
    ("Travel", Risk.R3_PERSONAL),
    ("Screenshots > Temporary", Risk.R1_LOW_VALUE),
    ("Downloads", Risk.R0_DISPOSABLE),
    ("Screenshots", Risk.R2_NORMAL),
    ("Objects", Risk.R2_NORMAL),
    ("Clothing", Risk.R2_NORMAL),
    ("Places", Risk.R2_NORMAL),
]


@dataclass
class Factors:
    """The six inputs §5 names. Kept as one object so a policy decision can never be
    made from a subset by accident."""
    risk: Risk
    lifecycle: Lifecycle
    confidence: float
    recoverability: Recoverability
    in_equivalence_group: bool = False
    is_exact_duplicate: bool = False
    personal_preference: Optional[Action] = None


@dataclass
class Proposal:
    asset_id: str
    action: Action
    factors: Factors
    evidence: List[Evidence]
    note: str = ""

    def __post_init__(self):
        if not self.evidence:
            raise ValueError(
                f"proposal {self.action.value} for {self.asset_id} carries no evidence. "
                "Every suggestion must be able to explain why.")
        if self.action in ACTING_ACTIONS and self.factors.risk >= NEVER_DELETE_AT_OR_ABOVE:
            raise ValueError(
                f"{self.factors.risk.name} may never be deleted automatically or "
                "suggested for deletion (§6, Tier 2-A: 高风险类别 R4-R6 零自动删除)")
        if self.action in ACTING_ACTIONS \
                and self.factors.recoverability == Recoverability.IRREPLACEABLE:
            raise ValueError(
                "an irreplaceable asset may not be acted on — §7's tolerance argument "
                "only holds where the mistake is recoverable")
        if self.action == Action.AUTO_CLEAN:
            if self.factors.risk != Risk.R0_DISPOSABLE:
                raise ValueError("auto-clean is R0 only (§6)")
            if self.factors.recoverability != Recoverability.RECOVERABLE:
                raise ValueError("auto-clean requires a recoverable asset")

    @property
    def requires_confirmation(self) -> bool:
        return self.action != Action.AUTO_CLEAN

    @property
    def reversible(self) -> bool:
        return True

    @property
    def auto_applicable(self) -> bool:
        return self.action == Action.AUTO_CLEAN

    def why(self) -> str:
        return "; ".join(e.reason for e in self.evidence)


# --------------------------------------------------------------------------------
def classify_risk(c: Classification, *, is_exact_duplicate: bool = False,
                  has_person: bool = False, is_irreplaceable: bool = False) -> Risk:
    """§6. Escalations before de-escalations: an exact duplicate of a passport is still
    a passport, so duplication only lowers risk for content that was disposable anyway."""
    if is_irreplaceable:
        return Risk.R6_IRREPLACEABLE

    best = None
    for path in c.paths:
        for prefix, risk in RISK_BY_PATH_PREFIX:
            if path == prefix or path.startswith(prefix + taxonomy.SEP):
                best = risk if best is None else max(best, risk)
                break
    if has_person and (best is None or best < Risk.R3_PERSONAL):
        best = Risk.R3_PERSONAL

    if best is None:
        # Nothing placed it. That is a confidence problem, not a consequence level —
        # §5 keeps those axes apart, so it lands at Normal and the policy table sends
        # it to Review on its confidence.
        best = Risk.R2_NORMAL

    # §6 R0 is 完全重复下载、重复 Meme. A byte-identical copy IS a re-download, so the
    # de-escalation applies whether or not the classifier managed to file it — but only
    # for content that was disposable anyway. An exact duplicate of a passport stays a
    # passport, which is why this runs after the escalations and not before.
    if is_exact_duplicate and best <= Risk.R2_NORMAL:
        return Risk.R0_DISPOSABLE
    return best


def lifecycle_of(c: Classification, age_days: Optional[float],
                 transient_grace_days: float = 30.0) -> Lifecycle:
    """Temporary content becomes Expired; everything else is Active or Long-term.
    An unknown age is never Expired — absent evidence must not read as evidence."""
    transient = any(p.startswith("Screenshots > Temporary") for p in c.paths)
    if transient:
        if age_days is None:
            return Lifecycle.TEMPORARY
        return Lifecycle.EXPIRED if age_days >= transient_grace_days else Lifecycle.TEMPORARY
    if any(taxonomy.root_of(p) in ("Documents", "Purchases", "People") for p in c.paths):
        return Lifecycle.LONG_TERM
    return Lifecycle.ACTIVE


def recoverability_of(risk: Risk) -> Recoverability:
    if risk == Risk.R6_IRREPLACEABLE:
        return Recoverability.IRREPLACEABLE
    if risk >= Risk.R4_IMPORTANT:
        return Recoverability.HARD_TO_REPLACE
    return Recoverability.RECOVERABLE


def decide_action(f: Factors) -> Action:
    """The §5 formula, as a table rather than a paragraph. Tier 2-A requires this to be
    a Policy Table, so `policy_table()` below prints it."""
    if f.personal_preference is not None:
        # §14: the user's own corrections outrank the global default — except that they
        # can only ever make the system more careful, never less.
        if f.personal_preference in (Action.PROTECT, Action.KEEP):
            return f.personal_preference

    if f.risk >= Risk.R5_CRITICAL:
        return Action.PROTECT
    if f.risk == Risk.R4_IMPORTANT:
        return Action.ARCHIVE if f.lifecycle == Lifecycle.LONG_TERM else Action.KEEP

    # Byte identity is checked BEFORE the confidence gate, and the distinction is the
    # whole of §6 R0. `confidence` here is confidence in the *classification*; the
    # evidence for an exact duplicate is a content hash, which is certain whether or
    # not we managed to work out what the picture is of. Gating it on classification
    # confidence sent every unidentifiable re-download to Review — which is to say the
    # one thing the system can genuinely automate was the one thing it refused to do,
    # and §7 exists to forbid exactly that trade.
    if f.risk == Risk.R0_DISPOSABLE and f.is_exact_duplicate \
            and f.recoverability == Recoverability.RECOVERABLE:
        return Action.AUTO_CLEAN

    # Everything else below R4 may be acted on — but only when it is sure enough to.
    if f.confidence < REVIEW_FLOOR:
        return Action.REVIEW

    if f.risk == Risk.R0_DISPOSABLE:
        return Action.SUGGEST_DELETE if f.lifecycle == Lifecycle.EXPIRED else Action.KEEP
    if f.risk == Risk.R1_LOW_VALUE:
        return Action.SUGGEST_DELETE if f.lifecycle == Lifecycle.EXPIRED else Action.KEEP
    if f.risk == Risk.R2_NORMAL:
        return Action.SELECT_BEST if f.in_equivalence_group else Action.KEEP
    # R3 Personal — §6 says 保守精选: select best is offered, never applied.
    return Action.SELECT_BEST if f.in_equivalence_group else Action.KEEP


NOTES = {
    Action.AUTO_CLEAN: "an identical copy remains; removal goes to Recently Deleted and is undoable for 30 days",
    Action.SUGGEST_DELETE: "offered for removal — it has passed the point where it is useful",
    Action.SELECT_BEST: "one of several near-identical frames; the frames that differ are kept",
    Action.ARCHIVE: "kept and moved out of the way, still fully searchable",
    Action.KEEP: "kept where it is",
    Action.PROTECT: "protected — this is not offered for removal at all",
    Action.REVIEW: "not understood well enough to file confidently — kept and shown to you",
}


def propose(c: Classification, factors: Factors, *,
            extra_evidence: Optional[List[Evidence]] = None,
            duplicate_of: Optional[str] = None) -> Proposal:
    evidence = list(extra_evidence or [])
    primary = c.primary
    if primary:
        evidence.extend(primary.evidence[:2])
    elif c.assignments:
        evidence.extend(c.assignments[0].evidence[:1])
    if not evidence:
        raise ValueError("cannot propose anything for an asset with no evidence at all")

    action = decide_action(factors)
    note = NOTES[action]
    if action == Action.AUTO_CLEAN and duplicate_of:
        note = f"byte-for-byte identical to {duplicate_of}, which stays; " + note
    return Proposal(c.asset_id, action, factors, evidence, note)


def policy_table() -> str:
    """Tier 2-A deliverable: every risk layer against every lifecycle and confidence
    condition. Generated from `decide_action`, so the table cannot drift from the code
    it documents."""
    lines = ["| risk | meaning | §6 default | lifecycle | confident | low confidence |",
             "|---|---|---|---|---|---|"]
    for risk in Risk:
        for lc in (Lifecycle.EXPIRED, Lifecycle.ACTIVE, Lifecycle.LONG_TERM):
            hi = decide_action(Factors(risk, lc, 0.9, recoverability_of(risk),
                                       is_exact_duplicate=(risk == Risk.R0_DISPOSABLE)))
            lo = decide_action(Factors(risk, lc, 0.3, recoverability_of(risk),
                                       is_exact_duplicate=(risk == Risk.R0_DISPOSABLE)))
            lines.append(f"| {risk.name} | {risk.meaning} | {risk.default_policy} | "
                         f"{lc.value} | {hi.value} | {lo.value} |")
    return "\n".join(lines)
