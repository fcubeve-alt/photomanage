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

from . import dedup, deltas, importance, memory, taxonomy
from .catalog import BATCH, Catalog
from .classifier import Classifier
from .context import LibraryContext, build_context
from .risk import (Action, Factors, Importance, Risk, classify_risk, lifecycle_of, propose,
                   recoverability_of)
from .signals import AssetSignals, Tier

UNSCORED = -1

# How old, relative to the library's own span, a capture has to be before it reads as
# an old photograph rather than a recent one.
OLD_PHOTO_YEARS = 15


def looks_irreplaceable(asset, c) -> bool:
    """§6 R6 — 老照片、特殊家庭影像。

    PARTIAL, and deliberately conservative: what actually makes an image irreplaceable
    is knowledge only the user has, which is §14 Personal Policy and is not built. What
    can be derived is the signature of a *scanned* old photograph — a person in it, a
    capture date many years back, and none of the provenance a phone camera leaves. A
    false positive here costs one protected photo; a false negative costs the photo.
    The asymmetry decides which way to lean."""
    if not any(taxonomy.root_of(p) == "People" for p in c.paths):
        return False
    if asset.created_at is None or asset.geo is not None:
        return False
    if asset.source == "camera":
        return False
    age_years = (datetime.now() - asset.created_at).days / 365.25
    return age_years >= OLD_PHOTO_YEARS


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
    by_importance: Counter = field(default_factory=Counter)
    by_asset_class: Counter = field(default_factory=Counter)
    personal_preferences_applied: int = 0
    by_action: Counter = field(default_factory=Counter)
    by_root: Counter = field(default_factory=Counter)
    unfiled: int = 0
    needs_review: int = 0
    entities: int = 0
    observations: int = 0
    entity_review: int = 0
    videos: int = 0
    video_frames_seen: int = 0
    video_frames_processed: int = 0
    video_ms_saved: float = 0.0

    @property
    def video_frames_skipped(self) -> int:
        return self.video_frames_seen - self.video_frames_processed
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
            "importance: " + ", ".join(
                f"{Importance(i).name}={n}" for i, n in sorted(self.by_importance.items())),
            "§4 class: " + ", ".join(
                f"{k}={n}" for k, n in sorted(self.by_asset_class.items(), key=lambda kv: -kv[1])),
            "action: " + ", ".join(f"{a}={n}" for a, n in sorted(self.by_action.items())),
            f"needs review {self.needs_review}  unfiled {self.unfiled}  "
            f"§14 preferences applied {self.personal_preferences_applied}",
            f"remembered: {self.entities} things, {self.observations} sightings",
            f"same-entity pairs the resolver would not decide: {self.entity_review}",
            (f"video: {self.videos} looked inside, "
             f"{self.video_frames_processed:,}/{self.video_frames_seen:,} frames carried "
             f"new information ({self.video_ms_saved/1000:.1f}s of deep work skipped)"
             if self.videos else "video: none in this library"),
        ]
        return "\n".join(lines)


def run(assets: Sequence[AssetSignals], catalog: Catalog, *,
        budget: Tier = Tier.TEXT,
        reconcile_deletions: bool = True,
        build_memory: bool = True,
        frames_for: Optional[Callable[[AssetSignals], Sequence[deltas.Frame]]] = None,
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
        catalog.upsert(a, c, Risk.R2_NORMAL, None)
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
    # The relation between two look-alikes is a question about what they are, so the
    # classifications go in with them: §24 Gate 2 puts that answer in the
    # Category-Specific Entity Resolver rather than in one universal rule ladder.
    report = dedup.analyse(assets, document_ids=document_ids,
                           classifications=classifications)
    catalog.write_relations(report.relations)
    stats.entity_review = len(report.needs_entity_review)

    # How large the equivalence group around each asset is. §8 makes the group, not the
    # frame, the unit of value: one of six near-identical shots is worth less on its own
    # than the only photograph of an afternoon, and importance has to be able to see the
    # difference.
    group_size: Dict[str, int] = {}
    for g in report.relations:
        if g.kind != "same_moment":
            continue
        for member in g.members:
            group_size[member] = max(group_size.get(member, 1), len(g.members))

    # How often each named person turns up in the whole library. A face the user named
    # and then photographed thirty times is somebody in their life; a face that appears
    # once is somebody who was once in shot, and §16 forbids inferring anything further
    # about either. This counts appearances and nothing else.
    person_assets: Counter = Counter()
    for c in classifications.values():
        for path in getattr(c, "paths", ()):
            if path.startswith("People > ") and path != "People > Groups":
                person_assets[path] += 1

    # §14, consulted at run time for the first time. `decide_action` has honoured a
    # personal preference since the axis was built and nothing was ever passing one:
    # the policy existed, was tested, and had no route into a real run. Derived once
    # per run rather than per asset — it is a read over the whole decision log.
    policy = catalog.personal_policy()

    for aid in unscored:
        a = by_id.get(aid)
        c = classifications.get(aid)
        if a is None or c is None:
            # Classified by an earlier, interrupted run: the classification is in the
            # catalogue but not in this process's memory. Redo the cheap part only.
            if a is None:
                continue
            c = classifier.classify(a)
        is_dup = aid in report.exact_duplicate_of
        risk = classify_risk(
            c,
            is_exact_duplicate=is_dup,
            has_person=any("unnamed person" in n for n in c.notes),
            is_irreplaceable=looks_irreplaceable(a, c),
        )
        age_days = None
        if a.created_at is not None:
            now = datetime.now(a.created_at.tzinfo) if a.created_at.tzinfo else datetime.now()
            age_days = max(0.0, (now - a.created_at).total_seconds() / 86400)
        in_group = (aid in report.near_duplicate_in_moment
                    and aid not in report.protected_distinct)
        recoverability = recoverability_of(risk)
        preference = policy.preference_for(c.paths, risk)
        signals = importance.ImportanceSignals(
            paths=c.paths,
            recoverability=recoverability,
            people_recurrence=max(
                (person_assets[p] for p in c.paths if p in person_assets), default=0),
            group_size=group_size.get(aid, 1),
            in_equivalence_group=in_group,
            is_exact_duplicate=is_dup,
            is_irreplaceable=(risk == Risk.R6_IRREPLACEABLE),
            user_protects_category=bool(
                preference and preference.action in (Action.PROTECT, Action.KEEP)),
        )
        assessment = importance.assess(signals)
        factors = Factors(
            risk=risk,
            lifecycle=lifecycle_of(c, age_days),
            confidence=c.primary.confidence if c.primary else 0.0,
            recoverability=recoverability,
            importance=assessment.level,
            in_equivalence_group=in_group,
            is_exact_duplicate=is_dup,
            personal_preference=preference.action if preference else None,
        )
        proposal = propose(c, factors, duplicate_of=report.exact_duplicate_of.get(aid))
        catalog.upsert(a, c, risk, proposal, assessment=assessment)
        stats.by_importance[int(assessment.level)] += 1
        stats.by_asset_class[assessment.asset_class.name] += 1  # the report is for humans
        if preference is not None:
            stats.personal_preferences_applied += 1
        stats.by_risk[int(risk)] += 1
        stats.by_action[proposal.action.value] += 1
        stats.scored += 1
    # Written AFTER the scoring loop, not with the relations, and the order is load
    # bearing. `entity_review` carries a foreign key to `assets` with ON DELETE CASCADE
    # — which is what stops a deleted photo leaving a question about itself behind — and
    # `upsert` uses INSERT OR REPLACE. In SQLite a REPLACE deletes the old row before
    # inserting the new one, and that delete cascades. Writing these rows before the
    # scoring loop silently emptied the table: the count said 1 and the queue the user
    # reads said 0, which is the exact shape of failure this project keeps hitting.
    catalog.write_entity_review(report.needs_entity_review)
    catalog.commit()

    # ---- phase 3b: video ------------------------------------------------
    #
    # The engine has no decoder, so frames come from outside — the same shape of
    # contract `AssetSignals` already is with the rest of the world. Without a source
    # a video is still catalogued from its metadata; it is simply never looked inside,
    # and `stats.videos` stays at zero rather than the run implying otherwise.
    #
    # What happens here is L1-B §4's division of labour: this decides **which frames
    # deserve deep processing** and records **what the video contributed**. Actually
    # running a model on those frames is the caller's job, because that is the part
    # that needs Vision and a device.
    if frames_for is not None:
        _video_pass(assets, classifications, ctx, catalog, stats, frames_for)

    # ---- phase 4: remember ---------------------------------------------
    # §2 lists Remember among the ten things the product is, and §15 builds every later
    # service on it. This spends no new intelligence: it reads the classifications and
    # the signals already computed above and turns them into entities and sightings.
    #
    # It is skipped when the run classified nothing, because the graph is derived from
    # the whole library and rebuilding it from an incremental slice would produce a
    # memory of only the newest photos.
    if build_memory and classifications:
        graph = memory.build(assets, classifications, ctx,
                             moment_groups=[g.members for g in report.relations
                                            if g.kind == "same_moment"])
        catalog.write_memory(graph)
        stats.entities = len(graph.entities)
        stats.observations = len(graph.observations)

    stats.wall_s = time.time() - t0
    return stats


def _video_pass(assets, classifications, ctx, catalog, stats, frames_for) -> None:
    for asset in assets:
        if asset.media_type != "video":
            continue
        frames = list(frames_for(asset) or [])
        if not frames:
            # A video whose frames could not be read is not a video with no new
            # information. Saying nothing is the honest outcome; writing an empty
            # record would claim the opposite.
            continue

        # Documents get a stricter gate — a page of text that drifts slightly is still
        # a different page, and §9's false merge is expensive there.
        c = classifications.get(asset.asset_id)
        is_document = bool(c and any(p.startswith("Documents") for p in c.paths))
        selection = deltas.select_keyframes(frames, is_document=is_document)
        cost = deltas.estimate_cost(selection)

        # Which keyframes were taken because something *changed*, as opposed to the
        # periodic re-check the gate does inside a static shot. The two mean opposite
        # things to a segment, and the gate is the only place that knows which is which.
        new_content = {d.index for d in selection.decisions
                       if d.process and not d.reason.startswith(str(deltas.MAX_SKIP_RUN))}
        record = memory.video_record(
            asset, selection.keyframes,
            frame_rate=_frame_rate(frames, asset),
            classification=c, context=ctx, new_content_at=new_content)
        catalog.write_video_record(record, frames_seen=selection.total)

        stats.videos += 1
        stats.video_frames_seen += selection.total
        stats.video_frames_processed += selection.processed
        stats.video_ms_saved += cost.saved_ms
    catalog.commit()


def _frame_rate(frames, asset) -> float:
    """Derived from the frames themselves where they carry timestamps, because the
    sampling rate is a property of what the caller handed us and not of the file.

    A caller that samples every tenth frame of a 30 fps video is giving us 3 fps, and
    using the file's rate would put every segment boundary in the wrong place — the
    record would name the wrong seconds of the user's own video.
    """
    stamped = [f for f in frames if f.timestamp_s]
    if len(stamped) >= 2:
        span = stamped[-1].timestamp_s - stamped[0].timestamp_s
        steps = stamped[-1].index - stamped[0].index
        if span > 0 and steps > 0:
            return steps / span
    if asset.duration_s > 0 and len(frames) > 1:
        return (len(frames) - 1) / asset.duration_s
    return 1.0
