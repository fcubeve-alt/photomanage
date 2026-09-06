# -*- coding: utf-8 -*-
"""
Behavioural tests for the classification engine.

These are not accuracy tests — accuracy is measured against the labelled library by
`eval/evaluate.py`. These lock down the behaviours that must hold for every library,
including the ones no corpus happens to contain, and the safety red lines that must
hold even when the classifier is wrong.

    python -m unittest discover -s tests -v
"""

import os
import sys
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pvm import dedup, taxonomy                                        # noqa: E402
from pvm.classifier import Classifier, SETTLE_AT                       # noqa: E402
from pvm.context import LibraryContext, build_context                  # noqa: E402
from pvm.risk import (Action, Proposal, Risk, classify_risk, propose)  # noqa: E402
from pvm.signals import (AssetSignals, FaceCluster, GeoFix, PlaceName,  # noqa: E402
                         SceneLabel, Tier)
from pvm.verdict import Assignment, Evidence                            # noqa: E402

LONDON = GeoFix(51.5074, -0.1278)
TOKYO = GeoFix(35.6762, 139.6503)
UK_LONDON = PlaceName("United Kingdom", "London", 0.9)
JP_TOKYO = PlaceName("Japan", "Tokyo", 0.9)
WHEN = datetime(2025, 6, 18, 14, 3)


def asset(aid="a", **kw) -> AssetSignals:
    kw.setdefault("created_at", WHEN)
    return AssetSignals(aid, **kw)


def classify(a, ctx=None, budget=Tier.TEXT):
    return Classifier(ctx or LibraryContext(), budget=budget).classify(a)


class TaxonomyGuards(unittest.TestCase):
    def test_a_rule_cannot_invent_a_category(self):
        with self.assertRaises(taxonomy.InvalidPath):
            taxonomy.ensure_node("Documents > Crypto")

    def test_data_derived_branches_may_grow(self):
        self.assertEqual(taxonomy.ensure_node("People > Zoe"), "People > Zoe")
        self.assertEqual(taxonomy.ensure_node("Places > France > Paris"),
                         "Places > France > Paris")

    def test_cross_listing_comes_from_the_tree_not_the_rules(self):
        self.assertEqual(taxonomy.cross_listing("Purchases > Receipts"), "Documents > Receipts")


class EveryAssignmentExplainsItself(unittest.TestCase):
    """The Constitution's safety red line, enforced at construction."""

    def test_assignment_without_evidence_cannot_exist(self):
        with self.assertRaises(ValueError):
            Assignment("Documents", [])

    def test_evidence_without_a_reason_cannot_exist(self):
        with self.assertRaises(ValueError):
            Evidence("ocr_text", Tier.TEXT, 0.9, "   ")

    def test_no_amount_of_evidence_reaches_certainty(self):
        strong = [Evidence("s", Tier.METADATA, 0.99, "r") for _ in range(20)]
        self.assertLess(Assignment("Documents", strong).confidence, 1.0)

    def test_every_classified_path_carries_a_reason(self):
        c = classify(asset(is_screenshot=True, ocr_ran=True,
                           ocr_text="VERIFICATION CODE 115838"))
        for path, why in c.explain().items():
            self.assertTrue(why.strip(), f"{path} was filed with no explanation")


class Cascade(unittest.TestCase):
    def test_a_screenshot_with_no_readable_text_stops_at_the_root(self):
        """The subtype proves it is a screenshot and nothing proves which kind.
        Guessing `Screenshots > Chat` here would be a confident lie."""
        c = classify(asset(is_screenshot=True, ocr_ran=True, ocr_text="SCREENSHOT"))
        self.assertEqual(c.primary.path, "Screenshots")
        self.assertNotIn("Screenshots > Chat", c.paths)

    def test_text_deepens_a_screenshot_and_the_parent_is_not_counted_twice(self):
        c = classify(asset(is_screenshot=True, ocr_ran=True,
                           ocr_text="PICKUP CODE 4417 — LOCKER B12"))
        self.assertIn("Screenshots > Temporary > Pickup Codes", c.paths)
        self.assertNotIn("Screenshots", c.paths)

    def test_the_parents_reason_survives_into_the_leaf(self):
        c = classify(asset(is_screenshot=True, ocr_ran=True, ocr_text="VERIFICATION CODE 9"))
        why = c.explain()["Screenshots > Temporary > Verification Codes"]
        self.assertIn("screenshot", why)
        self.assertIn("verification code", why)

    def test_an_ambiguous_document_stops_at_the_branch_it_can_prove(self):
        """"CONTRACT — PAGE 1 OF 4" says it is a contract and not what kind. Stopping
        at `Documents > Contracts` is the right answer, not a failure to reach a leaf."""
        c = classify(asset(ocr_ran=True, ocr_text="CONTRACT — PAGE 1 OF 4"))
        self.assertEqual(c.primary.path, "Documents > Contracts")

    def test_receipts_are_cross_listed_once_not_copied(self):
        c = classify(asset(ocr_ran=True, ocr_text="RECEIPT — HEADPHONES £129.00"))
        self.assertIn("Purchases > Receipts", c.paths)
        self.assertIn("Documents > Receipts", c.paths)
        self.assertEqual(len(c.paths), len(set(c.paths)))

    def test_every_asset_reaches_the_timeline(self):
        self.assertIn("Timeline > 2025", classify(asset()).paths)

    def test_an_asset_with_no_date_says_so_instead_of_guessing_one(self):
        c = classify(asset(created_at=None))
        self.assertFalse(any(p.startswith("Timeline") for p in c.paths))
        self.assertTrue(any("timeline" in n for n in c.notes))

    def test_video_is_reported_as_having_nowhere_to_go(self):
        """The canonical tree has eleven roots and none is Video (FC-2). Filing video
        as a photo would hide that; saying so surfaces it."""
        c = classify(asset(media_type="video"))
        self.assertTrue(any("video" in n for n in c.notes))


class LocationIsContextNotIdentity(unittest.TestCase):
    """The regression that cost nine of nine foreground documents.

    `_places` used to run before the text tier. A GPS fix filed a photographed passport
    as `Places > United Kingdom > London` at 0.91, the escalation policy saw a settled
    leaf, and the OCR pass that would have recognised it never ran. The failure was
    silent and the wrong answer was plausible, which is the worst combination."""

    def test_a_document_photographed_at_home_is_still_a_document(self):
        c = classify(asset(geo=LONDON, place=UK_LONDON, ocr_ran=True, ocr_text="PASSPORT"))
        self.assertEqual(c.primary.path, "Documents > Identity > Passports")

    def test_paperwork_does_not_appear_under_places(self):
        c = classify(asset(geo=LONDON, place=UK_LONDON, ocr_ran=True, ocr_text="PASSPORT"))
        self.assertFalse([p for p in c.paths if p.startswith("Places")],
                         "a passport was filed on the Places shelf next to the holiday photos")

    def test_an_ordinary_photo_with_a_fix_still_gets_its_place(self):
        c = classify(asset(geo=TOKYO, place=JP_TOKYO))
        self.assertEqual(c.primary.path, "Places > Japan > Tokyo")

    def test_an_inferred_fix_is_not_treated_as_a_measured_one(self):
        c = classify(asset(geo=GeoFix(51.5, -0.1, source="inferred"), place=UK_LONDON))
        self.assertFalse([p for p in c.paths if p.startswith("Places")])


class People(unittest.TestCase):
    def test_a_named_cluster_files_the_person(self):
        c = classify(asset(face_clusters=[FaceCluster("c1", "Anna", 0.3)]))
        self.assertEqual(c.primary.path, "People > Anna")

    def test_two_people_become_a_group(self):
        c = classify(asset(face_clusters=[FaceCluster("c1", "Anna"), FaceCluster("c2", "Ben")]))
        self.assertEqual(c.primary.path, "People > Groups")

    def test_an_unnamed_face_still_changes_the_risk(self):
        c = classify(asset(face_clusters=[FaceCluster("c9", None, 0.4)]))
        self.assertTrue(any("unnamed person" in n for n in c.notes))
        self.assertEqual(classify_risk(c, has_unnamed_person=True), Risk.R4_PEOPLE)


class Cost(unittest.TestCase):
    def test_a_cheap_answer_does_not_pay_for_expensive_signals(self):
        c = classify(asset(is_screenshot=True, ocr_ran=True, ocr_text="SCREENSHOT"))
        self.assertNotIn(Tier.FACES, c.tiers_spent,
                         "face clustering was run on a screenshot")
        self.assertNotIn(Tier.VISUAL, c.tiers_spent)

    def test_spent_and_used_are_reported_separately(self):
        """A photo answered by its GPS fix still cost a face pass if one ran. Reporting
        only `tier_used` would make the engine look cheaper than it is."""
        c = classify(asset(geo=TOKYO, place=JP_TOKYO))
        self.assertEqual(c.tier_used, Tier.METADATA)
        self.assertIn(Tier.FACES, c.tiers_spent)

    def test_a_metadata_budget_never_reads_text(self):
        c = classify(asset(ocr_ran=True, ocr_text="PASSPORT"), budget=Tier.METADATA)
        self.assertNotIn("Documents > Identity > Passports", c.paths)


class Context(unittest.TestCase):
    def _library(self):
        home = [asset(f"h{i}", created_at=datetime(2024, 1, 1, 21) + timedelta(days=i),
                      geo=LONDON, place=UK_LONDON) for i in range(200)]
        trip = [asset(f"t{i}", created_at=datetime(2025, 4, 12, 10) + timedelta(hours=i * 3),
                      geo=TOKYO, place=JP_TOKYO) for i in range(40)]
        return home, trip

    def test_home_is_learned_and_never_asked_for(self):
        home, trip = self._library()
        ctx = build_context(home + trip)
        self.assertEqual(ctx.home_city, "London")
        self.assertGreater(ctx.home_confidence, 0.5)

    def test_home_is_measured_in_days_not_in_captures(self):
        """One weekend of 500 beach photos must not outvote two years of living
        somewhere. Counting captures is how it does."""
        home = [asset(f"h{i}", created_at=datetime(2024, 1, 1, 21) + timedelta(days=i),
                      geo=LONDON, place=UK_LONDON) for i in range(200)]
        beach = [asset(f"b{i}", created_at=datetime(2024, 7, 6, 12) + timedelta(minutes=i),
                       geo=GeoFix(50.8225, -0.1372),
                       place=PlaceName("United Kingdom", "Brighton", 0.9)) for i in range(500)]
        self.assertEqual(build_context(home + beach).home_city, "London")

    def test_a_run_of_days_away_becomes_a_trip(self):
        home, trip = self._library()
        ctx = build_context(home + trip)
        self.assertEqual([t.label for t in ctx.trips], ["Tokyo · Apr 2025"])

    def test_two_photos_on_a_day_out_are_not_a_trip(self):
        home, _ = self._library()
        blip = [asset("x1", created_at=datetime(2025, 4, 12, 10), geo=TOKYO, place=JP_TOKYO),
                asset("x2", created_at=datetime(2025, 4, 13, 10), geo=TOKYO, place=JP_TOKYO)]
        self.assertEqual(build_context(home + blip).trips, [])

    def test_a_trip_photo_is_filed_under_both_the_trip_and_the_place(self):
        home, trip = self._library()
        ctx = build_context(home + trip)
        c = classify(trip[0], ctx)
        self.assertIn("Travel > Tokyo · Apr 2025", c.paths)
        self.assertIn("Places > Japan > Tokyo", c.paths)


class RiskRedLines(unittest.TestCase):
    def test_there_is_no_delete_action_at_all(self):
        self.assertNotIn("DELETE", {a.name for a in Action})

    def test_an_identity_document_can_never_be_proposed_for_removal(self):
        with self.assertRaises(ValueError):
            Proposal("x", Action.PROPOSE_REMOVE, Risk.R5_CRITICAL_DOCUMENT,
                     [Evidence("ocr_text", Tier.TEXT, 0.9, "passport")])

    def test_a_person_can_never_be_proposed_for_removal(self):
        with self.assertRaises(ValueError):
            Proposal("x", Action.PROPOSE_REMOVE, Risk.R4_PEOPLE,
                     [Evidence("faces", Tier.FACES, 0.9, "Anna")])

    def test_an_irreversible_removal_cannot_be_constructed(self):
        with self.assertRaises(ValueError):
            Proposal("x", Action.PROPOSE_REMOVE, Risk.R0_EXACT_DUPLICATE,
                     [Evidence("hash", Tier.HASH, 0.99, "identical")], reversible=False)

    def test_a_proposal_without_evidence_cannot_be_constructed(self):
        with self.assertRaises(ValueError):
            Proposal("x", Action.KEEP, Risk.R3_ORDINARY, [])

    def test_a_duplicate_passport_is_still_a_passport(self):
        """Escalations are checked before de-escalations, or the cheapest fact about an
        asset would decide what happens to the most expensive one."""
        c = classify(asset(ocr_ran=True, ocr_text="PASSPORT"))
        self.assertEqual(classify_risk(c, is_exact_duplicate=True), Risk.R5_CRITICAL_DOCUMENT)

    def test_only_an_exact_byte_duplicate_may_be_applied_without_asking(self):
        c = classify(asset(is_screenshot=True, ocr_ran=True, ocr_text="SCREENSHOT"))
        for risk in Risk:
            if risk in (Risk.R4_PEOPLE, Risk.R5_CRITICAL_DOCUMENT):
                continue
            p = propose(c, risk, duplicate_of="other")
            if p.auto_applicable:
                self.assertEqual(risk, Risk.R0_EXACT_DUPLICATE)

    def test_an_asset_the_engine_does_not_understand_is_protected_not_discarded(self):
        c = classify(asset())
        self.assertEqual(classify_risk(c), Risk.R6_UNKNOWN)
        self.assertEqual(propose(c, Risk.R6_UNKNOWN).action, Action.REVIEW)

    def test_a_medical_document_is_filed_without_any_claim_about_the_person(self):
        """§16: the category holds documents. It never characterises the human."""
        c = classify(asset(ocr_ran=True, ocr_text="PRESCRIPTION — COLLECT AT PHARMACY"))
        self.assertEqual(c.primary.path, "Documents > Medical")
        self.assertEqual(classify_risk(c), Risk.R5_CRITICAL_DOCUMENT)
        why = c.explain()["Documents > Medical"].lower()
        self.assertIn("nothing about your health", why)


class DuplicatesAndTheThingsThatOnlyLookLikeThem(unittest.TestCase):
    def test_exact_duplicates_keep_the_earliest_and_flag_the_rest(self):
        a = asset("orig", content_hash="h", dhash=0xABCD)
        b = asset("copy", created_at=WHEN + timedelta(days=30), content_hash="h", dhash=0xABCD)
        r = dedup.analyse([a, b])
        self.assertEqual(r.exact_duplicate_of, {"copy": "orig"})

    def test_the_same_card_photographed_months_later_is_not_a_duplicate(self):
        """§9 Same Entity. One object, two occasions; deleting either loses a record."""
        a = asset("id1", content_hash="h1", dhash=0x1122334455667788, ocr_text="ID CARD")
        b = asset("id2", created_at=WHEN + timedelta(days=180),
                  content_hash="h2", dhash=0x1122334455667789, ocr_text="ID CARD")
        r = dedup.analyse([a, b])
        self.assertEqual(r.exact_duplicate_of, {})
        kinds = {g.kind for g in r.relations}
        self.assertIn("same_entity", kinds)

    def test_two_contract_pages_that_look_alike_are_never_merged(self):
        """The Document-class False Merge — the make-or-break number for Tier 1."""
        a = asset("c1", content_hash="h1", dhash=0x99AABBCCDDEEFF00,
                  ocr_text="CONTRACT — PAGE 1 OF 4")
        b = asset("c2", created_at=WHEN + timedelta(minutes=1), content_hash="h2",
                  dhash=0x99AABBCCDDEEFF01, ocr_text="CONTRACT — PAGE 2 OF 4")
        r = dedup.analyse([a, b], document_ids={"c1", "c2"})
        self.assertEqual(r.exact_duplicate_of, {})
        group = [g for g in r.relations if set(g.members) == {"c1", "c2"}][0]
        self.assertEqual(sorted(group.distinct_members), ["c1", "c2"])
        self.assertIn("text differs", group.reason)

    def test_the_one_frame_that_differs_survives_the_burst(self):
        """§8: frame 5 is the one everybody's eyes are open in. It is why the burst
        was taken, and it is the frame a naive collapse deletes."""
        frames = [asset(f"b{i}", created_at=WHEN + timedelta(seconds=i), burst_id="B",
                        content_hash=f"h{i}", dhash=0xF0F0F0F0F0F0F0F0 | i) for i in range(4)]
        frames.append(asset("b4", created_at=WHEN + timedelta(seconds=4), burst_id="B",
                            content_hash="h4", dhash=0x0F0F0F0F0F0F0F0F))
        r = dedup.analyse(frames)
        self.assertIn("b4", r.protected_distinct)
        self.assertNotIn("b4", r.near_duplicate_in_moment)

    def test_a_hash_of_zero_is_a_failure_and_never_a_match(self):
        """FC-1a: dHash returns 0 for a whole class of ordinary images AND for every
        failure. Treating it as a value links unrelated photos as duplicates."""
        a = asset("flat1", content_hash="h1", dhash=0)
        b = asset("flat2", content_hash="h2", dhash=0)
        r = dedup.analyse([a, b])
        self.assertEqual(r.relations, [])
        self.assertEqual(r.unusable_hash, {"flat1", "flat2"})

    def test_an_unhashable_frame_in_a_burst_counts_as_distinct(self):
        frames = [asset("g0", burst_id="B", content_hash="h0", dhash=0xAAAA),
                  asset("g1", created_at=WHEN + timedelta(seconds=1), burst_id="B",
                        content_hash="h1", dhash=0xAAAB),
                  asset("g2", created_at=WHEN + timedelta(seconds=2), burst_id="B",
                        content_hash="h2", dhash=0)]
        r = dedup.analyse(frames)
        self.assertIn("g2", r.protected_distinct)


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TransientAssetsExpireBeforeTheyAreTidied(unittest.TestCase):
    """A verification code screenshot taken this morning is the most useful photo in
    the library. The same screenshot in two months is clutter. The risk class is the
    same on both days; what changes is whether acting on it is safe."""

    def _otp(self):
        return classify(asset(is_screenshot=True, ocr_ran=True,
                              ocr_text="VERIFICATION CODE 115838"))

    def test_a_fresh_code_is_kept(self):
        p = propose(self._otp(), Risk.R2_TRANSIENT, age_days=1)
        self.assertEqual(p.action, Action.KEEP)
        self.assertIn("still recent", p.note)

    def test_an_expired_code_is_offered_for_archiving(self):
        p = propose(self._otp(), Risk.R2_TRANSIENT, age_days=120)
        self.assertEqual(p.action, Action.PROPOSE_ARCHIVE)

    def test_archiving_a_code_still_requires_confirmation_and_stays_reversible(self):
        p = propose(self._otp(), Risk.R2_TRANSIENT, age_days=120)
        self.assertTrue(p.requires_confirmation)
        self.assertTrue(p.reversible)
        self.assertFalse(p.auto_applicable)

    def test_an_unknown_age_is_not_an_old_age(self):
        """Absent evidence must never read as evidence for acting."""
        p = propose(self._otp(), Risk.R2_TRANSIENT, age_days=None)
        self.assertEqual(p.action, Action.KEEP)
