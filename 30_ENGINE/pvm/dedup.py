# -*- coding: utf-8 -*-
"""
DUPLICATES, MOMENTS AND THE THINGS THAT ONLY LOOK LIKE DUPLICATES.

This is the part of a photo manager that destroys libraries. Every competitor ships a
"remove duplicates" button; the interesting question is what it does to the four
cases that are not duplicates and look exactly like them:

  1. **Same Entity, different capture** (§9). The same ID card photographed again six
     months later. Same object, two events. Deleting one loses a record.
  2. **Near-identical, different content.** Pages 1 and 2 of a contract. Visually
     almost the same; semantically unrelated. This is the Document-class False Merge
     that MASTER_PLAN calls the make-or-break number for Tier 1, and it is the reason
     visual similarity alone may never authorise a merge for a document.
  3. **A burst where one frame is genuinely different** (§8). Frame 5 is the one where
     everyone's eyes are open. Collapsing the burst silently loses precisely the frame
     the burst was taken for.
  4. **A failed hash.** FC-1a: `dHash` returns 0 both for a whole class of ordinary
     images and for every failure. Treating 0 as a value links unrelated photos and
     makes a failure indistinguishable from a confident match.

So the policy here is deliberately asymmetric. Exact byte-identity is the only thing
allowed to be confident. Everything else produces a *relation* — "these belong
together" — which is useful for browsing and is never on its own a reason to remove
anything.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from . import taxonomy
from .signals import AssetSignals, hamming

# 64-bit dHash. <= 5 differing bits is "looks the same to a person at thumbnail size".
NEAR_BITS = 5
# Above this, a frame inside a burst is carrying different content and is never
# proposed for archive, whatever the rest of the burst looks like (§8).
DISTINCT_BITS = 10
# Captures this far apart are two events, even if the pixels agree.
SAME_MOMENT = timedelta(seconds=90)
# Two captures of the same thing more than this apart are a Same Entity relation, not
# redundancy — the second one was taken deliberately.
SEPARATE_OCCASION = timedelta(hours=12)


@dataclass
class DuplicateGroup:
    keeper: str
    duplicates: List[str]
    reason: str


@dataclass
class RelationGroup:
    """Assets that belong together but must all survive."""
    kind: str                      # "same_moment" | "same_entity" | "looks_alike"
    members: List[str]
    distinct_members: List[str] = field(default_factory=list)
    reason: str = ""


@dataclass
class DedupReport:
    exact_groups: List[DuplicateGroup] = field(default_factory=list)
    relations: List[RelationGroup] = field(default_factory=list)
    exact_duplicate_of: Dict[str, str] = field(default_factory=dict)
    near_duplicate_in_moment: Set[str] = field(default_factory=set)
    protected_distinct: Set[str] = field(default_factory=set)
    unusable_hash: Set[str] = field(default_factory=set)
    #: Pairs the Category-Specific Entity Resolver would not decide. §24 Gate 2:
    #: 低置信度只能进入 Review Queue，不自动合并/删除.
    needs_entity_review: List[Tuple[str, str, str]] = field(default_factory=list)

    @property
    def removable_count(self) -> int:
        return len(self.exact_duplicate_of)


def analyse(assets: Sequence[AssetSignals],
            document_ids: Optional[Set[str]] = None,
            ocr_by_id: Optional[Dict[str, str]] = None,
            classifications: Optional[Dict[str, object]] = None) -> DedupReport:
    """`document_ids` are assets classified under Documents. They get the stricter
    rule, because that is where a false merge is unrecoverable."""
    document_ids = document_ids or set()
    ocr_by_id = ocr_by_id or {}
    report = DedupReport()
    by_id = {a.asset_id: a for a in assets}

    # ---- exact: the only confident case ------------------------------------
    by_hash: Dict[str, List[AssetSignals]] = defaultdict(list)
    for a in assets:
        if a.content_hash:
            by_hash[a.content_hash].append(a)
    for h, group in by_hash.items():
        if len(group) < 2:
            continue
        # The earliest capture is the original; the later ones are the copies.
        ordered = sorted(group, key=lambda x: (x.created_at or _EPOCH, x.asset_id))
        keeper, rest = ordered[0], ordered[1:]
        report.exact_groups.append(DuplicateGroup(
            keeper.asset_id, [x.asset_id for x in rest],
            "byte-for-byte identical files"))
        for x in rest:
            report.exact_duplicate_of[x.asset_id] = keeper.asset_id

    # ---- moments: bursts and rapid sequences -------------------------------
    moments: Dict[str, List[AssetSignals]] = defaultdict(list)
    for a in assets:
        if a.burst_id:
            moments[a.burst_id].append(a)
    for burst_id, group in moments.items():
        if len(group) < 2:
            continue
        distinct = _distinct_frames(group, report)
        report.relations.append(RelationGroup(
            "same_moment", [x.asset_id for x in group], distinct,
            f"{len(group)} frames from one burst"))
        for x in group:
            if x.asset_id in distinct or x.asset_id in report.exact_duplicate_of:
                continue
            report.near_duplicate_in_moment.add(x.asset_id)
        # §8: the frames that differ are never archive candidates. Not "usually" —
        # never. The distinct frame is the reason the burst exists.
        report.protected_distinct.update(distinct)

    # ---- look-alikes: a relation, never a removal --------------------------
    for a in assets:
        if not a.has_usable_dhash:
            if a.dhash is not None:
                report.unusable_hash.add(a.asset_id)
    _look_alikes(assets, by_id, document_ids, ocr_by_id, report, classifications)
    return report


def _distinct_frames(group: Sequence[AssetSignals], report: DedupReport) -> List[str]:
    """Inside a burst, a frame far from the others is carrying different content.
    Frames whose hash is unusable count as distinct: an unreadable hash is not
    permission to treat a photo as redundant (FC-1a)."""
    usable = [x for x in group if x.has_usable_dhash]
    unusable = [x.asset_id for x in group if not x.has_usable_dhash]
    if len(usable) < 2:
        return [x.asset_id for x in group]

    distinct: List[str] = list(unusable)
    for x in usable:
        far = sum(1 for y in usable
                  if y is not x and hamming(x.dhash, y.dhash) > DISTINCT_BITS)
        if far >= len(usable) - 1:
            distinct.append(x.asset_id)
    # Whatever else happens, one frame survives on its own merits.
    if not distinct:
        distinct.append(sorted(group, key=lambda x: (x.created_at or _EPOCH, x.asset_id))[0].asset_id)
    return distinct


def _look_alikes(assets, by_id, document_ids, ocr_by_id, report: DedupReport,
                 classifications=None) -> None:
    buckets: Dict[int, List[AssetSignals]] = defaultdict(list)
    for a in assets:
        if a.has_usable_dhash:
            # Bucket on the high bits so comparison stays near-linear instead of
            # comparing 100k assets pairwise. Assets whose hashes differ in the top
            # bits cannot be within NEAR_BITS of each other in the usual case; the
            # cost of the rare miss is a relation we do not draw, never a deletion.
            buckets[a.dhash >> 48].append(a)

    seen: Set[Tuple[str, str]] = set()
    for bucket in buckets.values():
        for i, a in enumerate(bucket):
            for b in bucket[i + 1:]:
                if hamming(a.dhash, b.dhash) > NEAR_BITS:
                    continue
                # Already related by a stronger fact. Restating it as "these look
                # alike" adds a row and no information, and a review queue full of
                # restatements is one the user stops reading.
                if a.content_hash and a.content_hash == b.content_hash:
                    continue
                if a.burst_id and a.burst_id == b.burst_id:
                    continue
                key = tuple(sorted((a.asset_id, b.asset_id)))
                if key in seen:
                    continue
                seen.add(key)
                report.relations.append(
                    _relate(a, b, document_ids, ocr_by_id, classifications, report))


def _relate(a: AssetSignals, b: AssetSignals, document_ids: Set[str],
            ocr_by_id: Dict[str, str],
            classifications: Optional[Dict[str, object]] = None,
            report: Optional[DedupReport] = None) -> RelationGroup:
    """What the relation between two look-alikes actually is.

    When classifications are available this delegates to the Category-Specific Entity
    Resolver, and that delegation is the point. §24 Gate 2 forbids a universal
    same-entity model — 禁止寻找一个万能 Same-Entity 模型 — and the code that used to
    live here was one: a single ladder of text-then-time rules applied to ID cards,
    chairs and holiday snaps alike. `resolver.py` asks a different question per
    category instead, which is what the Gate requires.

    The fallback below runs only when nothing has been classified yet — the breadth
    pass, before any content is known. It is deliberately timid: with no category it
    can say *these look alike* and must not say *these are the same thing*.
    """
    members = [a.asset_id, b.asset_id]

    if classifications is not None:
        from . import resolver as _resolver          # local: keeps the import graph flat
        r = _resolver.resolve(a, b, classifications.get(a.asset_id),
                              classifications.get(b.asset_id))
        if r.needs_review:
            if report is not None:
                report.needs_entity_review.append((a.asset_id, b.asset_id, r.why()))
            # Undecided is not permission to fold: both stay protected as distinct.
            return RelationGroup("looks_alike", members, members, r.why())
        if r.verdict is _resolver.Verdict.DIFFERENT:
            return RelationGroup("looks_alike", members, members, r.why())
        if r.relation in (_resolver.Relation.OTHER_PAGE, _resolver.Relation.OTHER_VERSION):
            # One thing, more than one asset — every one of which must survive. Pages
            # of a contract and stages of an order are related, never redundant.
            return RelationGroup("same_entity", members, members, r.why())
        return RelationGroup("same_moment", members, [], r.why())

    # ---- breadth pass: no classification yet -------------------------------
    if a.asset_id in document_ids or b.asset_id in document_ids:
        ta = (ocr_by_id.get(a.asset_id) or a.ocr_text or "").strip().lower()
        tb = (ocr_by_id.get(b.asset_id) or b.ocr_text or "").strip().lower()
        if ta and tb and ta != tb:
            return RelationGroup("looks_alike", members, members,
                                 "these two pages look alike but their text differs — "
                                 "kept as separate documents")
        if not ta or not tb:
            return RelationGroup("looks_alike", members, members,
                                 "these look alike, but there is not enough text to be "
                                 "sure they are the same document — both kept")

    return RelationGroup("looks_alike", members, members,
                         "these look alike; nothing has been classified yet, so what "
                         "they are to each other is not yet known")
