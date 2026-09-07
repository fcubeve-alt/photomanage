# -*- coding: utf-8 -*-
"""
Tests for Personal Policy — §14.

    如果用户总是删除某类工作截图，系统以后可以更激进。
    如果用户始终保留人物连拍，系统对该用户自动变得保守。

The Constitution explicitly allows a personal policy to make the system **less**
careful, and until now `decide_action` honoured only PROTECT and KEEP — safe, and not
what §14 says. Most of this file is about the line where §14 stops and §6 starts, and
about what counts as evidence that a user "always" does something.

    python -m unittest discover -s tests -v
"""

import os
import sys
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pvm import personal                                              # noqa: E402
from pvm.catalog import Catalog                                       # noqa: E402
from pvm.personal import (Decision, MIN_AGREEMENT, MIN_OBSERVATIONS,  # noqa: E402
                          PersonalPolicy, learn)
from pvm.risk import (Action, Factors, Lifecycle, Recoverability,     # noqa: E402
                      Risk, decide_action)

WHEN = datetime(2026, 1, 1, 12)


def decisions(path: str, action: str, n: int, start=WHEN):
    return [Decision(f"{path}-{i}", path, action, start + timedelta(days=i))
            for i in range(n)]


def factors(risk=Risk.R2_NORMAL, confidence=0.5, **kw):
    return Factors(risk=risk, lifecycle=kw.pop("lifecycle", Lifecycle.ACTIVE),
                   confidence=confidence,
                   recoverability=kw.pop("recoverability", Recoverability.RECOVERABLE),
                   **kw)


class WhatCountsAsAlways(unittest.TestCase):
    """总是 / 始终 is the Constitution's own word. One deletion is a mood."""

    def test_a_few_decisions_are_not_a_pattern(self):
        policy = learn(decisions("Screenshots > Work", "delete", MIN_OBSERVATIONS - 1))
        self.assertEqual({}, policy.preferences)

    def test_enough_consistent_decisions_are(self):
        policy = learn(decisions("Screenshots > Work", "delete", MIN_OBSERVATIONS))
        self.assertIn("Screenshots > Work", policy.preferences)
        self.assertIs(Action.SUGGEST_DELETE, policy.preferences["Screenshots > Work"].action)

    def test_an_inconsistent_category_teaches_nothing(self):
        """Being asked case by case is what the user is telling us here. Picking the
        majority would be reading a coin flip as a preference."""
        mixed = (decisions("Screenshots > Work", "delete", 6)
                 + decisions("Screenshots > Work", "keep", 6))
        self.assertEqual({}, learn(mixed).preferences)

    def test_the_preference_says_what_it_is_standing_on(self):
        policy = learn(decisions("Screenshots > Work", "delete", 12))
        why = policy.preferences["Screenshots > Work"].why()
        self.assertIn("12", why)
        self.assertIn("100%", why)

    def test_a_correction_is_not_a_preference_about_actions(self):
        """A correction says the *classification* was wrong, not that the action was.
        Reading "you filed this in the wrong place" as "you may delete things like
        this" is the inference §11 and §16 exist to prevent."""
        policy = learn(decisions("Screenshots > Work", "correction", 20))
        self.assertEqual({}, policy.preferences)
        self.assertEqual(20, policy.decisions_seen)

    def test_an_unknown_verb_is_refused(self):
        with self.assertRaises(ValueError):
            Decision("a", "Screenshots", "archive-it", WHEN)


class SectionFourteenIsHonoured(unittest.TestCase):
    """如果用户总是删除某类工作截图，系统以后可以更激进."""

    def test_a_demonstrated_pattern_turns_review_into_a_proposal(self):
        f = factors(confidence=0.4)
        self.assertIs(Action.REVIEW, decide_action(f))
        self.assertIs(Action.SUGGEST_DELETE,
                      decide_action(replace(f, personal_preference=Action.SUGGEST_DELETE)),
                      "§14 allows the system to become more aggressive for a category "
                      "the user always deletes")

    def test_keeping_bursts_of_people_makes_it_conservative(self):
        """如果用户始终保留人物连拍，系统对该用户自动变得保守."""
        f = factors(risk=Risk.R3_PERSONAL, in_equivalence_group=True, confidence=0.9)
        self.assertIs(Action.KEEP, decide_action(replace(f, personal_preference=Action.KEEP)))


class SectionSixIsNotNegotiable(unittest.TestCase):
    """§6's red lines are not preferences, and are not negotiable by anyone — the user
    included. No amount of consistent behaviour makes a passport a disposable
    screenshot."""

    def test_a_delete_preference_cannot_reach_r4(self):
        for risk in (Risk.R4_IMPORTANT, Risk.R5_CRITICAL, Risk.R6_IRREPLACEABLE):
            action = decide_action(
                replace(factors(risk=risk), personal_preference=Action.SUGGEST_DELETE))
            self.assertNotIn(action, (Action.SUGGEST_DELETE, Action.AUTO_CLEAN),
                             f"{risk.name} was relaxed by a personal preference")

    def test_the_policy_withholds_it_too_rather_than_relying_on_one_guard(self):
        policy = learn(decisions("Documents > Identity > Passports", "delete", 30))
        self.assertIsNone(
            policy.preference_for(["Documents > Identity > Passports"], Risk.R5_CRITICAL),
            "the policy must not hand out a relaxing preference at R4+, even though "
            "decide_action would refuse it — one guard is a single point of failure")

    def test_becoming_more_careful_is_allowed_at_any_risk(self):
        for risk in Risk:
            action = decide_action(
                replace(factors(risk=risk), personal_preference=Action.PROTECT))
            self.assertIs(Action.PROTECT, action, f"{risk.name}")

    def test_no_preference_can_produce_an_irreversible_action(self):
        """The most aggressive thing a preference may produce is SUGGEST_DELETE, which
        still requires confirmation. AUTO_CLEAN is reachable only from byte-identical
        duplication, which is evidence rather than taste."""
        for preference in (Action.AUTO_CLEAN, Action.SUGGEST_DELETE):
            action = decide_action(
                replace(factors(confidence=0.4), personal_preference=preference))
            self.assertIsNot(Action.AUTO_CLEAN, action)


class MostSpecificWins(unittest.TestCase):

    def test_a_deeper_preference_beats_a_shallower_one(self):
        policy = learn(decisions("Screenshots > Temporary", "delete", 12)
                       + decisions("Screenshots > Chat", "keep", 12))
        deep = policy.preference_for(["Screenshots > Temporary"], Risk.R1_LOW_VALUE)
        self.assertIsNotNone(deep)
        self.assertEqual("Screenshots > Temporary", deep.path)
        self.assertIs(Action.SUGGEST_DELETE, deep.action)

    def test_a_category_the_user_never_touched_has_no_preference(self):
        policy = learn(decisions("Screenshots > Work", "delete", 12))
        self.assertIsNone(policy.preference_for(["People > Anna"], Risk.R3_PERSONAL))


class ItStartsEmptyAndSaysSo(unittest.TestCase):

    def test_a_new_library_has_no_policy_and_that_is_correct(self):
        policy = PersonalPolicy()
        self.assertEqual({}, policy.preferences)
        self.assertIsNone(policy.preference_for(["Screenshots"], Risk.R2_NORMAL))


class TheLogIsTheDurableThing(unittest.TestCase):

    def test_decisions_round_trip_and_the_policy_is_derived_from_them(self):
        catalog = Catalog(os.path.join(tempfile.mkdtemp(), "c.sqlite"))
        try:
            for i in range(12):
                catalog.record_decision(f"s{i}", "Screenshots > Work", "delete")
            self.assertEqual(12, len(catalog.decisions()))
            policy = catalog.personal_policy()
            self.assertIn("Screenshots > Work", policy.preferences)
        finally:
            catalog.close()

    def test_a_bad_verb_never_reaches_the_table(self):
        catalog = Catalog(os.path.join(tempfile.mkdtemp(), "c.sqlite"))
        try:
            with self.assertRaises(ValueError):
                catalog.record_decision("s1", "Screenshots", "yeet")
            self.assertEqual([], catalog.decisions())
        finally:
            catalog.close()


class PersonalizationGainMeasuresOutcomes(unittest.TestCase):
    """Not the number of rules learned. A policy that fires on nothing the user owns
    has taught the system nothing, and would score well on any metric counting rules."""

    def test_gain_is_zero_when_the_policy_matches_nothing_owned(self):
        gain = personal.PersonalizationGain(reviews_without_policy=10,
                                            reviews_with_policy=10, assets=100)
        self.assertEqual(0, gain.reviews_avoided)
        self.assertEqual(0.0, gain.gain)

    def test_gain_counts_questions_the_user_was_not_asked(self):
        gain = personal.PersonalizationGain(reviews_without_policy=10,
                                            reviews_with_policy=4, assets=100)
        self.assertEqual(6, gain.reviews_avoided)
        self.assertAlmostEqual(0.6, gain.gain)
        self.assertIn("6 of 10", gain.human())


if __name__ == "__main__":
    unittest.main(verbosity=2)
