# -*- coding: utf-8 -*-
"""
INTENT SEARCH — §10's third retrieval path.

    Intent Search：用户直接说“找我的身份证正反面”“找所有有气球的照片”。   — L1 §10

Those two examples are not the same problem, and the difference is the whole design.

The first — *找我的身份证正反面* — is a query the library can answer completely: a
taxonomy node it has (`Documents > Identity > ID Cards`), plus an aspect (两面) that the
entity resolver already models as one document with more than one side.

The second — *找所有有气球的照片* — it cannot. "气球" is not a label anything in this
build produces. There is no open-vocabulary visual index, and pretending otherwise is
the failure this file exists to avoid: **a search that silently returns nothing looks
like an answer.** "You have no photos of balloons" and "I cannot search for balloons"
are completely different statements, and only one of them is true.

So every search returns what it understood, what it did not, and why — and a query
that resolved to nothing says so in those words rather than showing an empty shelf.

This is L1-B's Minimum Necessary Inference applied to retrieval: resolve the query
against what is actually indexed, cheaply, and never invent a capability to cover a
term. It is also B1-ORDER's Candidate Reduction, which until now existed per-asset
during classification and not at all during retrieval.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, List, Optional, Sequence, Tuple

from . import rules, taxonomy

# --------------------------------------------------------------------------------
# Vocabulary. Deliberately a table rather than a model: §24 Gate 5 wants multi-signal
# classification, and the retrieval side of that is a vocabulary you can read, audit
# and correct. Every entry maps a word a person would actually type to something the
# library genuinely indexes.
#
# Chinese and English side by side because the Constitution's own examples are Chinese
# and the taxonomy is English; a user typing 身份证 and a user typing "id card" are
# asking the same question.
# --------------------------------------------------------------------------------

CATEGORY_WORDS: Dict[str, str] = {
    # documents
    "身份证": "Documents > Identity > ID Cards", "id card": "Documents > Identity > ID Cards",
    "identity card": "Documents > Identity > ID Cards",
    "护照": "Documents > Identity > Passports", "passport": "Documents > Identity > Passports",
    "驾照": "Documents > Identity > Driver Licenses",
    "driving licence": "Documents > Identity > Driver Licenses",
    "drivers license": "Documents > Identity > Driver Licenses",
    "签证": "Documents > Identity > Visas", "visa": "Documents > Identity > Visas",
    "合同": "Documents > Contracts", "contract": "Documents > Contracts",
    "租房合同": "Documents > Contracts > Tenancy", "tenancy": "Documents > Contracts > Tenancy",
    "保险": "Documents > Contracts > Insurance", "insurance": "Documents > Contracts > Insurance",
    "银行": "Documents > Financial > Bank", "bank": "Documents > Financial > Bank",
    "报税": "Documents > Financial > Tax", "tax": "Documents > Financial > Tax",
    "对账单": "Documents > Financial > Statements", "statement": "Documents > Financial > Statements",
    "证件": "Documents > Identity", "documents": "Documents", "文件": "Documents",
    "医疗": "Documents > Medical", "medical": "Documents > Medical",

    # purchases
    "收据": "Purchases > Receipts", "receipt": "Purchases > Receipts",
    "发票": "Purchases > Receipts", "invoice": "Purchases > Receipts",
    "订单": "Purchases > Orders", "order": "Purchases > Orders",
    "保修": "Purchases > Warranty", "warranty": "Purchases > Warranty",
    "快递": "Purchases > Delivery", "delivery": "Purchases > Delivery",

    # everything else the tree actually has
    "截图": "Screenshots", "screenshot": "Screenshots", "screenshots": "Screenshots",
    "人": "People", "people": "People", "人物": "People",
    "地点": "Places", "places": "Places",
    "旅行": "Travel", "travel": "Travel", "trip": "Travel",
    "工作": "Work", "work": "Work",
    "下载": "Downloads", "downloads": "Downloads",
    "衣服": "Clothing", "clothing": "Clothing", "clothes": "Clothing",
    "物品": "Objects", "objects": "Objects",
}

#: 正反面 / front and back. §9's Same Entity, asked as a question rather than stored as
#: a relation: one document, more than one side.
MULTI_SIDE_WORDS = {"正反面", "正反", "两面", "front and back", "both sides", "front back"}

MEDIA_WORDS = {
    "视频": "video", "video": "video", "videos": "video", "影片": "video",
    "照片": "image", "photo": "image", "photos": "image", "图片": "image",
}

#: Time expressions the metadata can answer exactly. Anything vaguer than these
#: ("recently", "那阵子") is left unresolved rather than guessed at — a window the user
#: did not choose is a wrong answer that looks like a right one.
_YEAR = re.compile(r"\b(19|20)\d{2}\b")
_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
    "december": 12,
    "一月": 1, "二月": 2, "三月": 3, "四月": 4, "五月": 5, "六月": 6,
    "七月": 7, "八月": 8, "九月": 9, "十月": 10, "十一月": 11, "十二月": 12,
}
RELATIVE_WORDS = {"今年", "this year", "去年", "last year"}

#: Words that carry no constraint. Dropping them silently is safe; dropping a noun is
#: not, which is why this list is short and explicit.
_FILLER = {
    "find", "search", "show", "me", "all", "my", "the", "a", "an", "of", "with",
    "photos", "photo", "pictures", "picture", "images", "image", "any", "for", "in",
    "and", "or", "to", "some", "please", "from", "taken", "there", "is", "are",
}

#: Chinese is not space-separated, so filler is stripped as substrings rather than
#: matched as tokens. Without this the whole sentence comes back as one unresolved
#: term and the user is told the search understood nothing when it understood most.
_FILLER_CJK = ["找到", "所有", "那些", "我的", "时候", "照片", "图片",
               "找", "查", "搜", "我", "的", "有", "里", "中", "和", "在",
               "张", "个", "年", "月", "日", "拍", "过", "些", "了"]


@dataclass
class Query:
    """What the words resolved to, and what they did not."""
    text: str
    paths: List[str] = field(default_factory=list)
    people: List[str] = field(default_factory=list)
    places: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    media_type: Optional[str] = None
    year: Optional[int] = None
    month: Optional[int] = None
    wants_multiple_sides: bool = False
    #: Words that name nothing this library indexes. The most important field here.
    unresolved: List[str] = field(default_factory=list)
    #: One line per resolved term, in the user's words.
    understood: List[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not (self.paths or self.people or self.places or self.entities
                    or self.media_type or self.year or self.month)

    @property
    def narrows(self) -> bool:
        """Whether anything here actually restricts the library.

        A media type alone does not. “找所有有气球的照片” resolves “照片” to *images*
        and nothing else, and running that returns every photograph the user owns —
        presented as the answer to a question about balloons. Fifty results is a worse
        lie than zero, so a query whose only resolved constraint is a media type, and
        which contains a term the library cannot search, is refused rather than
        answered broadly.
        """
        return bool(self.paths or self.people or self.places or self.entities
                    or self.year or self.month)

    @property
    def answerable(self) -> bool:
        return self.narrows or not self.unresolved

    def explain(self) -> str:
        parts = []
        if self.unresolved and not self.narrows:
            words = ", ".join(f"“{w}”" for w in self.unresolved)
            return (f"I cannot search for {words} — nothing in this library is indexed "
                    "by that. Showing you everything instead would look like an answer, "
                    "so I have not. This is a limit of the search, not a statement "
                    "about your photos.")
        if self.understood:
            parts.append("I looked for " + "; ".join(self.understood) + ".")
        if self.unresolved:
            words = ", ".join(f"“{w}”" for w in self.unresolved)
            parts.append(
                f"I do not know how to search for {words} — nothing in this library is "
                "indexed by that, so it was not used to narrow the results. "
                "That is a limit of the search, not a statement about your photos.")
        if not parts:
            parts.append("I could not turn that into anything this library indexes.")
        return " ".join(parts)


def _tokens(text: str) -> List[str]:
    """Words plus CJK runs. Chinese is not space-separated, so phrase matching is done
    against the raw text and this only supplies the leftovers to report as unresolved."""
    latin = re.findall(r"[a-z0-9']+", text.lower())
    cjk = re.findall(r"[一-鿿]+", text)
    return latin + cjk


def parse(text: str, *, known_people: Sequence[str] = (),
          known_places: Sequence[str] = (),
          known_entities: Sequence[str] = ()) -> Query:
    """Resolve a sentence against what this library actually contains.

    `known_people`, `known_places` and `known_entities` come from the catalogue rather
    than from a list of names in this file. A search that only recognises names someone
    wrote down in advance is not searching the user's library.
    """
    q = Query(text=text)
    lowered = text.lower()
    consumed: List[str] = []

    def consume(phrase: str):
        consumed.append(phrase.lower())

    # ---- longest phrases first, so "id card" wins over "card" -------------
    for phrase in sorted(CATEGORY_WORDS, key=len, reverse=True):
        if phrase in lowered and not any(phrase in c and phrase != c for c in consumed):
            path = CATEGORY_WORDS[phrase]
            if path not in q.paths:
                q.paths.append(path)
                q.understood.append(f"{path} (from “{phrase}”)")
            consume(phrase)

    for phrase in sorted(MULTI_SIDE_WORDS, key=len, reverse=True):
        if phrase in lowered:
            q.wants_multiple_sides = True
            q.understood.append("documents with more than one side or page")
            consume(phrase)
            break

    for phrase, kind in MEDIA_WORDS.items():
        if phrase in lowered:
            q.media_type = kind
            q.understood.append(f"{kind}s only")
            consume(phrase)
            break

    # ---- what the library itself knows about -----------------------------
    for name in known_people:
        if name.lower() in lowered:
            q.people.append(name)
            q.understood.append(f"photos of {name}")
            consume(name)
    for name in known_places:
        if name.lower() in lowered:
            q.places.append(name)
            q.understood.append(f"in {name}")
            consume(name)
    for name in known_entities:
        if name.lower() in lowered and name not in q.people + q.places:
            q.entities.append(name)
            q.understood.append(f"the {name.lower()} it remembers")
            consume(name)

    # ---- time ------------------------------------------------------------
    year_match = _YEAR.search(text)
    if year_match:
        q.year = int(year_match.group(0))
        q.understood.append(f"taken in {q.year}")
        consume(year_match.group(0))
    for word, number in _MONTHS.items():
        if word in lowered:
            q.month = number
            q.understood.append(f"in month {number}")
            consume(word)
            break
    today = date.today()
    if "今年" in text or "this year" in lowered:
        q.year = q.year or today.year
        q.understood.append(f"taken in {q.year}")
        consume("今年")
        consume("this year")
    elif "去年" in text or "last year" in lowered:
        q.year = q.year or today.year - 1
        q.understood.append(f"taken in {q.year}")
        consume("去年")
        consume("last year")

    # ---- what is left over ----------------------------------------------
    #
    # Computed by subtraction from the sentence, not by tokenising it. Chinese runs
    # together, so a matched sub-phrase used to swallow the whole run: 找所有有气球的
    # 照片 resolved “照片” and then reported nothing unresolved, which is how a query
    # about balloons came back as the entire library with no warning at all.
    residue = lowered
    for phrase in sorted(consumed, key=len, reverse=True):
        residue = residue.replace(phrase, " ")
    for phrase in _FILLER_CJK:
        residue = residue.replace(phrase, " ")

    for token in re.findall(r"[a-z0-9']+", residue):
        # A one-letter leftover is punctuation from subtraction, not a search term:
        # consuming "receipt" out of "receipts" leaves an "s", and reporting that as
        # something the library cannot search is noise that discredits the real cases.
        if token in _FILLER or len(token) < 2:
            continue
        path = rules.SCENE_MAP.get(token)
        if path:
            if path not in q.paths:
                q.paths.append(path)
                q.understood.append(f"{path} (from “{token}”)")
            continue
        if token not in q.unresolved:
            q.unresolved.append(token)

    for token in re.findall(r"[一-鿿]+", residue):
        if token in _FILLER:
            continue
        path = rules.SCENE_MAP.get(token)
        if path:
            if path not in q.paths:
                q.paths.append(path)
                q.understood.append(f"{path} (from “{token}”)")
            continue
        if token not in q.unresolved:
            q.unresolved.append(token)

    return q


# --------------------------------------------------------------------------------
# Execution. Everything below is a query over rows the catalogue already has — no
# new signal is computed to answer a search, which is Gate 1's constraint as much as
# Gate 3's.
# --------------------------------------------------------------------------------

def _year_bounds(year: int, month: Optional[int]) -> Tuple[float, float]:
    if month:
        start = datetime(year, month, 1)
        end = datetime(year + (month == 12), (month % 12) + 1, 1)
    else:
        start, end = datetime(year, 1, 1), datetime(year + 1, 1, 1)
    return start.timestamp(), end.timestamp()


@dataclass
class Hit:
    asset_id: str
    path: str
    why: str


@dataclass
class Results:
    query: Query
    hits: List[Hit] = field(default_factory=list)
    #: Assets the query matched that also have a sibling showing another side or page.
    sides: Dict[str, List[str]] = field(default_factory=dict)

    def summary(self) -> str:
        if self.query.is_empty:
            return self.query.explain()
        head = (f"{len(self.hits)} match" + ("" if len(self.hits) == 1 else "es")
                if self.hits else "Nothing in the library matches that")
        return f"{head}. {self.query.explain()}"


def search(catalog, text: str, limit: int = 50) -> Results:
    """Answer a sentence against the catalogue."""
    people = [r[2] for r in catalog.entities(kind="person", limit=500)]
    places = [r[2] for r in catalog.entities(kind="place", limit=500)]
    others = [r[2] for r in catalog.entities(limit=1000)]
    q = parse(text, known_people=people, known_places=places, known_entities=others)
    results = Results(query=q)
    if q.is_empty or not q.answerable:
        return results

    where: List[str] = []
    args: List[object] = []

    if q.paths:
        # A node matches itself and everything under it: asking for Documents means
        # asking for the passports inside it.
        clauses = []
        for path in q.paths:
            clauses.append("(a2.path = ? OR a2.path LIKE ?)")
            args.extend([path, path + " > %"])
        where.append("(" + " OR ".join(clauses) + ")")
    if q.media_type:
        where.append("assets.media_type = ?")
        args.append(q.media_type)
    # `created_at` is stored as epoch seconds, so a year is a range rather than a
    # string prefix. Doing it as text would silently match nothing.
    if q.year:
        start, end = _year_bounds(q.year, q.month)
        where.append("assets.created_at >= ? AND assets.created_at < ?")
        args.extend([start, end])
    elif q.month:
        where.append("CAST(strftime('%m', assets.created_at, 'unixepoch') AS INTEGER) = ?")
        args.append(q.month)

    # One clause per *kind*, ANDed. "Anna in Tokyo" means both, and a single IN list
    # over people and places would have meant either — which returned nineteen assets
    # for a query that has one right answer.
    for group in (q.people, q.places, q.entities):
        if not group:
            continue
        marks = ",".join("?" for _ in group)
        where.append(
            "assets.asset_id IN (SELECT o.asset_id FROM observations o "
            f"JOIN entities e ON e.entity_id = o.entity_id WHERE e.name IN ({marks}))")
        args.extend(group)

    # Grouped per asset. Counting (asset, path) rows made one photo filed on three
    # shelves read as three results, so a seven-photo answer announced itself as fifty.
    sql = ("SELECT assets.asset_id, GROUP_CONCAT(a2.path, ' | ') FROM assets "
           "JOIN assignments a2 ON a2.asset_id = assets.asset_id")
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " GROUP BY assets.asset_id ORDER BY assets.created_at DESC LIMIT ?"
    args.append(limit)

    for asset_id, paths in catalog.db.execute(sql, tuple(args)).fetchall():
        first = (paths or "").split(" | ")[0]
        results.hits.append(Hit(asset_id, first, f"filed under {paths}"))

    if q.wants_multiple_sides:
        results.sides = _sides(catalog, [h.asset_id for h in results.hits])
    return results


def _sides(catalog, asset_ids: Sequence[str]) -> Dict[str, List[str]]:
    """The other sides or pages of the same document.

    Read from the relations the Category-Specific Entity Resolver already wrote, not
    recomputed here — “正反面” is a question about entity identity, and §24 Gate 2 says
    that answer has exactly one home.
    """
    if not asset_ids:
        return {}
    marks = ",".join("?" for _ in asset_ids)
    rows = catalog.db.execute(
        f"""SELECT group_key, asset_id FROM relations
            WHERE kind = 'same_entity' AND group_key IN (
              SELECT group_key FROM relations
              WHERE kind = 'same_entity' AND asset_id IN ({marks}))""",
        tuple(asset_ids)).fetchall()
    groups: Dict[str, List[str]] = {}
    for group_key, asset_id in rows:
        groups.setdefault(group_key, []).append(asset_id)
    return {k: sorted(v) for k, v in groups.items() if len(v) > 1}
