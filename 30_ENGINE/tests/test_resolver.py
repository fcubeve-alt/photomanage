# -*- coding: utf-8 -*-
"""
Tests for the Category-Specific Entity Resolver — §24 Gate 2.

`eval/evaluate_entities.py` scores the resolver against hand-built pairs and reports
False Merge and False Split. These are the different job: they lock the *rules*, so a
later change that improves the score by loosening a boundary fails here instead of
passing there.

The asymmetry is the whole design. Tier 1-B: 错误合并证件/合同的代价远高于漏检 — the
cost of wrongly merging two people's ID cards is far above the cost of missing a match.
So most of this file is about what the resolver must refuse to do.

    python -m unittest discover -s tests -v
"""

import os
import sys
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pvm import dedup, resolver                                         # noqa: E402
from pvm.classifier import Classifier                                   # noqa: E402
from pvm.context import build_context                                   # noqa: E402
from pvm.resolver import (Relation, Verdict, holder_names, identifiers, # noqa: E402
                          page_of, resolve, text_similarity)
from pvm.signals import (AssetSignals, GeoFix, PlaceName, SceneLabel,   # noqa: E402
                         Tier)
from pvm.verdict import Assignment, Classification, Evidence            # noqa: E402

WHEN = datetime(2025, 6, 18, 14)
LONDON = GeoFix(51.5074, -0.1278)
BRIGHTON = GeoFix(50.8225, -0.1372)


def asset(aid, *, text="", when=None, dhash=0x1234_5678_9ABC_DEF0, labels=(),
          screenshot=False, geo=None, content_hash=None) -> AssetSignals:
    a = AssetSignals(aid)
    a.created_at = when or WHEN
    a.pixel_w, a.pixel_h, a.byte_size = 4032, 3024, 500_000
    a.content_hash = content_hash or f"sha::{aid}"
    a.dhash = dhash
    a.source = "screenshot" if screenshot else "camera"
    a.is_screenshot = screenshot
    if text:
        a.ocr_ran, a.ocr_text = True, text
    a.scene_labels = [SceneLabel(x, 0.8) for x in labels]
    if geo:
        a.geo = geo
        a.place = PlaceName("United Kingdom", "London", 0.9)
    return a


def _as_document(asset_id: str) -> Classification:
    """A classification that says "this is a document" and nothing more — the state a
    photograph of paperwork reaches when the OCR came back empty."""
    c = Classification(asset_id)
    c.add(Assignment("Documents",
                     [Evidence("shape", Tier.METADATA, 0.6,
                               "the page shape reads as paperwork")],
                     is_primary=True))
    return c


def decide(a, b):
    ctx = build_context([a, b])
    clf = Classifier(ctx)
    return resolve(a, b, clf.classify(a), clf.classify(b))


class FieldExtraction(unittest.TestCase):
    """A wrong identifier is worse than none: none ends at UNCERTAIN, wrong ends at
    SAME. Every case here is one the first version of the patterns got wrong."""

    def test_a_label_alone_is_not_an_identifier(self):
        self.assertEqual(set(), identifiers("PASSPORT UNITED KINGDOM"))

    def test_no_inside_a_word_is_not_the_word_no(self):
        self.assertEqual(set(), identifiers("RECEIPT NORTHSIDE COFFEE"))

    def test_an_identifier_must_contain_a_digit(self):
        self.assertEqual(set(), identifiers("ORDER CONFIRMED"))
        self.assertEqual({"A882291"}, identifiers("ORDER NO: A88-2291"))

    def test_punctuation_inside_an_identifier_is_ignored(self):
        self.assertEqual({"INV2025889"}, identifiers("INVOICE NO: INV-2025-889"))
        self.assertEqual({"INV2025889"}, identifiers("INVOICE NO. INV/2025/889"))

    def test_a_known_limit_ocr_that_breaks_an_identifier_into_words(self):
        """When OCR reads `INV-2025-889` as three space-separated tokens the pattern
        no longer sees an identifier, and the pair falls through to the text
        fingerprint. That is a false-split risk, and it is the right way round: the
        alternative — allowing spaces inside a reference — would capture `ORDER NO 5
        ITEMS TOTAL 12` as the reference `512`, and a wrong reference merges."""
        self.assertEqual(set(), identifiers("INVOICE NO INV 2025 889"))

    def test_a_holder_name_stops_at_two_words(self):
        self.assertEqual({"JANE DOE"},
                         holder_names("IDENTITY CARD NAME: JANE DOE DATE OF BIRTH 1990"))

    def test_prose_has_no_holder(self):
        self.assertEqual(set(), holder_names("the name of this thing is unclear"))

    def test_page_markers(self):
        self.assertEqual((2, 4), page_of("CONTRACT PAGE 2 OF 4"))
        self.assertEqual((3, 7), page_of("第 3 页 共 7 页"))
        self.assertIsNone(page_of("no pagination here"))

    def test_similarity_of_nothing_is_not_evidence_of_difference(self):
        self.assertEqual(0.0, text_similarity("", "anything at all here"),
                         "an empty side means no evidence, and callers must not read "
                         "0.0 as proof that the two differ")


class DocumentsAreNeverMergedOnAppearance(unittest.TestCase):
    """The Tier 1-B PASS criterion, as rules rather than as a score."""

    def test_two_passports_with_different_numbers_are_two_passports(self):
        a = asset("p1", text="PASSPORT UNITED KINGDOM SURNAME: DOE PASSPORT NO: 123456789")
        b = asset("p2", text="PASSPORT UNITED KINGDOM SURNAME: DOE PASSPORT NO: 987654321",
                  dhash=0x1234_5678_9ABC_DEF1)
        r = decide(a, b)
        self.assertIs(Verdict.DIFFERENT, r.verdict)
        self.assertFalse(r.may_merge)

    def test_two_id_cards_with_different_holders_are_two_cards(self):
        a = asset("i1", text="IDENTITY CARD NAME: JANE DOE DATE OF BIRTH 1990-01-04")
        b = asset("i2", text="IDENTITY CARD NAME: JOHN ROE DATE OF BIRTH 1988-11-22",
                  dhash=0x1234_5678_9ABC_DEF1)
        self.assertIs(Verdict.DIFFERENT, decide(a, b).verdict)

    def test_a_disagreeing_reference_beats_every_similarity_signal(self):
        """Page 1 of two contracts on one template: same page number, same page count,
        same boilerplate. Only the contract number differs, and it has to win."""
        boiler = ("THIS AGREEMENT is made between the parties and shall be governed "
                  "by the laws of England and Wales. ")
        a = asset("c1", text=boiler + "CONTRACT NO: AB-4417 PAGE 1 OF 4")
        b = asset("c2", text=boiler + "CONTRACT NO: ZZ-9902 PAGE 1 OF 4",
                  dhash=0x1234_5678_9ABC_DEF1)
        r = decide(a, b)
        self.assertIs(Verdict.DIFFERENT, r.verdict)
        self.assertEqual("document.identifier", r.resolver)

    def test_pages_of_one_contract_are_one_document_and_both_are_kept(self):
        boiler = "THIS AGREEMENT is made between the parties named below. "
        a = asset("c3", text=boiler + "CONTRACT NO: AB-4417 PAGE 1 OF 4")
        b = asset("c4", text=boiler + "CONTRACT NO: AB-4417 PAGE 2 OF 4",
                  dhash=0x1234_5678_9ABC_DEF1)
        r = decide(a, b)
        self.assertIs(Verdict.SAME, r.verdict)
        self.assertIs(Relation.OTHER_PAGE, r.relation)

    def test_an_unreadable_document_is_never_merged_on_looks(self):
        """Two document photographs that look identical and carry no readable text.
        Appearance is the only signal left, and for documents appearance is not
        enough — the answer has to be a question."""
        a = asset("d1")
        b = asset("d2", dhash=0x1234_5678_9ABC_DEF0)
        r = resolve(a, b, _as_document("d1"), _as_document("d2"))
        self.assertIs(Verdict.UNCERTAIN, r.verdict)
        self.assertFalse(r.may_merge)

    def test_one_document_on_two_occasions_is_a_version_not_a_duplicate(self):
        """§9: both records survive. `SAME_INSTANCE` would let a caller fold them."""
        a = asset("v1", text="INVOICE NO: INV-2025-889 TOTAL 240.00")
        b = asset("v2", text="INVOICE NO: INV-2025-889 TOTAL 240.00 PAID",
                  when=WHEN + timedelta(days=30), dhash=0x1234_5678_9ABC_DEF1)
        r = decide(a, b)
        self.assertIs(Verdict.SAME, r.verdict)
        self.assertIs(Relation.OTHER_VERSION, r.relation)


class ScreenshotsJoinOnReference(unittest.TestCase):

    def test_one_order_captured_at_two_stages_is_one_purchase(self):
        a = asset("o1", text="ORDER CONFIRMED ORDER NO: A88-2291 HEADPHONES",
                  screenshot=True)
        b = asset("o2", text="OUT FOR DELIVERY ORDER NO: A88-2291 ARRIVING TODAY",
                  screenshot=True, when=WHEN + timedelta(days=2),
                  dhash=0x0F0F_0F0F_0F0F_0F0F)
        r = decide(a, b)
        self.assertIs(Verdict.SAME, r.verdict)
        self.assertTrue(r.may_merge)

    def test_two_orders_from_one_retailer_are_two_orders(self):
        a = asset("o3", text="ORDER CONFIRMED ORDER NO: A88-2291 HEADPHONES",
                  screenshot=True)
        b = asset("o4", text="ORDER CONFIRMED ORDER NO: B12-7740 KEYBOARD",
                  screenshot=True, dhash=0x1234_5678_9ABC_DEF1)
        self.assertIs(Verdict.DIFFERENT, decide(a, b).verdict)


class ObjectsStopAtTheHonestLimit(unittest.TestCase):
    """Tier 1 allows a category to be downgraded to Review rather than guessed:
    部分类别（例如复杂物品识别）暂时做不到高置信度，可以先把这些类别降级为
    「Review Queue 优先」上线. This is that downgrade, made explicit."""

    def test_the_same_object_within_one_moment_resolves(self):
        a = asset("b1", labels=["bicycle"], dhash=0xAAAA_BBBB_CCCC_DDDD)
        b = asset("b2", labels=["bicycle"], dhash=0xAAAA_BBBB_CCCC_DDDF,
                  when=WHEN + timedelta(seconds=4))
        self.assertIs(Verdict.SAME, decide(a, b).verdict)

    def test_across_occasions_it_refuses_rather_than_guesses(self):
        a = asset("c1", labels=["chair"], dhash=0x0F0F_0F0F_0F0F_0F0F)
        b = asset("c2", labels=["chair"], dhash=0x0F0F_0F0F_0F0F_0F0E,
                  when=WHEN + timedelta(days=2))
        r = decide(a, b)
        self.assertIs(Verdict.UNCERTAIN, r.verdict,
                      "one chair twice and two identical chairs look the same here; "
                      "answering SAME would merge the second case")
        self.assertTrue(r.needs_review)
        self.assertFalse(r.may_merge)

    def test_a_missing_hash_is_never_read_as_a_match(self):
        """FC-1a: dHash returns 0 both for flat images and for failure."""
        a = asset("h1", labels=["chair"], dhash=0)
        b = asset("h2", labels=["chair"], dhash=0)
        self.assertIs(Verdict.UNCERTAIN, decide(a, b).verdict)


class PhotosUsePlaceAndTime(unittest.TestCase):

    def test_lookalikes_taken_in_two_cities_are_two_photographs(self):
        a = asset("v1", dhash=0xC0FF_EE00_C0FF_EE00, geo=LONDON)
        b = asset("v2", dhash=0xC0FF_EE00_C0FF_EE01, when=WHEN + timedelta(hours=2))
        b.geo, b.place = BRIGHTON, PlaceName("United Kingdom", "Brighton", 0.9)
        self.assertIs(Verdict.DIFFERENT, decide(a, b).verdict)

    def test_byte_identity_settles_it_before_any_category_question(self):
        a = asset("m1", content_hash="sha::meme", dhash=0)
        b = asset("m2", content_hash="sha::meme", dhash=0,
                  when=WHEN + timedelta(days=40))
        r = resolve(a, b)
        self.assertIs(Verdict.SAME, r.verdict)
        self.assertEqual("bytes", r.resolver)


class EveryAnswerCarriesEvidence(unittest.TestCase):

    def test_a_resolution_cannot_be_built_without_evidence(self):
        with self.assertRaises(ValueError):
            resolver.Resolution(Verdict.SAME, Relation.SAME_INSTANCE, 0.9, "test", [])

    def test_every_branch_explains_itself(self):
        pairs = [
            (asset("a1", text="PASSPORT NO: 111111"), asset("a2", text="PASSPORT NO: 222222")),
            (asset("b1", labels=["chair"]), asset("b2", labels=["chair"],
                                                  when=WHEN + timedelta(days=2))),
            (asset("c1", dhash=0), asset("c2", dhash=0, content_hash="other")),
            (asset("d1"), asset("d2", dhash=0xFFFF_FFFF_FFFF_FFFF)),
        ]
        for a, b in pairs:
            r = decide(a, b)
            self.assertTrue(r.why().strip(), f"{r.resolver} explained nothing")


class TheGateForbidsAUniversalModel(unittest.TestCase):
    """§24 Gate 2: 禁止寻找一个万能 Same-Entity 模型."""

    def test_different_categories_use_different_resolvers(self):
        used = set()
        cases = [
            (asset("x1", text="PASSPORT NO: 111111"),
             asset("x2", text="PASSPORT NO: 222222", dhash=0x1234_5678_9ABC_DEF1)),
            (asset("y1", text="ORDER NO: A1-1 THING", screenshot=True),
             asset("y2", text="ORDER NO: B2-2 OTHER", screenshot=True,
                   dhash=0x1234_5678_9ABC_DEF1)),
            (asset("z1", labels=["chair"]),
             asset("z2", labels=["chair"], when=WHEN + timedelta(days=2))),
            (asset("w1", dhash=0xC0FF_EE00_C0FF_EE00),
             asset("w2", dhash=0xFFFF_0000_FFFF_0000)),
        ]
        for a, b in cases:
            used.add(decide(a, b).resolver.split(".")[0])
        self.assertGreaterEqual(len(used), 4,
                                f"one ladder answered every category: {used}")

    def test_the_breadth_pass_may_not_name_a_relation_it_cannot_know(self):
        """Before classification there is no category, so there is no resolver — and
        the pass must protect both assets rather than guess which relation applies."""
        a = asset("q1", text="IDENTITY CARD NAME: JANE DOE", dhash=0x1122_3344_5566_7788)
        b = asset("q2", text="IDENTITY CARD NAME: JANE DOE", dhash=0x1122_3344_5566_7789,
                  when=WHEN + timedelta(days=180))
        report = dedup.analyse([a, b])
        self.assertTrue(report.relations)
        for group in report.relations:
            self.assertEqual(sorted(group.members), sorted(group.distinct_members))
            self.assertEqual("looks_alike", group.kind)


class UndecidedGoesToReviewAndNeverToAMerge(unittest.TestCase):
    """低置信度只能进入 Review Queue，不自动合并/删除."""

    def test_an_uncertain_pair_reaches_the_review_list_and_stays_distinct(self):
        a = asset("r1", labels=["chair"], dhash=0x0F0F_0F0F_0F0F_0F0F)
        b = asset("r2", labels=["chair"], dhash=0x0F0F_0F0F_0F0F_0F0E,
                  when=WHEN + timedelta(days=2))
        ctx = build_context([a, b])
        clf = Classifier(ctx)
        cs = {x.asset_id: clf.classify(x) for x in (a, b)}
        report = dedup.analyse([a, b], classifications=cs)

        self.assertEqual(1, len(report.needs_entity_review))
        self.assertTrue(report.needs_entity_review[0][2].strip())
        for group in report.relations:
            self.assertEqual(sorted(group.members), sorted(group.distinct_members),
                             "undecided is not permission to fold")


if __name__ == "__main__":
    unittest.main(verbosity=2)
