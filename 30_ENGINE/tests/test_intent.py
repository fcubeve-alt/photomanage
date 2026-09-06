# -*- coding: utf-8 -*-
"""
Tests for Intent Search — §10's third retrieval path.

The Constitution gives two worked examples, and they are not the same problem:

    Intent Search：用户直接说“找我的身份证正反面”“找所有有气球的照片”。

The first the library can answer. The second it cannot — 气球 is not a label anything
in this build produces — and **that is the case these tests are mostly about.** A
search that silently returns everything, or silently returns nothing, turns a missing
capability into a false statement about the user's own photos.

    python -m unittest discover -s tests -v
"""

import os
import sys
import tempfile
import unittest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pvm import fixture, intent, pipeline                              # noqa: E402
from pvm.catalog import Catalog                                        # noqa: E402


def catalogued(assets=None):
    catalog = Catalog(os.path.join(tempfile.mkdtemp(), "c.sqlite"))
    pipeline.run(assets if assets is not None else fixture.build(), catalog)
    return catalog


class TheFirstWorkedExample(unittest.TestCase):
    """*找我的身份证正反面* — a query the library can answer completely."""

    def test_it_resolves_the_category_and_the_aspect(self):
        q = intent.parse("找我的身份证正反面")
        self.assertIn("Documents > Identity > ID Cards", q.paths)
        self.assertTrue(q.wants_multiple_sides)
        self.assertEqual([], q.unresolved)

    def test_the_english_form_resolves_the_same_way(self):
        q = intent.parse("find the front and back of my id card")
        self.assertIn("Documents > Identity > ID Cards", q.paths)
        self.assertTrue(q.wants_multiple_sides)

    def test_it_finds_the_id_card(self):
        catalog = catalogued()
        try:
            results = intent.search(catalog, "找我的身份证正反面")
            self.assertTrue(results.hits)
            self.assertTrue(all("ID Cards" in h.why for h in results.hits))
        finally:
            catalog.close()

    def test_the_aspect_is_answered_from_the_resolver_not_recomputed(self):
        """“正反面” is a question about entity identity, and §24 Gate 2 says that
        answer has exactly one home — the Category-Specific Entity Resolver."""
        q = intent.parse("身份证正反面")
        self.assertTrue(q.wants_multiple_sides)
        self.assertIn("more than one side", " ".join(q.understood))


class TheSecondWorkedExample(unittest.TestCase):
    """*找所有有气球的照片* — the one it cannot answer, and the reason this module
    exists. "You have no photos of balloons" and "I cannot search for balloons" are
    different statements and only one of them is true."""

    def test_the_unsearchable_term_is_named(self):
        q = intent.parse("找所有有气球的照片")
        self.assertIn("气球", q.unresolved,
                      "Chinese runs together; a matched sub-phrase used to swallow the "
                      "whole sentence and the balloon was never reported at all")

    def test_it_refuses_rather_than_returning_the_whole_library(self):
        catalog = catalogued()
        try:
            results = intent.search(catalog, "找所有有气球的照片")
            self.assertEqual([], results.hits,
                             "“照片” alone resolves to *every image*, so answering "
                             "broadly would present the entire library as the answer "
                             "to a question about balloons")
            self.assertIn("cannot search for", results.summary())
            self.assertIn("气球", results.summary())
        finally:
            catalog.close()

    def test_the_refusal_says_it_is_about_the_search_not_the_photos(self):
        catalog = catalogued()
        try:
            summary = intent.search(catalog, "找所有有气球的照片").summary()
            self.assertIn("not a statement about your photos", summary)
        finally:
            catalog.close()

    def test_a_media_type_alone_does_not_count_as_narrowing(self):
        q = intent.parse("找所有有气球的照片")
        self.assertEqual("image", q.media_type)
        self.assertFalse(q.narrows)
        self.assertFalse(q.answerable)


class WhatItUnderstoodIsAlwaysReported(unittest.TestCase):

    def test_a_partly_understood_query_still_answers_and_still_warns(self):
        catalog = catalogued()
        try:
            results = intent.search(catalog, "找 Anna 的气球照片")
            self.assertTrue(results.hits, "Anna is indexed, so the query narrows")
            self.assertIn("气球", results.summary())
            self.assertIn("Anna", results.summary())
        finally:
            catalog.close()

    def test_a_query_that_resolves_to_nothing_says_so(self):
        q = intent.parse("那阵子拍的东西")
        self.assertTrue(q.is_empty)
        self.assertIn("cannot search", q.explain())


class ItSearchesTheUsersOwnLibrary(unittest.TestCase):
    """Names come from the catalogue, not from a list written into this file. A search
    that only recognises names someone wrote down in advance is not searching the
    user's library."""

    def test_people_and_places_come_from_the_stored_memory(self):
        catalog = catalogued()
        try:
            results = intent.search(catalog, "Anna")
            self.assertTrue(results.hits)
            self.assertIn("Anna", results.query.people)
        finally:
            catalog.close()

    def test_two_kinds_of_constraint_intersect_rather_than_union(self):
        """"Anna in Tokyo" means both. A single list over people and places meant
        either, and answered a one-photo question with nineteen."""
        catalog = catalogued()
        try:
            both = intent.search(catalog, "Anna in Tokyo")
            anna = intent.search(catalog, "Anna")
            self.assertIn("Anna", both.query.people)
            self.assertIn("Tokyo", both.query.places)
            self.assertLess(len(both.hits), len(anna.hits),
                            "adding a place must narrow, never widen")
        finally:
            catalog.close()

    def test_one_asset_on_three_shelves_is_one_result(self):
        """Counting (asset, path) rows made a seven-photo answer announce itself as
        fifty."""
        catalog = catalogued()
        try:
            results = intent.search(catalog, "找 Anna 的照片")
            ids = [h.asset_id for h in results.hits]
            self.assertEqual(len(ids), len(set(ids)))
        finally:
            catalog.close()


class TimeIsAnExactWindowOrNoWindow(unittest.TestCase):

    def test_a_year_narrows(self):
        catalog = catalogued()
        try:
            all_shots = intent.search(catalog, "截图")
            in_2026 = intent.search(catalog, "2026 年的截图")
            self.assertEqual(2026, in_2026.query.year)
            self.assertLess(len(in_2026.hits), len(all_shots.hits))
        finally:
            catalog.close()

    def test_a_year_is_a_range_not_a_string_prefix(self):
        """`created_at` is stored as epoch seconds. Comparing it as text matches
        nothing, silently."""
        catalog = catalogued()
        try:
            self.assertTrue(intent.search(catalog, "screenshots 2026").hits)
        finally:
            catalog.close()

    def test_a_vague_time_is_not_guessed_into_a_window(self):
        q = intent.parse("最近拍的护照")
        self.assertIsNone(q.year)
        self.assertIn("Documents > Identity > Passports", q.paths)


class NoiseIsNotReportedAsAMissingCapability(unittest.TestCase):

    def test_filler_words_are_not_unresolved_terms(self):
        q = intent.parse("show me all my receipts from 2026")
        self.assertEqual([], q.unresolved,
                         "reporting “from” as unsearchable is noise that discredits "
                         "the real cases")

    def test_a_plural_leftover_is_not_a_term(self):
        q = intent.parse("my passports")
        self.assertEqual([], q.unresolved,
                         "consuming “passport” out of “passports” leaves an “s”")


if __name__ == "__main__":
    unittest.main(verbosity=2)
