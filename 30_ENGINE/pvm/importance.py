# -*- coding: utf-8 -*-
"""
§4 精细 Visual Asset Taxonomy, and IMPORTANCE as an axis of its own.

Two things live here because they are the same omission seen from two sides, and the
audit had them as four separate PARTIAL clauses (S2-RISK, S3-RISKDIM, S5-FORMULA,
P25-L5, S4-CATEGORIES).

**1. §5 names six factors and the engine implemented five.**

    Category × Importance × Lifecycle × Confidence × Recoverability ×
    Personal Preference → Action Policy

Importance was folded into Category — `risk.py` graded consequence and nothing graded
value. That reads like a small gap and is not, because §18 defines the project's own
error metric as

    Weighted Error Cost = 错误 × 内容重要性 × 不可恢复程度

Three factors multiplied. If importance were a synonym for risk, that formula would
square one axis and the number the project steers by would be wrong. So they are
different questions, and the difference is sharpest exactly where it matters most:

    a photo of a passport   — risk R5 (法律/身份/金融价值), importance ORDINARY.
                              Losing the photo costs a walk to a scanner; mishandling
                              it costs identity documents in the wrong place.
    a photo of a grandmother — risk R3 (具有个人意义), importance TREASURED.
                              Mishandling it is not a category of legal exposure. It
                              is simply gone.

An engine that only grades consequence protects the passport harder than the
grandmother. §6 is not wrong about the passport; it is answering a different question,
and §5 is explicit that both answers are needed.

**2. §4 is a different taxonomy from the tree the engine files into.**

The navigational tree (`20_TIER0/study_assets/taxonomy.py`) is where a user browses.
§4 is a 13-class scheme whose stated purpose is 改变整理、风险、生命周期和动作策略 —
it exists to drive policy, not to be browsed. Two of its thirteen classes are not tree
branches at all and never could be:

    连拍/同一时刻   is a RELATION between assets (§8's equivalence group)
    珍贵记忆        is a PROPERTY of one asset (irreplaceability, §6 R6)

That is why mapping §4 onto the tree was never going to work and why the previous
attempt quietly stopped at eleven roots. `classify_asset_class` therefore takes the
relation and the property as arguments rather than reading them off a path.

Each class carries its §4 默认风险 verbatim. `tests/test_importance.py` cross-checks
that band against what `risk.classify_risk` independently derives from §6 for the same
tree prefixes — two readings of two sections of the same document, and if they
disagree one of them is a misreading.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

from .risk import Importance, Recoverability, Risk

# The scale itself is declared in `risk.py` beside the other §5 factor scales, because
# `Factors` needs the type and this module needs `Risk` — one of the two imports has to
# come first. It is re-exported here because this is where it is explained.
#
# Five levels rather than §6's seven, deliberately: importance is judged from thinner
# evidence than risk, and a scale finer than the evidence supports invites a precision
# that is not there.
MEANING = {
    Importance.I0_NONE: "已经用过，没有留存价值",
    Importance.I1_LOW: "可再获得或非本人内容",
    Importance.I2_ORDINARY: "普通生活内容，值得保留",
    Importance.I3_MEANINGFUL: "具有个人意义",
    Importance.I4_TREASURED: "不可替代",
}


def meaning(level: Importance) -> str:
    return MEANING[level]


@dataclass(frozen=True)
class AssetClass:
    """One of §4's thirteen 大类."""
    key: str
    #: 大类, verbatim from §4.
    name: str
    #: 细分类示例, verbatim from §4.
    examples: str
    #: 默认风险, verbatim from §4, as the (low, high) band it names.
    default_risk: Tuple[Risk, Risk]
    #: Baseline 内容重要性. NOT from §4 — §4 gives a risk column and no importance
    #: column. This is derived, and the derivation is stated per class below so it can
    #: be argued with rather than trusted.
    baseline_importance: Importance
    #: Tree prefixes this class covers. Empty for the two classes that are not
    #: branches — see the module docstring.
    prefixes: Tuple[str, ...] = ()
    why: str = ""


#: §4's table, in §4's order. `prefixes` are longest-first within a class and the list
#: is scanned in order, so a more specific class wins over a general one.
ASSET_CLASSES: Tuple[AssetClass, ...] = (
    AssetClass(
        "treasured_memory", "珍贵记忆", "老照片、不可替代家庭影像、特殊人生事件",
        (Risk.R6_IRREPLACEABLE, Risk.R6_IRREPLACEABLE), Importance.I4_TREASURED,
        (),
        "The one class where §4's 极高 and importance agree, because 不可替代 is a "
        "statement about value and not about consequence. Recognised from the asset's "
        "own irreplaceability, never from a folder.",
    ),
    AssetClass(
        "identity_financial", "身份/金融证件", "身份证、护照、驾照、行驶证、银行卡",
        (Risk.R5_CRITICAL, Risk.R5_CRITICAL), Importance.I2_ORDINARY,
        ("Documents > Identity", "Documents > Financial"),
        "极高 risk and ordinary importance is the sharpest case for keeping the axes "
        "apart. A passport photograph is reproducible in an afternoon; what is not "
        "recoverable is the consequence of it leaking, and that is R5's job.",
    ),
    AssetClass(
        "legal_formal", "法律/正式文件", "合同、协议、保险、税务、产权",
        (Risk.R5_CRITICAL, Risk.R5_CRITICAL), Importance.I2_ORDINARY,
        ("Documents > Contracts", "Documents > Medical"),
        "Same shape as identity documents: the counterparty holds a copy, so the "
        "photograph is rarely the only one in the world. `Documents > Other Documents` "
        "is deliberately NOT here: it is the branch for a document the classifier could "
        "not identify further, and §6 reads that as 可能承担交易/工作价值 (R4) rather "
        "than 法律/身份/金融价值 (R5). Putting the catch-all in this class was the "
        "first version of this file, and `TwoReadingsOfOneDocument` caught it.",
    ),
    AssetClass(
        "transaction", "交易与购买", "收据、发票、订单、付款、保修",
        (Risk.R4_IMPORTANT, Risk.R4_IMPORTANT), Importance.I2_ORDINARY,
        ("Documents > Receipts", "Documents > Warranty", "Purchases"),
        "A receipt matters until the return window closes and the warranty expires. "
        "That is lifecycle, which §5 already has as its own factor — importance stays "
        "ordinary rather than double-counting it.",
    ),
    AssetClass(
        "work_study", "工作/学习", "白板、会议、课堂、项目资料",
        (Risk.R3_PERSONAL, Risk.R4_IMPORTANT), Importance.I2_ORDINARY,
        ("Work",),
        "中-高 risk because work content can carry obligations. Ordinary importance "
        "because a photographed whiteboard is a working note, and §14 is where a user "
        "who feels otherwise says so.",
    ),
    AssetClass(
        "travel_event", "旅行/事件", "机票、登机牌、酒店、门票、活动",
        (Risk.R3_PERSONAL, Risk.R4_IMPORTANT), Importance.I3_MEANINGFUL,
        ("Travel",),
        "An occasion the user was part of. §4's examples are the paperwork of a trip; "
        "the engine's Travel branch holds the trip itself, which is the more "
        "meaningful half and is what this scores.",
    ),
    AssetClass(
        "people_family", "人物与家庭", "自拍、朋友、家庭、儿童、合照",
        (Risk.R3_PERSONAL, Risk.R4_IMPORTANT), Importance.I3_MEANINGFUL,
        ("People",),
        "The class the whole distinction exists for. §6 puts people at R3, below a "
        "receipt at R4 — correct about consequence and, taken alone, an engine that "
        "guards receipts more carefully than faces.",
    ),
    AssetClass(
        "possession_record", "物品记录", "家电、家具、衣服、商品、设备序列号",
        (Risk.R2_NORMAL, Risk.R2_NORMAL), Importance.I1_LOW,
        ("Objects", "Clothing"),
        "A photograph taken to remember a fact — a serial number, a size, what the "
        "shelf looked like. The fact outlives the photograph.",
    ),
    AssetClass(
        "burst_moment", "连拍/同一时刻", "同人物同场景短时间多张",
        (Risk.R1_LOW_VALUE, Risk.R2_NORMAL), Importance.I1_LOW,
        (),
        "A relation, not a folder: membership of §8's equivalence group. Scored low on "
        "its own because the moment's value sits in the group, not in the "
        "forty-first frame — but §8 requires this to be read together with the "
        "subject's risk, so `assess` applies it as a reduction rather than a verdict.",
    ),
    AssetClass(
        "everyday_photo", "普通摄影", "风景、食物、街景、随手拍",
        (Risk.R1_LOW_VALUE, Risk.R2_NORMAL), Importance.I2_ORDINARY,
        ("Places",),
        "The ordinary content of a life. Not irreplaceable, and not disposable either "
        "— this is the bulk of a library and the default when nothing else fits.",
    ),
    AssetClass(
        "ordinary_screenshot", "普通截图", "网页、聊天、新闻、商品、工作截图",
        (Risk.R1_LOW_VALUE, Risk.R2_NORMAL), Importance.I1_LOW,
        ("Screenshots",),
        "Kept in case, almost never looked at again. §4 lists 工作截图 here rather "
        "than under 工作/学习, and the engine follows §4.",
    ),
    AssetClass(
        "downloaded", "网络/下载内容", "Meme、表情包、壁纸、社媒图、宣传图",
        (Risk.R0_DISPOSABLE, Risk.R1_LOW_VALUE), Importance.I1_LOW,
        ("Downloads",),
        "Not the user's own content and available from where it came from. Low rather "
        "than none: a saved image was saved on purpose.",
    ),
    AssetClass(
        "transient_info", "临时信息", "验证码、取件码、停车位置、临时导航、一次性报错",
        (Risk.R1_LOW_VALUE, Risk.R1_LOW_VALUE), Importance.I0_NONE,
        ("Screenshots > Temporary", "Screenshots > Errors"),
        "The only class that is genuinely worth nothing once used, and the reason I0 "
        "exists at all.",
    ),
)

#: The fourteenth entry, and deliberately not one of §4's thirteen — it is what the
#: engine says when §4 does not describe an asset. `Documents > Other Documents` is the
#: case that forced it into existence: a document the classifier could not identify
#: further is not a contract, not a receipt, and certainly not 随手拍, and quietly
#: filing it under whichever class was nearest is how a taxonomy stops meaning anything.
#: Its risk band is the whole scale, so the §4/§6 cross-check is vacuous for it by
#: construction rather than by an assertion nobody checked.
UNDESCRIBED = AssetClass(
    "undescribed", "（§4 未描述）", "分类器未能进一步识别的资产",
    (Risk.R0_DISPOSABLE, Risk.R6_IRREPLACEABLE), Importance.I2_ORDINARY, (),
    "§4 says 尽可能细，但只细到足以改变用户体验或处理决策 — it does not claim to cover "
    "everything, and neither does this. Ordinary importance because that is the level "
    "that changes nothing: the asset is scored on its risk, its lifecycle and its "
    "confidence, exactly as it was before this axis existed.",
)

BY_KEY = {c.key: c for c in ASSET_CLASSES}
BY_KEY[UNDESCRIBED.key] = UNDESCRIBED
DEFAULT_CLASS = UNDESCRIBED

#: How many other assets a named person has to appear in before they read as somebody
#: in this user's life rather than somebody who was once in shot. Twelve is a month of
#: a person appearing every few days; below that the library has not said enough.
RECURRING_PERSON = 12

#: An equivalence group this size or larger is a burst, and a single frame of it is
#: worth less than the group. Six is where a considered set of shots of one subject
#: becomes a held shutter.
BURST_SIZE = 6


def classify_asset_class(paths: Sequence[str], *,
                         is_irreplaceable: bool = False,
                         in_equivalence_group: bool = False) -> AssetClass:
    """§4's 大类 for one asset.

    The two non-branch classes are checked first and in this order: irreplaceability
    outranks everything, and one frame of a burst of a treasured moment is still part
    of a treasured moment.
    """
    if is_irreplaceable:
        return BY_KEY["treasured_memory"]

    best: Optional[AssetClass] = None
    best_rank = len(ASSET_CLASSES)
    best_len = -1
    for rank, cls in enumerate(ASSET_CLASSES):
        for prefix in cls.prefixes:
            if any(p == prefix or p.startswith(prefix + " > ") for p in paths):
                # Longest prefix wins; ties break on §4's own order, which runs from
                # most consequential to least.
                if len(prefix) > best_len or (len(prefix) == best_len and rank < best_rank):
                    best, best_rank, best_len = cls, rank, len(prefix)
    if best is not None:
        return best
    if in_equivalence_group:
        return BY_KEY["burst_moment"]
    return UNDESCRIBED


@dataclass
class ImportanceSignals:
    """Everything that bears on 内容重要性, gathered in one place so an assessment can
    never be made from a subset by accident — the same reason `risk.Factors` exists."""
    paths: Sequence[str] = ()
    recoverability: Recoverability = Recoverability.RECOVERABLE
    #: How many assets in the whole library the named people in this one also appear
    #: in. Zero when nobody here is named.
    people_recurrence: int = 0
    #: Size of the §8 equivalence group this asset belongs to; 1 when it is alone.
    group_size: int = 1
    in_equivalence_group: bool = False
    is_exact_duplicate: bool = False
    is_irreplaceable: bool = False
    #: §14. The user's own settled answer for this category, when they have given one.
    user_protects_category: bool = False


@dataclass
class Assessment:
    level: Importance
    asset_class: AssetClass
    reasons: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        return f"{self.level.name} ({self.asset_class.name}): " + "; ".join(self.reasons)


def assess(s: ImportanceSignals) -> Assessment:
    """内容重要性, from the class baseline and what the library knows about this asset.

    Every adjustment is ±1 and the reason is recorded, because an importance score
    that cannot say why it is what it is cannot be argued with by the person whose
    photographs it is about.
    """
    cls = classify_asset_class(s.paths, is_irreplaceable=s.is_irreplaceable,
                               in_equivalence_group=s.in_equivalence_group)
    level = int(cls.baseline_importance)
    reasons = [f"§4 {cls.name} baseline {cls.baseline_importance.name}"]

    if s.recoverability == Recoverability.IRREPLACEABLE:
        level = int(Importance.I4_TREASURED)
        reasons.append("irreplaceable — nothing else raises or lowers this")
        return Assessment(Importance(level), cls, reasons)

    if s.people_recurrence >= RECURRING_PERSON:
        level += 1
        reasons.append(
            f"someone here appears in {s.people_recurrence} other photographs — "
            "a person in this user's life, not a passer-by")

    if s.user_protects_category:
        level += 1
        reasons.append("§14 — the user has consistently protected this category")

    # §8: 同样的相似度，在 Meme 和家庭照片上采取不同策略. The reduction is applied to
    # the frame and not to the moment, and it is one level, so a burst of a treasured
    # occasion does not fall out of protection because the shutter was held down.
    if s.in_equivalence_group and s.group_size >= BURST_SIZE:
        level -= 1
        reasons.append(
            f"one frame of {s.group_size} near-identical — the moment is kept, "
            "this particular frame is not the whole of it")

    if s.is_exact_duplicate:
        level -= 1
        reasons.append("a byte-identical copy exists — this file is not the content")

    level = max(int(Importance.I0_NONE), min(int(Importance.I4_TREASURED), level))
    return Assessment(Importance(level), cls, reasons)


def class_table() -> str:
    """§4's table as the engine implements it, generated from the code so the two
    cannot drift."""
    lines = ["| 大类 | 细分类示例 | §4 默认风险 | importance | tree |",
             "|---|---|---|---|---|"]
    for c in ASSET_CLASSES + (UNDESCRIBED,):
        lo, hi = c.default_risk
        band = lo.name if lo == hi else f"{lo.name}–{hi.name}"
        where = ", ".join(c.prefixes) if c.prefixes else "*(a relation, not a branch)*"
        lines.append(f"| {c.name} | {c.examples} | {band} | "
                     f"{c.baseline_importance.name} | {where} |")
    return "\n".join(lines)
