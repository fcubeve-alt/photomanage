# -*- coding: utf-8 -*-
"""
PERSONAL POLICY — §14, and the one place the product is allowed to change its mind.

    Global Default Policy 是所有用户的初始规则。
    用户的 Keep/Delete/Protect/Restore/Correction 逐渐形成 Personal Policy。
    如果用户总是删除某类工作截图，系统以后可以更激进。
    如果用户始终保留人物连拍，系统对该用户自动变得保守。
    最终目标不是所有人共享一个"正确答案"，而是系统越来越懂这个用户愿意怎样管理。
                                                                        — L1 §14

THE TENSION THIS FILE HAS TO RESOLVE, stated plainly because it is the whole design.

§14 says the system **may become more aggressive** for a category the user always
deletes. `decide_action` until now accepted a personal preference and honoured it only
when it was PROTECT or KEEP — it could be made more careful and never less. That is
safe, and it is also not what §14 says.

The reconciliation is not "split the difference". It is that §6's red lines are not
preferences and are not negotiable by anybody, including the user:

  * **R4 and above are untouchable.** 高风险类别自动删除率必须为 0. No amount of
    consistent behaviour makes a passport a disposable screenshot. A personal policy
    that could reach R4 would be a mechanism for a user to talk themselves out of the
    protection that exists precisely because they will one day be tired and wrong.
  * **Below that, §14 governs.** For R0–R3, a demonstrated pattern may move a category
    from Review to Suggest Delete — the user stops being asked about something they
    have answered the same way many times, which is §18's Human Review Burden falling
    for a real reason rather than by loosening a threshold.
  * **Nothing here ever produces an irreversible action.** The most aggressive thing a
    personal policy can do is SUGGEST_DELETE, which still requires confirmation and
    still goes to Recently Deleted.

And "总是" means a pattern, not a decision. One deletion is a mood; twelve deletions
with no keeps is a preference. Both a minimum count and a minimum agreement are
required, and the policy says how much evidence it is standing on so a user can
disagree with it.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from . import taxonomy
from .risk import Action, Risk

#: Below this many decisions about a category, there is no pattern — only a few
#: choices, which every user makes differently on different days.
MIN_OBSERVATIONS = 8
#: And they have to agree. 总是 / 始终 is the Constitution's own word for this.
MIN_AGREEMENT = 0.85
#: Risk at or above which no personal policy may make the system less careful, ever.
#: §6, and the reason it is a constant here is so that changing it is a visible act.
NEVER_RELAX_AT_OR_ABOVE = Risk.R4_IMPORTANT

#: What the user did. Deliberately the five verbs §14 names and no others: a vocabulary
#: that grows by guesswork is one where "the user did something" starts to mean
#: "the system may act".
USER_ACTIONS = {"keep", "delete", "protect", "restore", "correction"}

#: How each verb reads as a preference. `restore` is the loudest signal in the set —
#: the user had to go and undo something — so it is treated as PROTECT, not KEEP.
_AS_PREFERENCE = {
    "keep": Action.KEEP,
    "protect": Action.PROTECT,
    "restore": Action.PROTECT,
    "delete": Action.SUGGEST_DELETE,
}


@dataclass(frozen=True)
class Decision:
    """One thing the user did, about one asset, at one time."""
    asset_id: str
    path: str
    action: str
    at: datetime

    def __post_init__(self):
        if self.action not in USER_ACTIONS:
            raise ValueError(
                f"{self.action!r} is not one of the five verbs §14 names ({sorted(USER_ACTIONS)}). "
                "A feedback vocabulary that grows by guesswork is one where "
                "“the user did something” quietly becomes “the system may act”.")


@dataclass(frozen=True)
class Preference:
    """A learned preference for one category, and the evidence under it."""
    path: str
    action: Action
    observations: int
    agreement: float
    #: True when this preference makes the system *less* careful than the global
    #: default would be. Kept separate because it is the half that needs a red line.
    relaxes: bool

    def why(self) -> str:
        share = f"{self.agreement * 100:.0f}%"
        verb = {Action.SUGGEST_DELETE: "removed", Action.KEEP: "kept",
                Action.PROTECT: "protected"}.get(self.action, str(self.action))
        return (f"you have {verb} {share} of the last {self.observations} things filed "
                f"under {self.path}")


@dataclass
class PersonalPolicy:
    """What this user has shown, per category. Empty is the correct starting state and
    is not a defect: a new user has told the system nothing, and §14's whole point is
    that the global default is where everyone begins."""
    preferences: Dict[str, Preference] = field(default_factory=dict)
    decisions_seen: int = 0

    def preference_for(self, paths: Sequence[str], risk: Risk) -> Optional[Preference]:
        """The most specific preference that applies, or None.

        Most specific wins: a user who deletes `Screenshots > Temporary` but keeps
        `Screenshots` has said two different things, and the deeper one is the one they
        said about *this* photo.
        """
        candidates: List[Preference] = []
        for path in paths:
            for node in [path] + taxonomy.ancestors(path):
                pref = self.preferences.get(node)
                if pref:
                    candidates.append(pref)
        if not candidates:
            return None
        best = max(candidates, key=lambda p: taxonomy.depth(p.path))

        # §6 outranks §14. A demonstrated pattern may make the system more careful at
        # any risk; it may only make it less careful below R4. Dropping the preference
        # entirely (rather than clamping it to KEEP) is deliberate: at R4+ the global
        # policy is already the careful answer, and silently substituting a different
        # one would make the explanation wrong.
        if best.relaxes and risk >= NEVER_RELAX_AT_OR_ABOVE:
            return None
        return best


def learn(decisions: Iterable[Decision]) -> PersonalPolicy:
    """Turn a decision log into a policy.

    Corrections are counted but never turned into a preference: a correction says the
    *classification* was wrong, not that the action was. Reading "you filed this in the
    wrong place" as "you may delete things like this" is exactly the kind of inference
    §16 and §11 exist to prevent.
    """
    by_path: Dict[str, Counter] = defaultdict(Counter)
    total = 0
    for decision in decisions:
        total += 1
        if decision.action == "correction":
            continue
        preference = _AS_PREFERENCE.get(decision.action)
        if preference is None:
            continue
        by_path[decision.path][preference] += 1
        for ancestor in taxonomy.ancestors(decision.path):
            by_path[ancestor][preference] += 1

    policy = PersonalPolicy(decisions_seen=total)
    for path, counts in by_path.items():
        observations = sum(counts.values())
        if observations < MIN_OBSERVATIONS:
            continue
        action, hits = counts.most_common(1)[0]
        agreement = hits / observations
        if agreement < MIN_AGREEMENT:
            # The user has been inconsistent here, which is information: it means this
            # category is one they want to decide case by case. Learning nothing is the
            # right response, not picking the majority.
            continue
        policy.preferences[path] = Preference(
            path=path, action=action, observations=observations, agreement=agreement,
            relaxes=action in (Action.SUGGEST_DELETE, Action.AUTO_CLEAN))
    return policy


# --------------------------------------------------------------------------------
# §18 Personalization Gain — "系统是否越来越懂这个用户".
# --------------------------------------------------------------------------------

@dataclass
class PersonalizationGain:
    """How much less the user is asked, because of what they already told us."""
    reviews_without_policy: int
    reviews_with_policy: int
    assets: int

    @property
    def reviews_avoided(self) -> int:
        return self.reviews_without_policy - self.reviews_with_policy

    @property
    def gain(self) -> float:
        if not self.reviews_without_policy:
            return 0.0
        return self.reviews_avoided / self.reviews_without_policy

    def human(self) -> str:
        if not self.assets:
            return "no assets scored"
        if self.reviews_without_policy == 0:
            return "nothing needed review even before personalisation"
        return (f"{self.reviews_avoided:,} of {self.reviews_without_policy:,} review "
                f"questions avoided ({self.gain * 100:.1f}%) across {self.assets:,} assets")


def personalization_gain(factors_by_asset, policy: PersonalPolicy,
                         paths_by_asset) -> PersonalizationGain:
    """Measured by running the same decision twice, with and without the policy.

    Not by counting how many preferences were learned: a policy that fires on nothing
    the user owns has taught the system nothing, and would score well on any metric
    that counted rules instead of outcomes.
    """
    from .risk import decide_action

    without = with_ = 0
    for asset_id, factors in factors_by_asset.items():
        base = decide_action(factors)
        if base is Action.REVIEW:
            without += 1
        pref = policy.preference_for(paths_by_asset.get(asset_id, []), factors.risk)
        personalised = decide_action(
            factors if pref is None
            else _with_preference(factors, pref.action))
        if personalised is Action.REVIEW:
            with_ += 1
    return PersonalizationGain(reviews_without_policy=without, reviews_with_policy=with_,
                               assets=len(factors_by_asset))


def _with_preference(factors, action: Action):
    from dataclasses import replace
    return replace(factors, personal_preference=action)
