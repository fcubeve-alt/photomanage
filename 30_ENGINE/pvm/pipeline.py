# -*- coding: utf-8 -*-
"""
THE PIPELINE — one library in, one catalogue out, resumable at every point.

Three phases, in this order for a reason:

  1. **Context.** Metadata only, one pass. Home, trips, known people — the facts no
     single photo contains.
  2. **Classify.** Per asset, escalating from free signals upward, checkpointed every
     `BATCH`. This is the expensive phase and the one that gets killed, so it is the
     one that resumes.
  3. **Relate and score.** Duplicates, moments and look-alikes are library-level, and
     risk depends on both the classification and the duplicate status — an exact
     duplicate of a passport is still a passport. Scoring last is what makes that
     ordering explicit instead of accidental.

Phase 2 writes `risk = UNSCORED`; phase 3 replaces it. So an interrupted run leaves
assets that are classified but not yet scored, and the next run finishes them rather
than redoing the expensive part. A resume that reprocesses more than one batch of
phase-2 work is a bug — the same bar `assets_reprocessed_after_resume` sets for the
indexer (C-3, Playbook E-07).
"""

from __future__ import annotations

import time
from collections import Counter
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence

from . import dedup, taxonomy
from .catalog import BATCH, Catalog
from .classifier import Classifier
from .context import LibraryContext, build_context
from .risk import Risk, classify_risk, propose
from .signals import AssetSignals, Tier

UNSCORED = -1


@dataclass
class RunStats:
    seen: int = 0
    classified: int = 0
    skipped_unchanged: int = 0
    forgotten: int = 0
    scored: int = 0
    by_tier: Counter = field(default_factory=Counter)
    by_tier_spent: Counter = field(default_factory=Counter)
    by_risk: Counter = field(default_factory=Counter)
    by_root: Counter = field(default_factory=Counter)
    unfiled: int = 0
    needs_review: int = 0
    wall_s: float = 0.0
    context: Optional[LibraryContext] = None

    @property
    def assets_per_s(self) -> float:
        return self.classified / self.wall_s if self.wall_s > 0 else 0.0

    def summary(self) -> str:
        lines = [
            f"seen {self.seen}  classified {self.classified}  "
            f"unchanged {self.skipped_unchanged}  forgotten {self.forgotten}",
            f"wall {self.wall_s:.2f}s  {self.assets_per_s:,.0f} assets/s "
            f"({self.wall_s * 1000 / max(1, self.classified):.2f} ms/asset)",
            "answered by:  " + ", ".join(
                f"{Tier(t).label}={n}" for t, n in sorted(self.by_tier.items())),
            "paid for up to: " + ", ".join(
                f"{Tier(t).label}={n}" for t, n in sorted(self.by_tier_spent.items())),
            "risk: " + ", ".join(f"{Risk(r).name}={n}" for r, n in sorted(self.by_risk.items())),
            f"needs review {self.needs_review}  unfiled {self.unfiled}",
        ]
        return "\n".join(lines)


def run(assets: Sequence[AssetSignals], catalog: Catalog, *,
        budget: Tier = Tier.TEXT,
        reconcile_deletions: bool = True,
        progress: Optional[Callable[[int, int], None]] = None) -> RunStats:
    t0 = time.time()
    stats = RunStats(seen=len(assets))

    # ---- phase 1: context ---------------------------------------------
    ctx = build_context(assets)
    stats.context = ctx
    classifier = Classifier(ctx, budget=budget)

    # ---- reconcile removals -------------------------------------------
    if reconcile_deletions:
        present = {a.asset_id for a in assets}
        stats.forgotten = catalog.forget(catalog.known_ids() - present)

    # ---- phase 2: classify, checkpointed -------------------------------
    classifications: Dict[str, object] = {}
    pending = 0
    for i, a in enumerate(assets):
        if not catalog.needs_classification(a):
            stats.skipped_unchanged += 1
            continue
        c = classifier.classify(a)
        classifications[a.asset_id] = c
        catalog.upsert(a, c, Risk(Risk.R6_UNKNOWN), None)
        catalog.db.execute("UPDATE assets SET risk=? WHERE asset_id=?", (UNSCORED, a.asset_id))
        stats.classified += 1
        stats.by_tier[int(c.tier_used)] += 1
        stats.by_tier_spent[int(c.tier_spent)] += 1
        if c.needs_review:
            stats.needs_review += 1
        if any("unfiled:" in n for n in c.notes):
            stats.unfiled += 1
        for path in c.paths:
            stats.by_root[taxonomy.root_of(path)] += 1

        pending += 1
        if pending >= BATCH:
            catalog.checkpoint(a.asset_id)
            pending = 0
            if progress:
                progress(i + 1, len(assets))
    catalog.checkpoint(assets[-1].asset_id if assets else "")

    # ---- phase 3: relate and score -------------------------------------
    by_id = {a.asset_id: a for a in assets}
    unscored = [r[0] for r in catalog.db.execute(
        "SELECT asset_id FROM assets WHERE risk=?", (UNSCORED,))]

    document_ids = {r[0] for r in catalog.db.execute(
        "SELECT DISTINCT asset_id FROM assignments WHERE path LIKE 'Documents%'")}
    report = dedup.analyse(assets, document_ids=document_ids)
    catalog.write_relations(report.relations)

    for aid in unscored:
        a = by_id.get(aid)
        c = classifications.get(aid)
        if a is None or c is None:
            # Classified by an earlier, interrupted run: the classification is in the
            # catalogue but not in this process's memory. Redo the cheap part only.
            if a is None:
                continue
            c = classifier.classify(a)
        risk = classify_risk(
            c,
            is_exact_duplicate=aid in report.exact_duplicate_of,
            is_near_duplicate_in_moment=(aid in report.near_duplicate_in_moment
                                         and aid not in report.protected_distinct),
            has_unnamed_person=any("unnamed person" in n for n in c.notes),
        )
        age_days = None
        if a.created_at is not None:
            now = datetime.now(a.created_at.tzinfo) if a.created_at.tzinfo else datetime.now()
            age_days = max(0.0, (now - a.created_at).total_seconds() / 86400)
        proposal = propose(c, risk, duplicate_of=report.exact_duplicate_of.get(aid),
                           age_days=age_days)
        catalog.upsert(a, c, risk, proposal)
        stats.by_risk[int(risk)] += 1
        stats.scored += 1
    catalog.commit()

    stats.wall_s = time.time() - t0
    return stats
