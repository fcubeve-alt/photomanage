# -*- coding: utf-8 -*-
"""
CATEGORY-SPECIFIC ENTITY RESOLVER — §24 Gate 2, and Tier 1-B.

The Constitution is unusually blunt here:

    禁止寻找一个万能 Same-Entity 模型。采用 Category-Specific Entity Resolver：
    证件用 OCR/版式/字段，合同用文本指纹/页码，普通照片用时间/地点/视觉相似，
    人物与物品使用适合其类别的组合信号。            — L1 §24, Gate 2

So there is no `same_entity(a, b)` in this file. There is a dispatch on what the two
assets *are*, and a different resolver behind each branch, because the question "are
these the same thing" means something different for an ID card than for a chair.

`dedup.py` already answers a narrower question — do these two look alike, and were they
taken in one moment. That is Layer 1 in §25 terms. This is Layer 4: given that two
assets look alike, do they show **the same thing in the world**, a different **page or
version** of it, or two different things that merely photograph alike.

Two rules run through every branch:

* **A document is never merged on appearance.** Tier 1-B's PASS criterion is that
  False Merge on documents is extremely low, "错误合并证件/合同的代价远高于漏检" — the
  cost of wrongly merging two people's ID cards is far above the cost of missing a
  match. So documents merge on *fields*: a shared identifier, a shared holder name.
  Looking identical buys UNCERTAIN at most, never SAME.
* **低置信度只能进入 Review Queue，不自动合并/删除.** UNCERTAIN is a first-class
  verdict, not a rounded-down SAME. It is review burden (§18), and burden is a cost to
  report honestly — not an error to hide by guessing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import timedelta
from enum import Enum
from typing import List, Optional, Sequence, Tuple

from . import taxonomy
from .signals import AssetSignals, Tier, hamming
from .verdict import Classification, Evidence, combine


class Verdict(str, Enum):
    SAME = "same"
    DIFFERENT = "different"
    #: Neither established. Goes to the Review Queue and is never auto-applied.
    UNCERTAIN = "uncertain"


class Relation(str, Enum):
    #: The same real thing, photographed again.
    SAME_INSTANCE = "same_instance"
    #: One document, two pages. Same entity; both assets must survive.
    OTHER_PAGE = "other_page"
    #: One document or screen, captured twice at different times — a version, not a
    #: page. Keeping the later one is a *proposal*, never an automatic act.
    OTHER_VERSION = "other_version"
    #: Two different things.
    DISTINCT = "distinct"
    UNKNOWN = "unknown"


@dataclass
class Resolution:
    """What the resolver concluded, and — always — why."""
    verdict: Verdict
    relation: Relation
    confidence: float
    resolver: str
    evidence: List[Evidence] = field(default_factory=list)

    def __post_init__(self):
        if not self.evidence:
            raise ValueError(
                f"{self.resolver} returned {self.verdict.value} with no evidence. "
                "A merge nobody can justify is the failure Gate 2 is about."
            )

    @property
    def may_merge(self) -> bool:
        """The only gate any caller should consult before joining two assets."""
        return self.verdict is Verdict.SAME and self.relation is not Relation.DISTINCT

    @property
    def needs_review(self) -> bool:
        return self.verdict is Verdict.UNCERTAIN

    def why(self) -> str:
        return "; ".join(e.reason for e in sorted(self.evidence, key=lambda e: -e.weight))


# ---------------------------------------------------------------------------
# Field extraction — the "OCR 字段" half of Gate 2.
#
# These are deliberately narrow. A pattern that matches loosely produces confident
# identifiers that are not identifiers, and a wrong identifier is worse here than no
# identifier: no identifier ends at UNCERTAIN, a wrong one ends at SAME.
# ---------------------------------------------------------------------------

#: Labelled identifiers. Three rules, each of which the first version of this file got
#: wrong and the evaluation caught within a minute:
#:
#: 1. The label must be followed by an explicit `no` / `number` / `#` / `:`. Without
#:    that, `PASSPORT UNITED KINGDOM` yielded the identifier "UNITED".
#: 2. `no` must end on a word boundary, or `RECEIPT NORTHSIDE COFFEE` yields "RTHSIDE".
#: 3. The captured token must contain a digit. Identifiers do; English words do not.
#:    This one rule kills "UNITED", "ENTITY", "CONFIRMED" and "NORTHSIDE" at once.
#:
#: Reading a wrong identifier is worse here than reading none: no identifier ends at
#: UNCERTAIN and a wrong one ends at SAME, which is a false merge on the category
#: Tier 1-B fails on.
_ID_LABEL = (r"passport|identity\s*card|id\s*card|driving\s*licen[cs]e|order|invoice|"
             r"receipt|policy|contract|agreement|tracking|reference|ref|customer|account")
_ID_SEPARATOR = r"(?:(?:no|number|nr|num|id|号)\b\.?\s*[:.#]?|[:#])"
_LABELLED_ID = re.compile(
    rf"\b(?:{_ID_LABEL})\b\s*{_ID_SEPARATOR}\s*([A-Z0-9][A-Z0-9/\-]{{3,23}})\b", re.I)

#: `PAGE 2 OF 4` and its variants. The denominator matters more than the numerator: two
#: pages that both say "of 4" belong to the same four-page thing.
_PAGE = re.compile(r"\bpage\s*(\d{1,3})\s*(?:of|/|第)?\s*(\d{1,3})?\b", re.I)
_PAGE_CN = re.compile(r"第\s*(\d{1,3})\s*页\s*(?:共\s*(\d{1,3})\s*页)?")

#: A holder name on an identity document: `NAME: JANE DOE`, `SURNAME/姓 DOE`.
#: Bounded to one or two upper-case words. Unbounded, `NAME: JANE DOE DATE OF BIRTH`
#: became the holder's name, and a holder that swallows the rest of the page compares
#: unequal for reasons that have nothing to do with who holds the document.
#: The label is case-insensitive; the value is not. A holder's name on an identity
#: document is set in capitals, and requiring that is most of what stops this from
#: matching prose.
_NAME = re.compile(r"\b(?i:name|surname|holder|姓名)\s*[:/]?\s*"
                   r"([A-Z]{2,20}(?:[ '\-][A-Z]{2,20})?)\b")

_STOPWORDS = {
    "the", "and", "for", "with", "this", "that", "page", "of", "no", "number",
    "date", "total", "amount", "card", "id", "order", "receipt", "invoice",
}


def identifiers(text: str) -> set:
    """Every labelled identifier in the text, upper-cased and punctuation-stripped.

    A candidate without a digit is discarded: it is a word that happened to follow a
    label, not a reference number.
    """
    out = set()
    for match in _LABELLED_ID.finditer(text or ""):
        token = re.sub(r"[^A-Z0-9]", "", match.group(1).upper())
        if len(token) >= 4 and any(ch.isdigit() for ch in token):
            out.add(token)
    return out


def page_of(text: str) -> Optional[Tuple[int, Optional[int]]]:
    """`(page, total)` where the text says so, else None."""
    for pattern in (_PAGE, _PAGE_CN):
        match = pattern.search(text or "")
        if match:
            total = int(match.group(2)) if match.group(2) else None
            return int(match.group(1)), total
    return None


def holder_names(text: str) -> set:
    return {re.sub(r"\s+", " ", m.group(1)).strip().upper()
            for m in _NAME.finditer(text or "")}


def _shingles(text: str, n: int = 3) -> set:
    """Word trigrams, minus stopwords — the "文本指纹" Gate 2 asks for on contracts.

    Trigrams rather than a bag of words because contract boilerplate shares almost
    every individual word with every other contract; what distinguishes two contracts
    is which words sit *next to* which.
    """
    words = [w for w in re.findall(r"[a-z0-9]+", (text or "").lower())
             if w not in _STOPWORDS]
    if len(words) < n:
        return {" ".join(words)} if words else set()
    return {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}


def text_similarity(a: str, b: str) -> float:
    """Jaccard over trigrams. 0 when either side has no usable text — which is a
    *lack of evidence*, and callers must not read it as evidence of difference."""
    sa, sb = _shingles(a), _shingles(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


# ---------------------------------------------------------------------------
# Thresholds. Each is a policy choice, so each says what it is trading.
# ---------------------------------------------------------------------------

#: Above this, two texts are the same text captured twice.
SAME_TEXT = 0.80
#: Below this, two documents of the same type are different documents. Between the two
#: the answer is UNCERTAIN, and the user decides.
DIFFERENT_TEXT = 0.35
#: Perceptual distance at which two photographs are of the same view.
SAME_VIEW_BITS = 6
#: ...and beyond which they are not the same view at all.
DIFFERENT_VIEW_BITS = 16
#: Two captures further apart than this are two occasions, whatever they show.
SAME_OCCASION = timedelta(hours=12)
#: An object seen this far apart in time is still the same object — objects persist,
#: which is the whole premise of Object Memory. Time is therefore *supporting*
#: evidence for objects and *deciding* evidence for moments.
OBJECT_MEMORY_SPAN = timedelta(days=365 * 10)


def _instance_or_version(a: AssetSignals, b: AssetSignals) -> "Relation":
    """SAME_INSTANCE means one thing in one moment; OTHER_VERSION means one thing on
    two occasions.

    The difference decides whether a caller may fold the two together, so it is not
    cosmetic. Two photographs of one ID card six months apart are the same card and two
    separate records of it — §9's case, and a deletion the user would not forgive. Only
    a pair within a single occasion is foldable.
    """
    gap = _gap(a, b)
    return (Relation.SAME_INSTANCE if gap is not None and gap <= SAME_OCCASION
            else Relation.OTHER_VERSION)


def _gap(a: AssetSignals, b: AssetSignals) -> Optional[timedelta]:
    if a.created_at is None or b.created_at is None:
        return None
    return abs(a.created_at - b.created_at)


def _visual_distance(a: AssetSignals, b: AssetSignals) -> Optional[int]:
    """None when either hash is unusable.

    FC-1a: dHash returns 0 both for a class of ordinary flat images and for every
    failure, so a 0 that came from a failure is indistinguishable from a perfect match.
    `has_usable_dhash` is the guard, and without it this function would report two
    unrelated blank screenshots as identical.
    """
    if not (a.has_usable_dhash and b.has_usable_dhash):
        return None
    return hamming(a.dhash, b.dhash)


def _category(c: Optional[Classification]) -> str:
    """Which resolver this asset belongs to. The dispatch key of the whole module."""
    if c is None:
        return "photo"
    roots = {taxonomy.root_of(p) for p in c.paths}
    # Order matters: a receipt is cross-listed into Documents *and* Purchases, and the
    # document resolver is the stricter of the two. Strictest wins.
    if "Documents" in roots:
        return "document"
    if "Screenshots" in roots or "Purchases" in roots:
        return "screenshot"
    if "Objects" in roots or "Clothing" in roots:
        return "object"
    if "People" in roots:
        return "person"
    return "photo"


def resolve(a: AssetSignals, b: AssetSignals,
            ca: Optional[Classification] = None,
            cb: Optional[Classification] = None) -> Resolution:
    """Dispatch to the resolver for what these two assets are.

    When the two assets are of different categories they are different things, and the
    answer is cheap: no resolver needs to run.
    """
    if a.asset_id == b.asset_id:
        return Resolution(Verdict.SAME, Relation.SAME_INSTANCE, 1.0, "identity",
                          [Evidence("asset_id", Tier.METADATA, 0.99,
                                    "the same asset compared with itself")])

    # Byte identity settles it before any category question is asked — and before any
    # confidence gate, because two identical files are the same file whatever either
    # one was classified as.
    if a.content_hash and a.content_hash == b.content_hash:
        return Resolution(Verdict.SAME, Relation.SAME_INSTANCE, 0.99, "bytes",
                          [Evidence("content_hash", Tier.HASH, 0.99,
                                    "these two files are byte-for-byte identical")])

    ka, kb = _category(ca), _category(cb)
    if ka != kb:
        return Resolution(
            Verdict.DIFFERENT, Relation.DISTINCT, 0.8, "category",
            [Evidence("taxonomy", Tier.METADATA, 0.8,
                      f"one is filed as {ka}, the other as {kb} — different kinds of thing")])

    return {
        "document": _resolve_document,
        "screenshot": _resolve_screenshot,
        "object": _resolve_object,
        "person": _resolve_photo,
        "photo": _resolve_photo,
    }[ka](a, b)


# ---------------------------------------------------------------------------
# Documents — 证件用 OCR/版式/字段，合同用文本指纹/页码
#
# The highest-cost branch, and the only one that refuses to merge on appearance.
# ---------------------------------------------------------------------------

def _resolve_document(a: AssetSignals, b: AssetSignals) -> Resolution:
    """The order of these checks is itself the design, and the evaluation set it.

    Disagreeing identifiers come first, before anything that could merge. Page 1 of two
    different contracts on the same template shares its page number, its page count and
    three paragraphs of boilerplate — every similarity signal says SAME — and the only
    thing that separates them is that the contract numbers differ. So that check runs
    before the ones it would otherwise lose to.
    """
    ta, tb = (a.ocr_text or "").strip(), (b.ocr_text or "").strip()
    ida, idb = identifiers(ta), identifiers(tb)
    pa, pb = page_of(ta), page_of(tb)
    similarity = text_similarity(ta, tb)

    # 1. Disagreeing references separate, whatever else agrees.
    if ida and idb and not (ida & idb):
        return Resolution(
            Verdict.DIFFERENT, Relation.DISTINCT, 0.93, "document.identifier",
            [Evidence("ocr_text", Tier.TEXT, 0.93,
                      "each carries a reference number and they do not match — "
                      "these are two different documents")])

    # 2. Different holders separate. Compared by token overlap, because OCR gives the
    #    name with a variable amount of the surrounding page attached to it.
    na = {w for n in holder_names(ta) for w in n.split()}
    nb = {w for n in holder_names(tb) for w in n.split()}
    if na and nb and not (na & nb):
        return Resolution(
            Verdict.DIFFERENT, Relation.DISTINCT, 0.9, "document.holder",
            [Evidence("ocr_text", Tier.TEXT, 0.9,
                      f"these are made out to different people ({sorted(na)[0]} and "
                      f"{sorted(nb)[0]})")])

    # 3. Pages of one document. Checked before the identifier merge so that page 1 and
    #    page 2 of contract AB-4417 are recorded as two pages, not two versions — the
    #    relation is what tells a view that both must be shown.
    if pa and pb and pa[1] and pa[1] == pb[1] and pa[0] != pb[0]:
        return Resolution(
            Verdict.SAME, Relation.OTHER_PAGE, 0.85, "document.page",
            [Evidence("ocr_text", Tier.TEXT, 0.85,
                      f"page {pa[0]} and page {pb[0]} of the same {pa[1]}-page "
                      "document — related, and both kept")])

    # 4. Agreeing references merge.
    if ida and idb:
        shared = ida & idb
        return Resolution(
            Verdict.SAME, _instance_or_version(a, b), 0.95, "document.identifier",
            [Evidence("ocr_text", Tier.TEXT, 0.95,
                      f"both carry the same reference {sorted(shared)[0]}")])

    # 5. Text fingerprint, as far as it honestly reaches — and no further. Without a
    #    reference or a holder, appearance never merges a document.
    if not ta or not tb:
        return Resolution(
            Verdict.UNCERTAIN, Relation.UNKNOWN, 0.3, "document.text",
            [Evidence("ocr_text", Tier.TEXT, 0.3,
                      "there is not enough text on one of these to tell whether they "
                      "are the same document")])
    if similarity >= SAME_TEXT:
        return Resolution(
            Verdict.SAME, _instance_or_version(a, b), 0.82, "document.text",
            [Evidence("ocr_text", Tier.TEXT, 0.82,
                      "the text on these two is the same text, word for word")])
    if similarity <= DIFFERENT_TEXT:
        return Resolution(
            Verdict.DIFFERENT, Relation.DISTINCT, 0.85, "document.text",
            [Evidence("ocr_text", Tier.TEXT, 0.85,
                      "these two pages read differently — kept as separate documents")])
    return Resolution(
        Verdict.UNCERTAIN, Relation.UNKNOWN, 0.5, "document.text",
        [Evidence("ocr_text", Tier.TEXT, 0.5,
                  "these two documents are similar but not the same; only you can say "
                  "whether they are one thing")])


# ---------------------------------------------------------------------------
# Screenshots — 同一订单/票务/报错/商品页面的不同截图/版本
# ---------------------------------------------------------------------------

def _resolve_screenshot(a: AssetSignals, b: AssetSignals) -> Resolution:
    ta, tb = (a.ocr_text or "").strip(), (b.ocr_text or "").strip()

    ida, idb = identifiers(ta), identifiers(tb)
    if ida and idb:
        shared = ida & idb
        if shared:
            # The point of this branch: an order confirmation, a dispatch mail and a
            # delivery photo are one purchase seen three times. §15 Purchase Memory
            # depends on exactly this join.
            return Resolution(
                Verdict.SAME, Relation.OTHER_VERSION, 0.92, "screenshot.reference",
                [Evidence("ocr_text", Tier.TEXT, 0.92,
                          f"both screens show reference {sorted(shared)[0]} — the same "
                          "order, captured at different stages")])
        return Resolution(
            Verdict.DIFFERENT, Relation.DISTINCT, 0.9, "screenshot.reference",
            [Evidence("ocr_text", Tier.TEXT, 0.9,
                      "these screens show different order references")])

    similarity = text_similarity(ta, tb)
    distance = _visual_distance(a, b)
    if similarity >= SAME_TEXT and distance is not None and distance <= SAME_VIEW_BITS:
        return Resolution(
            Verdict.SAME, Relation.OTHER_VERSION, 0.78, "screenshot.text",
            [Evidence("ocr_text", Tier.TEXT, 0.7, "the same screen, captured twice"),
             Evidence("dhash", Tier.HASH, 0.6, "and the two look the same")])
    if similarity <= DIFFERENT_TEXT and ta and tb:
        return Resolution(
            Verdict.DIFFERENT, Relation.DISTINCT, 0.8, "screenshot.text",
            [Evidence("ocr_text", Tier.TEXT, 0.8, "these screens show different things")])
    return Resolution(
        Verdict.UNCERTAIN, Relation.UNKNOWN, 0.45, "screenshot.text",
        [Evidence("ocr_text", Tier.TEXT, 0.45,
                  "these look like the same app but there is nothing on them that "
                  "says they are the same thing")])


# ---------------------------------------------------------------------------
# Objects — 视觉 embedding + attribute + temporal evidence
#
# What this branch cannot do is the honest headline of Tier 1-B. Without a real
# embedding it can say "the same view of an object" and cannot say "the same object
# from a different angle" — and the second is what Object Memory needs. It says so.
# ---------------------------------------------------------------------------

def _resolve_object(a: AssetSignals, b: AssetSignals) -> Resolution:
    distance = _visual_distance(a, b)
    labels_a = {s.identifier for s in a.scene_labels}
    labels_b = {s.identifier for s in b.scene_labels}
    shared_labels = labels_a & labels_b
    gap = _gap(a, b)

    if distance is None:
        return Resolution(
            Verdict.UNCERTAIN, Relation.UNKNOWN, 0.3, "object.visual",
            [Evidence("dhash", Tier.HASH, 0.3,
                      "one of these has no usable visual fingerprint, so they cannot "
                      "be compared by appearance")])

    same_occasion = gap is not None and gap <= SAME_OCCASION

    if distance <= SAME_VIEW_BITS and shared_labels and same_occasion:
        return Resolution(
            Verdict.SAME, Relation.SAME_INSTANCE, 0.75, "object.visual",
            [Evidence("dhash", Tier.HASH, 0.65,
                      "these two look like the same thing, minutes apart"),
             Evidence("scene_labels", Tier.VISUAL, 0.5,
                      f"and both were recognised as {sorted(shared_labels)[0]}")])

    if distance <= SAME_VIEW_BITS and shared_labels:
        # Deliberately NOT a merge, and this is the honest half of Gate 2.
        #
        # Two near-identical photographs of a chair taken two days apart are either one
        # chair photographed twice or two chairs of the same model in the same room, and
        # no signal in this build distinguishes them: appearance is identical by
        # construction, the labels agree, and the time gap says nothing because objects
        # persist. Answering SAME here would merge the two-identical-chairs case, and a
        # merge is not undone by the user noticing later.
        #
        # Tier 1 anticipates exactly this outcome — 部分类别（例如复杂物品识别）暂时做
        # 不到高置信度，可以先把这些类别降级为「Review Queue 优先」上线 — so the
        # category is downgraded to review rather than the threshold being loosened
        # until the number looks better.
        return Resolution(
            Verdict.UNCERTAIN, Relation.UNKNOWN, 0.55, "object.persistence",
            [Evidence("dhash", Tier.HASH, 0.55,
                      "these look like the same thing on two different occasions — but "
                      "two of the same model look like this too, and nothing here can "
                      "tell those apart")])

    if distance >= DIFFERENT_VIEW_BITS and not shared_labels:
        return Resolution(
            Verdict.DIFFERENT, Relation.DISTINCT, 0.8, "object.visual",
            [Evidence("dhash", Tier.HASH, 0.8,
                      "these look like different things and were recognised as "
                      "different things")])

    # The gap Tier 1-B names and this build does not close. Two photos of one chair
    # from opposite sides are far apart in every signal available here; a visual
    # embedding would join them and there is none. Saying UNCERTAIN is the truthful
    # answer, and it is review burden, not an error to be optimised away by guessing.
    return Resolution(
        Verdict.UNCERTAIN, Relation.UNKNOWN, 0.4, "object.visual",
        [Evidence("dhash", Tier.HASH, 0.4,
                  "these could be the same thing from a different angle, or two "
                  "similar things — telling those apart needs a visual embedding this "
                  "build does not have")])


# ---------------------------------------------------------------------------
# Ordinary photos and people — 普通照片用时间/地点/视觉相似
# ---------------------------------------------------------------------------

def _resolve_photo(a: AssetSignals, b: AssetSignals) -> Resolution:
    distance = _visual_distance(a, b)
    gap = _gap(a, b)

    if distance is None:
        return Resolution(
            Verdict.UNCERTAIN, Relation.UNKNOWN, 0.3, "photo.visual",
            [Evidence("dhash", Tier.HASH, 0.3,
                      "one of these has no usable visual fingerprint")])

    if distance >= DIFFERENT_VIEW_BITS:
        return Resolution(
            Verdict.DIFFERENT, Relation.DISTINCT, 0.85, "photo.visual",
            [Evidence("dhash", Tier.HASH, 0.85, "these are two different pictures")])

    if distance <= SAME_VIEW_BITS:
        if gap is not None and gap <= SAME_OCCASION:
            same_place = True
            if a.geo and b.geo:
                same_place = a.geo.km_to(b.geo) < 1.0
            if same_place:
                return Resolution(
                    Verdict.SAME, Relation.SAME_INSTANCE, 0.88, "photo.moment",
                    [Evidence("dhash", Tier.HASH, 0.7, "these look nearly identical"),
                     Evidence("created_at", Tier.METADATA, 0.6,
                              "and were taken within the same few hours")])
            return Resolution(
                Verdict.DIFFERENT, Relation.DISTINCT, 0.7, "photo.moment",
                [Evidence("geo", Tier.METADATA, 0.7,
                          "these look alike but were taken in different places")])
        # §9's case: one subject, two occasions. Related, and a deletion the user
        # would not forgive — so SAME as an entity, never SAME as a duplicate.
        return Resolution(
            Verdict.SAME, Relation.OTHER_VERSION, 0.6, "photo.subject",
            [Evidence("dhash", Tier.HASH, 0.6,
                      "the same subject photographed on two different occasions — "
                      "related, and both kept")])

    return Resolution(
        Verdict.UNCERTAIN, Relation.UNKNOWN, 0.45, "photo.visual",
        [Evidence("dhash", Tier.HASH, 0.45,
                  "these are similar without being the same picture")])


# ---------------------------------------------------------------------------
# Grouping, for callers that have more than a pair.
# ---------------------------------------------------------------------------

@dataclass
class EntityGroup:
    members: List[str]
    relation: Relation
    confidence: float
    resolver: str
    reason: str


def group(assets: Sequence[AssetSignals],
          classifications: dict,
          candidates: Sequence[Sequence[str]]) -> Tuple[List[EntityGroup], List[Tuple[str, str, Resolution]]]:
    """Resolve candidate clusters into entity groups, plus everything sent to review.

    Candidates come from the cheap pass (`dedup.py`): this never compares every pair,
    which is §24 Gate 1's constraint as much as Gate 2's. Grouping is transitive only
    through confirmed SAME edges — an UNCERTAIN edge never joins two groups, because a
    chain of maybes is how two people's ID cards end up in one folder.
    """
    by_id = {a.asset_id: a for a in assets}
    groups: List[EntityGroup] = []
    review: List[Tuple[str, str, Resolution]] = []

    for cluster in candidates:
        members = [m for m in cluster if m in by_id]
        if len(members) < 2:
            continue
        anchor = members[0]
        joined = [anchor]
        relation, confidence, resolver, reasons = Relation.UNKNOWN, 0.0, "", []
        for other in members[1:]:
            r = resolve(by_id[anchor], by_id[other],
                        classifications.get(anchor), classifications.get(other))
            if r.needs_review:
                review.append((anchor, other, r))
                continue
            if r.may_merge:
                joined.append(other)
                relation = r.relation
                confidence = max(confidence, r.confidence)
                resolver = r.resolver
                reasons.append(r.why())
        if len(joined) > 1:
            groups.append(EntityGroup(joined, relation, confidence, resolver,
                                      reasons[0] if reasons else ""))
    return groups, review
