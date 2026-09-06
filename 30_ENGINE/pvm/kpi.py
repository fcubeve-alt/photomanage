# -*- coding: utf-8 -*-
"""
THE KPIs THE PRODUCT IS ACTUALLY DEFINED BY — Constitution §18.

Written after the Owner pointed out that the engine was being measured against
whatever I had chosen to measure. F1 and precision are *my* measures. These are the
*product's*, they are named in L1 §18, and where the two disagree these win.

A classifier with an excellent F1 and a Human Review Burden of 300 per 1,000 assets is
a failed product: the user was handed back the work. That is the failure mode §7 exists
to forbid, and it is invisible in an F1 score.

**What is measurable without ground truth, and what is not.** At runtime there is no
oracle: the engine cannot know which of its answers are wrong. So each KPI below states
plainly whether it measures *outcome* (needs labels, only available in evaluation) or
*exposure* (measurable on any real library, and the honest thing to report in the
field). Reporting exposure as if it were outcome is how a dashboard starts lying.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from .risk import Action, Risk
from .schedule import BREADTH_MS

# How much being wrong costs, by risk class. Ordinal, deliberately steep at the top:
# losing a passport is not four times worse than losing a burst frame.
ERROR_COST = {
    Risk.R0_EXACT_DUPLICATE: 0.0,     # an identical copy remains
    Risk.R1_NEAR_DUPLICATE: 1.0,
    Risk.R2_TRANSIENT: 2.0,
    Risk.R3_ORDINARY: 10.0,
    Risk.R4_PEOPLE: 60.0,
    Risk.R5_CRITICAL_DOCUMENT: 100.0,
    Risk.R6_UNKNOWN: 40.0,            # unknown is priced high on purpose
}
# Risk classes whose loss cannot be undone by the user in practice.
IRRECOVERABLE = {Risk.R4_PEOPLE, Risk.R5_CRITICAL_DOCUMENT}


@dataclass
class KPIReport:
    automation_ratio: float
    human_review_burden: float
    weighted_error_cost: float
    catastrophic_error_rate: float
    classification_coverage: float
    continuous_hygiene_rate: Optional[float]
    ttfuv_seconds: float
    assets: int
    outcome_based: bool

    def as_markdown(self) -> str:
        kind = "outcome (scored against ground truth)" if self.outcome_based else \
               "exposure (no ground truth available — this is what a real library reports)"
        rows = [
            "| KPI (Constitution §18) | value | good is |",
            "|---|--:|:--|",
            f"| Automation Ratio | {self.automation_ratio*100:.1f}% | high |",
            f"| Human Review Burden | {self.human_review_burden:.0f} per 1,000 | low |",
            f"| Weighted Error Cost | {self.weighted_error_cost:.2f} per 1,000 | low |",
            f"| Catastrophic Error Rate | {self.catastrophic_error_rate*100:.4f}% | zero |",
            f"| Classification Coverage | {self.classification_coverage*100:.1f}% | high |",
            f"| Continuous Hygiene Rate | "
            + (f"{self.continuous_hygiene_rate*100:.1f}%" if self.continuous_hygiene_rate is not None else "n/a")
            + " | high |",
            f"| TTFUV (Time To First Useful View) | {self.ttfuv_seconds:.1f} s | low |",
            f"| Personalization Gain | not built | — |",
        ]
        return "\n".join(rows) + f"\n\nBasis: **{kind}**, over {self.assets:,} assets.\n"


# --------------------------------------------------------------------------------
# Individual measures. Each is a plain function so `CONSTRAINTS.md` can cite it and
# `check_constraints.py` can verify it exists.
# --------------------------------------------------------------------------------

def automation_ratio(catalog) -> float:
    """EXPOSURE. How much of the management work the system carried on its own —
    an asset filed confidently and given a settled action, without asking."""
    total = _one(catalog, "SELECT COUNT(*) FROM assets")
    if not total:
        return 0.0
    handled = _one(catalog,
                   "SELECT COUNT(*) FROM assets a JOIN proposals p USING(asset_id) "
                   "WHERE a.needs_review=0 AND p.action != ?", Action.REVIEW.value)
    return handled / total


def human_review_burden(catalog) -> float:
    """EXPOSURE. §12 requires the Review Queue to be *極小*. This is the number that
    says whether it is, per 1,000 assets — the unit §18 names."""
    total = _one(catalog, "SELECT COUNT(*) FROM assets")
    if not total:
        return 0.0
    reviews = _one(catalog,
                   "SELECT COUNT(*) FROM assets a JOIN proposals p USING(asset_id) "
                   "WHERE a.needs_review=1 OR p.action = ?", Action.REVIEW.value)
    return reviews / total * 1000


def weighted_error_cost(catalog, errors_by_asset: Optional[Dict[str, bool]] = None) -> float:
    """error × importance × irrecoverability, per 1,000 assets.

    With `errors_by_asset` (evaluation) this is OUTCOME: the real cost of the real
    mistakes. Without it, it is EXPOSURE: the cost that *would* be incurred if every
    acting proposal turned out to be wrong. Exposure is the honest field metric, and it
    is deliberately pessimistic — an engine that proposes nothing scores zero, which is
    correct, because it also automates nothing (see Automation Ratio)."""
    total = _one(catalog, "SELECT COUNT(*) FROM assets")
    if not total:
        return 0.0
    cost = 0.0
    for asset_id, risk, action in catalog.db.execute(
            "SELECT a.asset_id, a.risk, p.action FROM assets a JOIN proposals p USING(asset_id)"):
        if action not in (Action.PROPOSE_REMOVE.value, Action.PROPOSE_ARCHIVE.value):
            continue
        if errors_by_asset is not None and not errors_by_asset.get(asset_id, False):
            continue
        r = Risk(risk) if risk in {int(x) for x in Risk} else Risk.R6_UNKNOWN
        cost += ERROR_COST[r] * (3.0 if r in IRRECOVERABLE else 1.0)
    return cost / total * 1000


def catastrophic_error_rate(catalog) -> float:
    """The proportion of assets that are both important and irrecoverable AND were
    proposed for removal.

    The engine forbids this in `Proposal.__post_init__`, so the expected value is zero.
    Measuring it anyway is not a tautology: it checks the constructor guard actually
    held in the rows that were written, which is a different claim from the code being
    correct in isolation. A red line that is only enforced where it is enforced is not
    a red line."""
    total = _one(catalog, "SELECT COUNT(*) FROM assets")
    if not total:
        return 0.0
    bad = _one(catalog,
               "SELECT COUNT(*) FROM assets a JOIN proposals p USING(asset_id) "
               "WHERE a.risk >= ? AND p.action = ?",
               int(Risk.R4_PEOPLE), Action.PROPOSE_REMOVE.value)
    return bad / total


def classification_coverage(catalog) -> float:
    """EXPOSURE. How many assets reached a meaningful category. Timeline does not
    count — every asset with a date lands there, so counting it would report the
    calendar as an achievement."""
    total = _one(catalog, "SELECT COUNT(*) FROM assets")
    if not total:
        return 0.0
    covered = _one(catalog,
                   "SELECT COUNT(DISTINCT asset_id) FROM assignments "
                   "WHERE path NOT LIKE 'Timeline%'")
    return covered / total


def continuous_hygiene_rate(catalog, new_asset_ids) -> Optional[float]:
    """§13. Of the assets that arrived since the last run, how many were filed into a
    meaningful category automatically, with no review needed. This is the metric that
    says whether the library keeps working after the first big tidy-up — which is the
    whole product, not a follow-up feature."""
    ids = list(new_asset_ids)
    if not ids:
        return None
    marks = ",".join("?" * len(ids))
    filed = _one(catalog,
                 f"SELECT COUNT(DISTINCT a.asset_id) FROM assets a "
                 f"JOIN assignments s ON s.asset_id = a.asset_id "
                 f"WHERE a.asset_id IN ({marks}) AND a.needs_review = 0 "
                 f"AND s.path NOT LIKE 'Timeline%'", *ids)
    return filed / len(ids)


def time_to_first_useful_view(library_size: int, pessimistic: bool = True) -> float:
    """§24 Gate 3 names TTFUV a P0 metric. It is the time until the user has a
    structure to browse — the breadth pass — not the time until everything is
    understood. Measured cost per asset, no pixels decoded."""
    return library_size * BREADTH_MS[1 if pessimistic else 0] / 1000


def report(catalog, *, library_size: Optional[int] = None,
           new_asset_ids=(), errors_by_asset: Optional[Dict[str, bool]] = None) -> KPIReport:
    n = library_size if library_size is not None else _one(catalog, "SELECT COUNT(*) FROM assets")
    return KPIReport(
        automation_ratio=automation_ratio(catalog),
        human_review_burden=human_review_burden(catalog),
        weighted_error_cost=weighted_error_cost(catalog, errors_by_asset),
        catastrophic_error_rate=catastrophic_error_rate(catalog),
        classification_coverage=classification_coverage(catalog),
        continuous_hygiene_rate=continuous_hygiene_rate(catalog, new_asset_ids),
        ttfuv_seconds=time_to_first_useful_view(n),
        assets=n,
        outcome_based=errors_by_asset is not None,
    )


def _one(catalog, sql: str, *params):
    return catalog.db.execute(sql, params).fetchone()[0]
