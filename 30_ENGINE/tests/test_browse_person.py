# -*- coding: utf-8 -*-
"""
§10's first retrieval path: Browse：用户知道类别，直接 Documents → IDs → Person → ID Card.

The Person level did not exist, so the worked example the Constitution gives for Browse
could not be walked. These tests hold two things: that it exists in §10's own ordering,
and that the guard which stops a rule inventing a category is still a guard.
"""

from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pvm import taxonomy
from pvm.classifier import Classifier
from pvm.context import build_context
from pvm.signals import AssetSignals
from pvm.taxonomy import InvalidPath


def doc(asset_id: str, text: str) -> AssetSignals:
    a = AssetSignals(asset_id)
    a.ocr_ran, a.ocr_text, a.source = True, text, "camera"
    a.created_at = datetime(2025, 6, 18, 12)
    return a


def classify(*assets):
    taxonomy.reset_minted()
    cl = Classifier(build_context(list(assets)))
    return {a.asset_id: sorted(cl.classify(a).paths) for a in assets}


class TheWorkedExample(unittest.TestCase):
    def test_documents_ids_person_id_card(self):
        got = classify(doc("a", "ID CARD  NAME: JANE DOE  NO 88231"))["a"]
        self.assertIn("Documents > Identity > Jane Doe > ID Cards", got,
                      "§10 spells the Browse path out as Documents → IDs → Person → "
                      "ID Card; that is the path a user is told they can walk")

    def test_the_type_shelf_survives(self):
        """A cross-listing, not a replacement. §3: 同一 asset 可以出现在多个入口."""
        got = classify(doc("a", "PASSPORT  NAME: JANE DOE"))["a"]
        self.assertIn("Documents > Identity > Passports", got)
        self.assertIn("Documents > Identity > Jane Doe > Passports", got)

    def test_the_person_entry_records_where_it_came_from(self):
        taxonomy.reset_minted()
        a = doc("a", "PASSPORT  NAME: JANE DOE")
        c = Classifier(build_context([a])).classify(a)
        person = next(x for x in c.assignments if "Jane Doe" in x.path)
        self.assertEqual(person.cross_listed_from, "Documents > Identity > Passports")

    def test_two_people_can_have_their_own_shelves(self):
        got = classify(doc("a", "PASSPORT  NAME: JANE DOE"),
                       doc("b", "ID CARD  SURNAME: BEN SMITH  NO 4"))
        self.assertIn("Documents > Identity > Jane Doe > Passports", got["a"])
        self.assertIn("Documents > Identity > Ben Smith > ID Cards", got["b"])


class WhatItRefuses(unittest.TestCase):
    def test_two_holders_named_on_one_document(self):
        """A second signatory, or an OCR error that produced a name from a caption.
        Filing it under both puts a stranger's name on a shelf of the user's papers."""
        got = classify(doc("a", "PASSPORT  NAME: JANE DOE  HOLDER: BEN SMITH"))["a"]
        self.assertNotIn(True, [p.count(" > ") == 3 for p in got if p.startswith("Documents")])
        self.assertIn("Documents > Identity > Passports", got)

    def test_no_holder_named(self):
        got = classify(doc("a", "PASSPORT  ISSUED 2019"))["a"]
        self.assertEqual([p for p in got if p.startswith("Documents")],
                         ["Documents > Identity > Passports"])

    def test_a_receipt_with_a_name_on_it_is_not_an_identity_document(self):
        got = classify(doc("a", "RECEIPT  NAME: JANE DOE  TOTAL 12.00"))["a"]
        self.assertFalse([p for p in got if "Jane Doe" in p])

    def test_nothing_happens_without_ocr(self):
        a = AssetSignals("a")
        a.source, a.created_at = "camera", datetime(2025, 6, 18, 12)
        got = classify(a)["a"]
        self.assertFalse([p for p in got if "Identity" in p])


class TheGuardIsStillAGuard(unittest.TestCase):
    """`EXTENSIBLE_ROOTS` exists so that a rule inventing `Documents > Crypto` fails
    here rather than being discovered in the browse UI. Opening `Documents` to make
    §10's path possible would have bought the path at the cost of the guard, so
    extensibility is now per branch."""

    def test_the_identity_branch_may_grow(self):
        taxonomy.reset_minted()
        self.assertEqual(taxonomy.ensure_node("Documents > Identity > Jane Doe"),
                         "Documents > Identity > Jane Doe")

    def test_no_other_documents_branch_may(self):
        taxonomy.reset_minted()
        for path in ("Documents > Crypto",
                     "Documents > Receipts > Jane Doe",
                     "Documents > Contracts > Jane Doe",
                     "Documents > Other Documents > Jane Doe"):
            with self.assertRaises(InvalidPath, msg=f"{path} was minted"):
                taxonomy.ensure_node(path)

    def test_no_other_root_may(self):
        taxonomy.reset_minted()
        for path in ("Purchases > Anything", "Work > Anything", "Objects > Anything"):
            with self.assertRaises(InvalidPath, msg=f"{path} was minted"):
                taxonomy.ensure_node(path)

    def test_the_branch_has_a_depth_limit(self):
        taxonomy.reset_minted()
        taxonomy.ensure_node("Documents > Identity > Jane Doe > Passports")
        with self.assertRaises(InvalidPath):
            taxonomy.ensure_node("Documents > Identity > Jane Doe > Passports > 2019")

    def test_the_branch_itself_is_not_minted(self):
        """`Documents > Identity` is canonical. A branch may only grow BELOW itself."""
        taxonomy.reset_minted()
        taxonomy.ensure_node("Documents > Identity > Jane Doe")
        self.assertNotIn("Documents > Identity", taxonomy.minted_nodes())

    def test_the_extensible_roots_are_unchanged(self):
        self.assertEqual(set(taxonomy.EXTENSIBLE_ROOTS),
                         {"People", "Places", "Travel", "Timeline"},
                         "Documents must NOT be an extensible root — that was the "
                         "shortcut this mechanism exists to avoid")


if __name__ == "__main__":
    unittest.main()
