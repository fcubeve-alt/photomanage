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
from pvm.risk import (ACTING_ACTIONS, Action, Factors, Lifecycle,      # noqa: E402
                      NEVER_DELETE_AT_OR_ABOVE, Proposal, Recoverability, Risk,
                      classify_risk, decide_action, lifecycle_of, propose,
                      recoverability_of)
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
        self.assertEqual(classify_risk(c, has_person=True), Risk.R3_PERSONAL)


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


class TheRiskScaleIsTheConstitutionsNotMine(unittest.TestCase):
    """The audit's worst finding. The previous version used R0–R6 — the same
    identifiers §6 and Tier 2-A define — with meanings I had invented. R6 meant "not
    understood" where the Constitution means "irreplaceable, highest protection";
    receipts sat a level below §6's placement and people a level above. Every row of
    the catalogue read wrong against the document that defines it.

    These tests pin the scale to §6 so it cannot drift again."""

    EXPECTED = [
        (Risk.R0_DISPOSABLE, "几乎无长期价值", "激进自动处理"),
        (Risk.R1_LOW_VALUE, "通常短期/低价值", "自动处理或批量处理"),
        (Risk.R2_NORMAL, "普通生活内容", "按相似度/生命周期处理"),
        (Risk.R3_PERSONAL, "具有个人意义", "保守精选"),
        (Risk.R4_IMPORTANT, "可能承担交易/工作价值", "Protect/Archive 优先"),
        (Risk.R5_CRITICAL, "法律/身份/金融价值", "默认 Protect"),
        (Risk.R6_IRREPLACEABLE, "可能不可替代", "最高保护"),
    ]

    def test_the_scale_matches_section_6_exactly(self):
        self.assertEqual(len(Risk), len(self.EXPECTED))
        for level, meaning, policy in self.EXPECTED:
            self.assertEqual(level.meaning, meaning)
            self.assertEqual(level.default_policy, policy)

    def test_r6_is_the_top_of_the_scale_not_a_place_for_confusion(self):
        self.assertEqual(max(Risk), Risk.R6_IRREPLACEABLE)
        self.assertNotIn("UNKNOWN", {r.name for r in Risk})

    def test_an_unplaced_asset_does_not_get_a_risk_level_of_its_own(self):
        """§5 keeps consequence and confidence on separate axes. An asset we cannot
        file is a confidence problem; giving it its own rung let it outrank a passport."""
        c = classify(asset())
        self.assertEqual(classify_risk(c), Risk.R2_NORMAL)
        self.assertEqual(decide_action(Factors(Risk.R2_NORMAL, Lifecycle.ACTIVE, 0.2,
                                               Recoverability.RECOVERABLE)), Action.REVIEW)

    def test_receipts_are_important_and_people_are_personal(self):
        """The two placements the old code had inverted, straight from §6's examples."""
        receipt = classify(asset(ocr_ran=True, ocr_text="RECEIPT — HEADPHONES £129.00"))
        self.assertEqual(classify_risk(receipt), Risk.R4_IMPORTANT)
        person = classify(asset(face_clusters=[FaceCluster("c", "Anna")]))
        self.assertEqual(classify_risk(person), Risk.R3_PERSONAL)

    def test_identity_documents_are_critical(self):
        c = classify(asset(ocr_ran=True, ocr_text="PASSPORT"))
        self.assertEqual(classify_risk(c), Risk.R5_CRITICAL)

    def test_a_duplicate_passport_is_still_a_passport(self):
        """Escalations before de-escalations, or the cheapest fact about an asset would
        decide what happens to the most expensive one."""
        c = classify(asset(ocr_ran=True, ocr_text="PASSPORT"))
        self.assertEqual(classify_risk(c, is_exact_duplicate=True), Risk.R5_CRITICAL)

    def test_a_byte_identical_copy_of_something_ordinary_is_disposable(self):
        c = classify(asset(is_screenshot=True, ocr_ran=True, ocr_text="SCREENSHOT"))
        self.assertEqual(classify_risk(c, is_exact_duplicate=True), Risk.R0_DISPOSABLE)


class ThePolicyTable(unittest.TestCase):
    """§5: Category × Importance × Lifecycle × Confidence × Recoverability × Personal
    Preference → Action Policy. Tier 2-A requires it as a table and sets the PASS bar:
    R4–R6 zero automated deletion, R0–R1 largely automatic."""

    def test_no_risk_level_at_or_above_r4_is_ever_acted_on(self):
        for risk in (Risk.R4_IMPORTANT, Risk.R5_CRITICAL, Risk.R6_IRREPLACEABLE):
            for lc in Lifecycle:
                for conf in (0.1, 0.6, 0.99):
                    action = decide_action(Factors(risk, lc, conf, recoverability_of(risk),
                                                   in_equivalence_group=True,
                                                   is_exact_duplicate=True))
                    self.assertNotIn(action, ACTING_ACTIONS,
                                     f"{risk.name}/{lc.value} produced {action.value}")

    def test_r0_and_r1_can_actually_be_automated(self):
        """§7: the automation benefit must not be surrendered to a tiny probability of
        error. A policy that never acts is as much a failure as one that acts wrongly."""
        self.assertEqual(
            decide_action(Factors(Risk.R0_DISPOSABLE, Lifecycle.ACTIVE, 0.9,
                                  Recoverability.RECOVERABLE, is_exact_duplicate=True)),
            Action.AUTO_CLEAN)
        self.assertEqual(
            decide_action(Factors(Risk.R1_LOW_VALUE, Lifecycle.EXPIRED, 0.9,
                                  Recoverability.RECOVERABLE)),
            Action.SUGGEST_DELETE)

    def test_low_confidence_routes_to_review_rather_than_to_action(self):
        """With one deliberate exception, below. `confidence` is confidence in the
        *classification*, and acting on a guess about what a picture is, is what this
        gate prevents."""
        for risk in (Risk.R1_LOW_VALUE, Risk.R2_NORMAL, Risk.R3_PERSONAL):
            self.assertEqual(
                decide_action(Factors(risk, Lifecycle.EXPIRED, 0.2,
                                      Recoverability.RECOVERABLE, is_exact_duplicate=True)),
                Action.REVIEW,
                f"{risk.name} was acted on at 0.2 confidence")

    def test_the_one_exception_is_byte_identity_which_is_not_a_guess(self):
        """See ByteIdentityIsNotAClassificationGuess: a content hash is certain whether
        or not the classifier worked out what the picture is of."""
        self.assertEqual(
            decide_action(Factors(Risk.R0_DISPOSABLE, Lifecycle.ACTIVE, 0.0,
                                  Recoverability.RECOVERABLE, is_exact_duplicate=True)),
            Action.AUTO_CLEAN)

    def test_personal_preference_can_only_make_the_system_more_careful(self):
        """§14 lets the user's corrections outrank the default. Letting them loosen a
        protection would turn a red line into a setting."""
        f = Factors(Risk.R0_DISPOSABLE, Lifecycle.EXPIRED, 0.99, Recoverability.RECOVERABLE,
                    is_exact_duplicate=True, personal_preference=Action.PROTECT)
        self.assertEqual(decide_action(f), Action.PROTECT)
        loosened = Factors(Risk.R5_CRITICAL, Lifecycle.ACTIVE, 0.99,
                           Recoverability.HARD_TO_REPLACE,
                           personal_preference=Action.AUTO_CLEAN)
        self.assertEqual(decide_action(loosened), Action.PROTECT)

    def test_an_equivalence_group_is_where_select_best_applies(self):
        """§8: Same Moment + Same Subject + High Similarity + Low Risk → 选代表照."""
        self.assertEqual(
            decide_action(Factors(Risk.R2_NORMAL, Lifecycle.ACTIVE, 0.9,
                                  Recoverability.RECOVERABLE, in_equivalence_group=True)),
            Action.SELECT_BEST)


class RiskRedLines(unittest.TestCase):
    def test_there_is_no_permanent_delete_action(self):
        self.assertNotIn("DELETE", {a.name for a in Action})

    def test_an_important_asset_can_never_be_proposed_for_deletion(self):
        for risk in (Risk.R4_IMPORTANT, Risk.R5_CRITICAL, Risk.R6_IRREPLACEABLE):
            with self.assertRaises(ValueError):
                Proposal("x", Action.SUGGEST_DELETE,
                         Factors(risk, Lifecycle.EXPIRED, 0.9, recoverability_of(risk)),
                         [Evidence("ocr_text", Tier.TEXT, 0.9, "passport")])

    def test_an_irreplaceable_asset_may_not_be_acted_on_at_all(self):
        for action in ACTING_ACTIONS:
            with self.assertRaises(ValueError):
                Proposal("x", action,
                         Factors(Risk.R0_DISPOSABLE, Lifecycle.EXPIRED, 0.9,
                                 Recoverability.IRREPLACEABLE),
                         [Evidence("s", Tier.METADATA, 0.9, "r")])

    def test_auto_clean_is_r0_and_recoverable_only(self):
        with self.assertRaises(ValueError):
            Proposal("x", Action.AUTO_CLEAN,
                     Factors(Risk.R2_NORMAL, Lifecycle.ACTIVE, 0.9, Recoverability.RECOVERABLE),
                     [Evidence("s", Tier.METADATA, 0.9, "r")])
        with self.assertRaises(ValueError):
            Proposal("x", Action.AUTO_CLEAN,
                     Factors(Risk.R0_DISPOSABLE, Lifecycle.ACTIVE, 0.9,
                             Recoverability.HARD_TO_REPLACE),
                     [Evidence("s", Tier.METADATA, 0.9, "r")])

    def test_a_proposal_without_evidence_cannot_be_constructed(self):
        with self.assertRaises(ValueError):
            Proposal("x", Action.KEEP,
                     Factors(Risk.R2_NORMAL, Lifecycle.ACTIVE, 0.9, Recoverability.RECOVERABLE),
                     [])

    def test_only_an_exact_byte_duplicate_may_be_applied_without_asking(self):
        c = classify(asset(is_screenshot=True, ocr_ran=True, ocr_text="SCREENSHOT"))
        applied = []
        for risk in Risk:
            f = Factors(risk, Lifecycle.EXPIRED, 0.95, recoverability_of(risk),
                        is_exact_duplicate=True)
            p = propose(c, f, duplicate_of="other")
            if p.auto_applicable:
                applied.append(risk)
        self.assertEqual(applied, [Risk.R0_DISPOSABLE])

    def test_a_medical_document_is_filed_without_any_claim_about_the_person(self):
        """§16: the category holds documents. It never characterises the human."""
        c = classify(asset(ocr_ran=True, ocr_text="PRESCRIPTION — COLLECT AT PHARMACY"))
        self.assertEqual(c.primary.path, "Documents > Medical")
        self.assertEqual(classify_risk(c), Risk.R5_CRITICAL)
        self.assertIn("nothing about your health", c.explain()["Documents > Medical"].lower())


class LifecycleIsWhenNotHowMuch(unittest.TestCase):
    """§3 lists Lifecycle as its own index dimension: Temporary / Active / Expired /
    Long-term. A verification code screenshotted an hour ago is the most useful photo
    in the library; the same one in two months is clutter. The risk level is identical
    on both days — only the lifecycle moved."""

    def _otp(self):
        return classify(asset(is_screenshot=True, ocr_ran=True,
                              ocr_text="VERIFICATION CODE 115838"))

    def test_a_fresh_code_is_temporary_and_kept(self):
        c = self._otp()
        self.assertEqual(lifecycle_of(c, age_days=1), Lifecycle.TEMPORARY)
        f = Factors(Risk.R1_LOW_VALUE, Lifecycle.TEMPORARY, 0.9, Recoverability.RECOVERABLE)
        self.assertEqual(decide_action(f), Action.KEEP)

    def test_an_old_code_has_expired_and_is_offered_for_removal(self):
        c = self._otp()
        self.assertEqual(lifecycle_of(c, age_days=120), Lifecycle.EXPIRED)
        f = Factors(Risk.R1_LOW_VALUE, Lifecycle.EXPIRED, 0.9, Recoverability.RECOVERABLE)
        self.assertEqual(decide_action(f), Action.SUGGEST_DELETE)

    def test_an_unknown_age_is_not_an_old_age(self):
        self.assertEqual(lifecycle_of(self._otp(), age_days=None), Lifecycle.TEMPORARY)

    def test_documents_and_people_are_long_term(self):
        self.assertEqual(lifecycle_of(classify(asset(ocr_ran=True, ocr_text="PASSPORT")), 900),
                         Lifecycle.LONG_TERM)


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


class ByteIdentityIsNotAClassificationGuess(unittest.TestCase):
    """§6 R0 是 完全重复下载、重复 Meme · 激进自动处理.

    The confidence gate protects against acting on a guess about *what a picture is*.
    An exact duplicate is not a guess: the evidence is a content hash. Running the two
    together sent every unidentifiable re-download to Review, so the single thing the
    system can genuinely automate became the thing it refused to do — which is the
    trade §7 exists to forbid."""

    def test_an_unidentifiable_exact_duplicate_is_still_auto_cleanable(self):
        c = classify(asset())                       # nothing places it: confidence 0
        self.assertIsNone(c.primary)
        risk = classify_risk(c, is_exact_duplicate=True)
        self.assertEqual(risk, Risk.R0_DISPOSABLE)
        action = decide_action(Factors(risk, Lifecycle.ACTIVE, 0.0,
                                       Recoverability.RECOVERABLE, is_exact_duplicate=True))
        self.assertEqual(action, Action.AUTO_CLEAN)

    def test_but_a_low_confidence_non_duplicate_still_goes_to_review(self):
        action = decide_action(Factors(Risk.R2_NORMAL, Lifecycle.ACTIVE, 0.1,
                                       Recoverability.RECOVERABLE))
        self.assertEqual(action, Action.REVIEW)

    def test_and_byte_identity_never_overrides_an_escalation(self):
        c = classify(asset(ocr_ran=True, ocr_text="PASSPORT"))
        self.assertEqual(classify_risk(c, is_exact_duplicate=True), Risk.R5_CRITICAL)
