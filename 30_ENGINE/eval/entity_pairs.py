# -*- coding: utf-8 -*-
"""
GROUND TRUTH FOR GATE 2 — hand-built, because there is nothing else.

Tier 1-B is explicit about what it wants:

    建立人工 ground truth，并加入 hard negatives：看起来相似但实际不同的证件页、
    商品、文件页。                                             — L2 Tier 1-B

The 10k labelled library carries category labels and no same-entity labels, so there is
no corpus to measure this against. `eval/adapter.py` refuses to hand ground-truth
fields to the engine at all. This file is therefore hand-written, and that is a real
limitation, stated here rather than buried: **these are cases a person constructed, not
a sample of a real library.** A resolver tuned until this file goes green would be
tuned to this file. What it can honestly do is the thing Tier 1-B actually asks for —
show whether the hard negatives are separated, and where the resolver refuses to guess.

Every pair says *why* it is what it is, so a reader can disagree with the label rather
than only with the score.

The hard negatives are the point. Anyone can separate a passport from a beach photo.
The cases that decide Gate 2 are two people's ID cards on the same government template,
two receipts from the same shop on the same day, and page 1 of two different contracts
that share three paragraphs of boilerplate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional

from pvm.signals import AssetSignals, GeoFix, PlaceName, SceneLabel

LONDON = (51.5074, -0.1278)
BRIGHTON = (50.8225, -0.1372)


def _asset(asset_id: str, *, text: str = "", when: datetime = None, dhash: int = None,
           screenshot: bool = False, labels: List[str] = (), geo=None,
           content_hash: str = None) -> AssetSignals:
    a = AssetSignals(asset_id)
    a.created_at = when or datetime(2025, 6, 18, 14)
    a.pixel_w, a.pixel_h, a.byte_size = 4032, 3024, 500_000
    a.content_hash = content_hash or f"sha::{asset_id}"
    a.dhash = dhash if dhash is not None else 0x1234_5678_9ABC_DEF0
    if text:
        a.ocr_ran, a.ocr_text = True, text
    if screenshot:
        a.is_screenshot, a.source = True, "screenshot"
        a.pixel_w, a.pixel_h = 1170, 2532
    else:
        a.source = "camera"
    a.scene_labels = [SceneLabel(x, 0.8) for x in labels]
    if geo:
        a.geo = GeoFix(*geo)
        a.place = PlaceName("United Kingdom", "London" if geo == LONDON else "Brighton", 0.9)
    return a


@dataclass
class Pair:
    """One labelled comparison."""
    pair_id: str
    a: AssetSignals
    b: AssetSignals
    same: bool
    category: str            # document | screenshot | object | photo
    hard_negative: bool = False
    note: str = ""


def _p(pair_id, a, b, same, category, note, hard=False) -> Pair:
    return Pair(pair_id, a, b, same, category, hard, note)


# Contract boilerplate the hard negatives share, so "looks alike" is not a strawman.
_BOILER = ("THIS AGREEMENT is made between the parties named below and shall be "
           "governed by the laws of England and Wales. Neither party shall be liable "
           "for indirect or consequential loss. ")

DAY = datetime(2025, 6, 18, 14)


def build() -> List[Pair]:
    pairs: List[Pair] = []

    # ---------------------------------------------------------------- documents
    # POSITIVES
    pairs.append(_p(
        "doc-same-passport",
        _asset("pp-a", text="PASSPORT UNITED KINGDOM SURNAME: DOE PASSPORT NO: 123456789"),
        _asset("pp-b", text="PASSPORT UNITED KINGDOM SURNAME: DOE PASSPORT NO: 123456789",
               when=DAY + timedelta(minutes=3)),
        True, "document", "the same passport photographed twice, seconds apart"))

    pairs.append(_p(
        "doc-same-passport-relit",
        _asset("pp-c", text="PASSPORT UNITED KINGDOM SURNAME: DOE PASSPORT NO: 123456789"),
        _asset("pp-d", text="PASSPORT UNITED KINGDOM  SURNAME DOE  PASSPORT NO 123456789",
               when=DAY + timedelta(days=200), dhash=0xFFFF_0000_FFFF_0000),
        True, "document",
        "the same passport photographed months later under different light — the OCR "
        "reads slightly differently and the number does not"))

    pairs.append(_p(
        "doc-contract-pages",
        _asset("ct-1", text=_BOILER + "CONTRACT NO: AB-4417 PAGE 1 OF 4"),
        _asset("ct-2", text=_BOILER + "CONTRACT NO: AB-4417 PAGE 2 OF 4"),
        True, "document", "two pages of one contract — one document, both kept"))

    pairs.append(_p(
        "doc-invoice-reshot",
        _asset("inv-a", text="INVOICE NO: INV-2025-889 TOTAL 240.00"),
        _asset("inv-b", text="INVOICE NO INV-2025-889  TOTAL 240.00 PAID",
               when=DAY + timedelta(days=30)),
        True, "document", "the same invoice, photographed again after it was paid"))

    # HARD NEGATIVES — the cases Gate 2 is judged on.
    pairs.append(_p(
        "doc-two-passports", 
        _asset("pp-jane", text="PASSPORT UNITED KINGDOM SURNAME: DOE PASSPORT NO: 123456789"),
        _asset("pp-john", text="PASSPORT UNITED KINGDOM SURNAME: DOE PASSPORT NO: 987654321",
               dhash=0x1234_5678_9ABC_DEF1),
        False, "document",
        "two passports of two people with the same surname, on the same template — "
        "identical layout, identical wording, different number", hard=True))

    pairs.append(_p(
        "doc-two-id-cards",
        _asset("id-a", text="IDENTITY CARD NAME: JANE DOE DATE OF BIRTH 1990-01-04"),
        _asset("id-b", text="IDENTITY CARD NAME: JOHN ROE DATE OF BIRTH 1988-11-22",
               dhash=0x1234_5678_9ABC_DEF1),
        False, "document",
        "two ID cards on one government template — the only thing that differs is the "
        "holder, which is exactly what must not be merged", hard=True))

    pairs.append(_p(
        "doc-two-contracts-page1",
        _asset("ctx-1", text=_BOILER + "CONTRACT NO: AB-4417 PAGE 1 OF 4"),
        _asset("ctx-2", text=_BOILER + "CONTRACT NO: ZZ-9902 PAGE 1 OF 4",
               dhash=0x1234_5678_9ABC_DEF1),
        False, "document",
        "page 1 of two different contracts sharing three paragraphs of boilerplate — "
        "same page number, same page count, same template", hard=True))

    pairs.append(_p(
        "doc-two-receipts-same-shop",
        _asset("rc-a", text="RECEIPT NORTHSIDE COFFEE RECEIPT NO: 88121 TOTAL 4.20"),
        _asset("rc-b", text="RECEIPT NORTHSIDE COFFEE RECEIPT NO: 88377 TOTAL 4.20",
               when=DAY + timedelta(days=1), dhash=0x1234_5678_9ABC_DEF1),
        False, "document",
        "two visits to one coffee shop, same total, same layout, different receipt "
        "number", hard=True))

    pairs.append(_p(
        "doc-contract-vs-manual",
        _asset("ct-3", text=_BOILER + "CONTRACT NO: AB-4417 PAGE 3 OF 4"),
        _asset("man-1", text="USER MANUAL SAFETY INFORMATION DO NOT IMMERSE IN WATER"),
        False, "document", "unrelated documents — the easy case, kept as a control"))

    # NO IDENTIFIER ANYWHERE — the text fingerprint is the only evidence there is.
    pairs.append(_p(
        "doc-no-reference",
        _asset("ten-a", text="TENANCY AGREEMENT THE LANDLORD AND THE TENANT AGREE AS "
                             "FOLLOWS RENT IS PAYABLE MONTHLY IN ADVANCE"),
        _asset("ten-b", text="TENANCY AGREEMENT THE LANDLORD AND THE TENANT AGREE AS "
                             "FOLLOWS RENT IS PAYABLE MONTHLY IN ADVANCE",
               when=DAY + timedelta(days=7), dhash=0x1234_5678_9ABC_DEF1),
        True, "document",
        "the same tenancy page photographed twice a week apart — no reference number "
        "anywhere, so the text fingerprint is all there is"))

    pairs.append(_p(
        "doc-two-tenancies",
        _asset("ten-c", text="TENANCY AGREEMENT THE LANDLORD AND THE TENANT AGREE AS "
                             "FOLLOWS RENT IS PAYABLE MONTHLY IN ADVANCE"),
        _asset("ten-d", text="TENANCY AGREEMENT THE LANDLORD AND THE TENANT AGREE AS "
                             "FOLLOWS DEPOSIT HELD IN A GOVERNMENT SCHEME NO PETS",
               when=DAY + timedelta(days=400), dhash=0x1234_5678_9ABC_DEF1),
        False, "document",
        "two tenancy agreements on the same template, four hundred days apart — the "
        "opening is word for word identical and the terms are not", hard=True))

    # ---------------------------------------------------------------- screenshots
    pairs.append(_p(
        "shot-order-stages",
        _asset("ord-1", text="ORDER CONFIRMED ORDER NO: A88-2291 HEADPHONES",
               screenshot=True),
        _asset("ord-2", text="OUT FOR DELIVERY ORDER NO: A88-2291 ARRIVING TODAY",
               screenshot=True, when=DAY + timedelta(days=2),
               dhash=0x0F0F_0F0F_0F0F_0F0F),
        True, "screenshot",
        "one order, captured at two stages — the join §15 Purchase Memory is built on"))

    pairs.append(_p(
        "shot-two-orders-same-shop",
        _asset("ord-3", text="ORDER CONFIRMED ORDER NO: A88-2291 HEADPHONES",
               screenshot=True),
        _asset("ord-4", text="ORDER CONFIRMED ORDER NO: B12-7740 KEYBOARD",
               screenshot=True, when=DAY + timedelta(days=5),
               dhash=0x1234_5678_9ABC_DEF1),
        False, "screenshot",
        "two orders from one retailer — same app, same screen design, different order",
        hard=True))

    pairs.append(_p(
        "shot-same-screen-twice",
        _asset("err-1", text="ERROR 0x8007 THE OPERATION COULD NOT BE COMPLETED",
               screenshot=True),
        _asset("err-2", text="ERROR 0x8007 THE OPERATION COULD NOT BE COMPLETED",
               screenshot=True, when=DAY + timedelta(minutes=1),
               dhash=0x1234_5678_9ABC_DEF0),
        True, "screenshot", "the same error screen captured twice in a minute"))

    pairs.append(_p(
        "shot-different-chats",
        _asset("chat-1", text="whatsapp delivered read 14:02 see you at eight",
               screenshot=True),
        _asset("chat-2", text="whatsapp delivered read 09:30 running late sorry",
               screenshot=True, when=DAY + timedelta(days=3),
               dhash=0x1234_5678_9ABC_DEF1),
        False, "screenshot",
        "two chat screenshots from the same app on different days", hard=True))

    # ---------------------------------------------------------------- objects
    pairs.append(_p(
        "obj-same-bike-same-view",
        _asset("bike-1", labels=["bicycle"], dhash=0xAAAA_BBBB_CCCC_DDDD, geo=LONDON),
        _asset("bike-2", labels=["bicycle"], dhash=0xAAAA_BBBB_CCCC_DDDF,
               when=DAY + timedelta(seconds=4), geo=LONDON),
        True, "object", "one bicycle, two shots seconds apart from the same spot"))

    pairs.append(_p(
        "obj-same-bike-months-later",
        _asset("bike-3", labels=["bicycle"], dhash=0xAAAA_BBBB_CCCC_DDDD, geo=LONDON),
        _asset("bike-4", labels=["bicycle"], dhash=0xAAAA_BBBB_CCCC_DDDE,
               when=DAY + timedelta(days=120), geo=BRIGHTON),
        True, "object",
        "the same bicycle photographed from the same angle four months later, "
        "somewhere else — Object Memory's core case"))

    pairs.append(_p(
        "obj-same-chair-other-angle",
        _asset("chair-1", labels=["chair"], dhash=0x0F0F_0F0F_0F0F_0F0F),
        _asset("chair-2", labels=["chair"], dhash=0xF0F0_F0F0_F0F0_F0F0,
               when=DAY + timedelta(days=2)),
        True, "object",
        "one chair from two opposite angles. Recorded as SAME because it is; expected "
        "to come back UNCERTAIN, because without a visual embedding nothing here can "
        "join two views of one object. This pair exists to make that gap visible."))

    pairs.append(_p(
        "obj-two-identical-chairs",
        _asset("chair-3", labels=["chair"], dhash=0x0F0F_0F0F_0F0F_0F0F),
        _asset("chair-4", labels=["chair"], dhash=0x0F0F_0F0F_0F0F_0F0E,
               when=DAY + timedelta(days=2)),
        False, "object",
        "two chairs of the same model in the same room. Indistinguishable by any "
        "signal in this build — a hard negative that also shows the ceiling", hard=True))

    pairs.append(_p(
        "obj-bike-vs-laptop",
        _asset("bike-5", labels=["bicycle"], dhash=0xAAAA_BBBB_CCCC_DDDD),
        _asset("lap-1", labels=["laptop"], dhash=0x1111_2222_3333_4444),
        False, "object", "different objects — a control"))

    # ---------------------------------------------------------------- photos
    pairs.append(_p(
        "photo-burst",
        _asset("b-1", dhash=0xC0FF_EE00_C0FF_EE00, geo=LONDON),
        _asset("b-2", dhash=0xC0FF_EE00_C0FF_EE02, when=DAY + timedelta(seconds=1),
               geo=LONDON),
        True, "photo", "two frames of one burst"))

    pairs.append(_p(
        "photo-same-view-two-cities",
        _asset("v-1", dhash=0xC0FF_EE00_C0FF_EE00, geo=LONDON),
        _asset("v-2", dhash=0xC0FF_EE00_C0FF_EE01, when=DAY + timedelta(hours=2),
               geo=BRIGHTON),
        False, "photo",
        "two photographs that look alike, taken 80 km apart within the same "
        "afternoon — appearance alone would merge them", hard=True))

    pairs.append(_p(
        "photo-unrelated",
        _asset("u-1", dhash=0x0000_FFFF_0000_FFFF),
        _asset("u-2", dhash=0xFFFF_0000_FFFF_0000, when=DAY + timedelta(days=40)),
        False, "photo", "two unrelated pictures — a control"))

    # ---------------------------------------------------------------- bytes
    pairs.append(_p(
        "exact-copy",
        _asset("meme-1", content_hash="sha::meme", dhash=0x0000_0000_0000_0000,
               labels=["meme"]),
        _asset("meme-2", content_hash="sha::meme", dhash=0x0000_0000_0000_0000,
               when=DAY + timedelta(days=35), labels=["meme"]),
        True, "photo",
        "the same file downloaded twice. Note both hashes are 0: FC-1a says a dHash of "
        "0 is also what failure returns, so this pair only resolves because byte "
        "identity is checked before appearance"))

    return pairs


def summary() -> str:
    pairs = build()
    hard = sum(1 for p in pairs if p.hard_negative)
    same = sum(1 for p in pairs if p.same)
    return (f"{len(pairs)} hand-built pairs: {same} same, {len(pairs) - same} different, "
            f"of which {hard} are hard negatives")


if __name__ == "__main__":
    print(summary())
