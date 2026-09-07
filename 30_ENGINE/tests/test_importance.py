# -*- coding: utf-8 -*-
"""
§4 精细 Visual Asset Taxonomy and §5's Importance factor.

The test that matters most here is `TwoReadingsOfOneDocument`: §4 states a 默认风险
per class and §6 states a risk scale, and `pvm/risk.py` was built from §6 while
`pvm/importance.py` was built from §4. They are two readings of two sections of one
document, made months apart, and if they disagree about where a receipt sits then one
of them is a misreading of the Constitution rather than a bug in a function.
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pvm.importance import (ASSET_CLASSES, BY_KEY, BURST_SIZE, DEFAULT_CLASS,
                            Assessment, ImportanceSignals, RECURRING_PERSON,
                            assess, class_table, classify_asset_class)
from pvm.risk import (Action, Factors, Importance, Lifecycle, Proposal,
                      NEVER_DELETE_AT_OR_ABOVE_IMPORTANCE,
                      NEVER_PRUNE_AT_OR_ABOVE_IMPORTANCE,
                      Recoverability, Risk, classify_risk, decide_action,
                      equivalence_table, recoverability_of)
from pvm.verdict import Assignment, Classification, Evidence
from pvm.signals import Tier


def _classification(*paths, asset_id="a1"):
    assignments = [
        Assignment(path=p, is_primary=(i == 0),
                   evidence=[Evidence("test", Tier.METADATA, 1.0, "fixture")])
        for i, p in enumerate(paths)]
    return Classification(asset_id=asset_id, assignments=assignments,
                          tier_used=Tier.METADATA, tiers_spent={Tier.METADATA})


class TwoReadingsOfOneDocument(unittest.TestCase):
    """§4's 默认风险 column against §6's scale, for the same tree branches."""

    def test_every_node_in_the_tree_agrees_with_section_six(self):
        """Every path in the canonical tree, not only the prefixes this file names.

        The first version of this test walked `cls.prefixes`, which means it checked
        the mapping against itself — a branch I had forgotten to map could not fail a
        loop over the branches I had mapped. Sweeping the tree is what turns it into a
        check on the reading rather than on my bookkeeping, and it immediately found
        `Documents > Other Documents` filed as a legal instrument.
        """
        from pvm import taxonomy
        checked = 0
        for path in taxonomy.ALL_PATHS:
            if taxonomy.root_of(path) == "Timeline":
                continue    # an index every asset is on, not a class of content
            cls = classify_asset_class([path])
            risk = classify_risk(_classification(path))
            lo, hi = cls.default_risk
            checked += 1
            self.assertTrue(
                lo <= risk <= hi,
                f"§4 puts {cls.name} ({path}) at {lo.name}–{hi.name}; §6 as "
                f"implemented in risk.py says {risk.name}. One of the two readings "
                f"of the Constitution is wrong, and it is not a rounding error.")
        self.assertGreater(checked, 40, "the sweep stopped covering the tree")

    def test_the_two_non_branch_classes_declare_themselves(self):
        # 珍贵记忆 is a property of an asset and 连拍/同一时刻 is a relation between
        # assets. A future edit that gives either of them a tree prefix has misread §4.
        for key in ("treasured_memory", "burst_moment"):
            self.assertEqual(BY_KEY[key].prefixes, (),
                             f"{key} is not a branch of the navigational tree")

    def test_a_fall_through_says_so_rather_than_picking_the_nearest_class(self):
        from pvm import importance as I
        # A document the classifier could not identify further is the case that forced
        # the fourteenth entry to exist. It must not come back as a contract, a receipt
        # or a snapshot.
        self.assertEqual(classify_asset_class(["Documents > Other Documents"]).key,
                         I.UNDESCRIBED.key)
        self.assertEqual(classify_asset_class([]).key, I.UNDESCRIBED.key)
        self.assertNotIn(I.UNDESCRIBED, ASSET_CLASSES,
                         "§4 names thirteen 大类 and this is not one of them")


class WhichClass(unittest.TestCase):
    def test_longest_prefix_wins(self):
        self.assertEqual(
            classify_asset_class(["Screenshots > Temporary"]).key, "transient_info")
        self.assertEqual(
            classify_asset_class(["Screenshots > Chat"]).key, "ordinary_screenshot")

    def test_irreplaceability_outranks_the_tree(self):
        cls = classify_asset_class(["Screenshots > Temporary"], is_irreplaceable=True)
        self.assertEqual(cls.key, "treasured_memory")

    def test_a_burst_of_nothing_in_particular_is_a_burst(self):
        self.assertEqual(classify_asset_class([], in_equivalence_group=True).key,
                         "burst_moment")

    def test_a_receipt_is_a_transaction_not_a_legal_document(self):
        # Both live under Documents; §4 separates them and so must the mapping.
        self.assertEqual(classify_asset_class(["Documents > Receipts"]).key,
                         "transaction")
        self.assertEqual(classify_asset_class(["Documents > Contracts"]).key,
                         "legal_formal")


class TheAxisIsNotRisk(unittest.TestCase):
    """The case the whole module exists for."""

    def test_a_passport_outranks_a_grandmother_on_risk(self):
        passport = classify_risk(_classification("Documents > Identity"))
        person = classify_risk(_classification("People > Anna"))
        self.assertGreater(passport, person)

    def test_and_a_grandmother_outranks_a_passport_on_importance(self):
        passport = assess(ImportanceSignals(paths=["Documents > Identity"]))
        person = assess(ImportanceSignals(paths=["People > Anna"],
                                          people_recurrence=RECURRING_PERSON))
        self.assertGreater(person.level, passport.level)
        # And the two orderings are genuinely opposite, which is the point: one axis
        # could not have produced both.
        self.assertEqual(passport.level, Importance.I2_ORDINARY)
        self.assertEqual(person.level, Importance.I4_TREASURED)


class HowALevelIsReached(unittest.TestCase):
    def test_a_recurring_person_raises_it_and_a_stranger_does_not(self):
        stranger = assess(ImportanceSignals(paths=["People > Ben"], people_recurrence=1))
        known = assess(ImportanceSignals(paths=["People > Ben"],
                                         people_recurrence=RECURRING_PERSON))
        self.assertEqual(stranger.level, Importance.I3_MEANINGFUL)
        self.assertEqual(known.level, Importance.I4_TREASURED)

    def test_irreplaceable_short_circuits_everything(self):
        a = assess(ImportanceSignals(paths=["Screenshots > Temporary"],
                                     recoverability=Recoverability.IRREPLACEABLE,
                                     is_exact_duplicate=True,
                                     in_equivalence_group=True, group_size=40))
        self.assertEqual(a.level, Importance.I4_TREASURED)
        self.assertIn("irreplaceable", a.reasons[-1])

    def test_one_frame_of_a_long_burst_is_worth_less_than_the_moment(self):
        alone = assess(ImportanceSignals(paths=["Places > Japan"]))
        in_burst = assess(ImportanceSignals(paths=["Places > Japan"],
                                            in_equivalence_group=True,
                                            group_size=BURST_SIZE))
        self.assertLess(in_burst.level, alone.level)

    def test_a_short_group_is_not_a_burst(self):
        pair = assess(ImportanceSignals(paths=["Places > Japan"],
                                        in_equivalence_group=True,
                                        group_size=BURST_SIZE - 1))
        self.assertEqual(pair.level, Importance.I2_ORDINARY)

    def test_a_burst_of_a_treasured_occasion_stays_protected(self):
        # One level of reduction, deliberately, so holding the shutter down at a
        # wedding does not drop the frames out of protection.
        a = assess(ImportanceSignals(paths=["People > Anna"],
                                     people_recurrence=RECURRING_PERSON,
                                     in_equivalence_group=True, group_size=40))
        self.assertGreaterEqual(a.level, NEVER_DELETE_AT_OR_ABOVE_IMPORTANCE)

    def test_section_14_can_raise_importance(self):
        plain = assess(ImportanceSignals(paths=["Objects > Bicycle"]))
        protected = assess(ImportanceSignals(paths=["Objects > Bicycle"],
                                             user_protects_category=True))
        self.assertGreater(protected.level, plain.level)
        self.assertIn("§14", protected.reasons[-1])

    def test_every_assessment_can_say_why(self):
        for paths in ([], ["People > Anna"], ["Documents > Identity"],
                      ["Screenshots > Temporary"], ["Downloads > Memes"]):
            a = assess(ImportanceSignals(paths=paths))
            self.assertTrue(a.reasons, f"{paths} produced a level with no reason")
            self.assertIn("§4", a.reasons[0])

    def test_the_scale_is_never_left(self):
        # Every combination of every adjustment, in both directions.
        for rec in Recoverability:
            for recurrence in (0, RECURRING_PERSON):
                for group in (1, 40):
                    for dup in (False, True):
                        for pref in (False, True):
                            a = assess(ImportanceSignals(
                                paths=["Screenshots > Temporary"], recoverability=rec,
                                people_recurrence=recurrence, group_size=group,
                                in_equivalence_group=(group > 1),
                                is_exact_duplicate=dup, user_protects_category=pref))
                            self.assertIn(a.level, list(Importance))


class WhatItChangesInThePolicy(unittest.TestCase):
    def _f(self, **kw):
        base = dict(risk=Risk.R2_NORMAL, lifecycle=Lifecycle.ACTIVE, confidence=0.9,
                    recoverability=Recoverability.RECOVERABLE)
        base.update(kw)
        return Factors(**base)

    def test_section_8_a_meme_and_a_family_photo_do_not_get_the_same_policy(self):
        """§8: 同样的相似度，在 Meme 和家庭照片上采取不同策略."""
        meme = decide_action(self._f(importance=Importance.I1_LOW,
                                     in_equivalence_group=True))
        family = decide_action(self._f(importance=Importance.I4_TREASURED,
                                       in_equivalence_group=True))
        self.assertEqual(meme, Action.SELECT_BEST)
        self.assertEqual(family, Action.KEEP)

    def test_a_personal_habit_cannot_reach_meaningful_content(self):
        # §14 allows a user's demonstrated pattern to make the system more aggressive
        # below R4. People is R3, so risk alone would have permitted this.
        got = decide_action(self._f(risk=Risk.R3_PERSONAL,
                                    importance=Importance.I3_MEANINGFUL,
                                    personal_preference=Action.SUGGEST_DELETE))
        self.assertNotEqual(got, Action.SUGGEST_DELETE)

    def test_a_personal_habit_still_reaches_low_importance_content(self):
        got = decide_action(self._f(risk=Risk.R1_LOW_VALUE,
                                    importance=Importance.I1_LOW,
                                    personal_preference=Action.SUGGEST_DELETE))
        self.assertEqual(got, Action.SUGGEST_DELETE)

    def test_a_habit_may_always_make_the_system_more_careful(self):
        for imp in Importance:
            got = decide_action(self._f(importance=imp,
                                        personal_preference=Action.PROTECT))
            self.assertEqual(got, Action.PROTECT)

    def test_the_default_is_the_behaviour_that_existed_before_the_axis(self):
        # A caller that has not assessed importance must not accidentally receive the
        # protections a real assessment earns.
        self.assertEqual(self._f().importance, Importance.I2_ORDINARY)
        self.assertEqual(decide_action(self._f(in_equivalence_group=True)),
                         Action.SELECT_BEST)

    def test_the_proposal_guard_refuses_removal_of_meaningful_content(self):
        c = _classification("People > Anna")
        f = self._f(importance=Importance.I3_MEANINGFUL)
        with self.assertRaises(ValueError) as caught:
            Proposal("a1", Action.SUGGEST_DELETE, f,
                     [Evidence("t", Tier.METADATA, 1.0, "why")])
        self.assertIn("Importance", str(caught.exception))

    def test_the_guard_is_a_red_line_at_every_risk_level(self):
        for risk in Risk:
            f = self._f(risk=risk, importance=Importance.I4_TREASURED,
                        recoverability=recoverability_of(risk))
            with self.assertRaises(ValueError):
                Proposal("a1", Action.SUGGEST_DELETE, f,
                         [Evidence("t", Tier.METADATA, 1.0, "why")])


class TablesAreGeneratedFromTheCode(unittest.TestCase):
    def test_the_class_table_lists_all_thirteen(self):
        table = class_table()
        self.assertEqual(len(ASSET_CLASSES), 13,
                         "§4 names thirteen 大类; the table must hold all of them")
        for cls in ASSET_CLASSES:
            self.assertIn(cls.name, table)
            self.assertIn(cls.examples, table)

    def test_the_equivalence_table_shows_section_8(self):
        table = equivalence_table()
        for imp in Importance:
            self.assertIn(imp.name, table)
        # The clause is only demonstrated if some row differs from the others.
        self.assertIn("keep", table)
        self.assertIn("select_best", table)


class WeightedErrorCost(unittest.TestCase):
    """§18: 错误 × 内容重要性 × 不可恢复程度 — three factors, not one squared."""

    def test_importance_is_what_is_priced(self):
        from pvm.kpi import IMPORTANCE_COST, IRRECOVERABILITY
        self.assertEqual(len(IMPORTANCE_COST), len(list(Importance)))
        self.assertEqual(len(IRRECOVERABILITY), len(list(Recoverability)))
        self.assertEqual(IMPORTANCE_COST[Importance.I0_NONE], 0.0)
        for a, b in zip(list(Importance), list(Importance)[1:]):
            self.assertLess(IMPORTANCE_COST[a], IMPORTANCE_COST[b],
                            "the cost of loss must rise with importance")


if __name__ == "__main__":
    unittest.main()
