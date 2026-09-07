# -*- coding: utf-8 -*-
"""
§10 Relations, the join: 从某个人、物品、订单、旅行进入，找到相关照片、截图、文件和收据.

Walking from one entity to its own sightings has worked since the memory graph was
built. What did not exist is the step ACROSS categories — from a receipt to the warranty
document for the same purchase, or from an order screenshot to the photo of what
arrived. Three assets, three roots, three entities, and nothing joining them.

Most of these tests are about what does not join. A false join puts someone else's order
in your warranty folder, and §9's whole argument is that being wrong about identity is
the expensive kind of wrong.
"""

from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pvm import memory, taxonomy
from pvm.classifier import Classifier
from pvm.context import build_context
from pvm.memory import MIN_JOIN_DIGITS
from pvm.signals import AssetSignals


def paper(aid, text, day=1, screenshot=False):
    a = AssetSignals(aid)
    a.created_at = datetime(2026, 3, day, 12)
    a.ocr_ran, a.ocr_text = True, text
    a.source = "screenshot" if screenshot else "camera"
    a.is_screenshot = screenshot
    if screenshot:
        a.pixel_w, a.pixel_h = 1170, 2532
    return a


def graph_of(*assets):
    taxonomy.reset_minted()
    ctx = build_context(list(assets))
    cl = Classifier(ctx)
    classifications = {a.asset_id: cl.classify(a) for a in assets}
    return memory.build(list(assets), classifications, ctx)


def joins(graph):
    return {e.name: sorted(o.asset_id for o in graph.observations
                           if o.entity_id == e.entity_id)
            for e in graph.entities.values() if e.name.startswith("Reference ")}


class TheJoin(unittest.TestCase):
    def test_a_receipt_and_its_warranty_reach_each_other(self):
        graph = graph_of(
            paper("receipt", "RECEIPT — HEADPHONES  ORDER NO 784125  £129.00"),
            paper("warranty", "WARRANTY CERTIFICATE  ORDER NO 784125  24 MONTHS", day=4))
        self.assertEqual(joins(graph), {"Reference 784125": ["receipt", "warranty"]})

    def test_an_order_screenshot_reaches_the_delivery_photo(self):
        graph = graph_of(
            paper("order", "ORDER CONFIRMATION  ORDER NO 784125", screenshot=True),
            paper("delivery", "DELIVERED  ORDER NO 784125", day=6))
        self.assertIn("Reference 784125", joins(graph))
        self.assertEqual(joins(graph)["Reference 784125"], ["delivery", "order"])

    def test_the_relation_can_say_why_it_exists(self):
        graph = graph_of(
            paper("a", "RECEIPT  ORDER NO 784125"),
            paper("b", "WARRANTY  ORDER NO 784125", day=3))
        entity = next(e for e in graph.entities.values()
                      if e.name == "Reference 784125")
        self.assertTrue(entity.evidence)
        self.assertIn("784125", entity.evidence[0].reason)

    def test_three_assets_on_one_reference_all_join(self):
        graph = graph_of(
            paper("receipt", "RECEIPT  ORDER NO 784125"),
            paper("warranty", "WARRANTY  ORDER NO 784125", day=3),
            paper("order", "ORDER CONFIRMATION  ORDER NO 784125", screenshot=True))
        self.assertEqual(joins(graph)["Reference 784125"],
                         ["order", "receipt", "warranty"])


class WhatDoesNotJoin(unittest.TestCase):
    def test_two_different_references_stay_apart(self):
        graph = graph_of(
            paper("a", "RECEIPT  ORDER NO 784125"),
            paper("b", "RECEIPT  ORDER NO 990001", day=3))
        self.assertEqual(joins(graph), {})

    def test_one_asset_with_a_reference_is_not_a_relation(self):
        graph = graph_of(paper("a", "RECEIPT  ORDER NO 784125"))
        self.assertEqual(joins(graph), {},
                         "a document with a number on it is a document, not a relation")

    def test_a_short_number_is_not_enough_to_join_on(self):
        """Two digits is a hundred possible values. That is a collision waiting to put
        a stranger's order in someone's warranty folder."""
        short = "1" * (MIN_JOIN_DIGITS - 1)
        graph = graph_of(
            paper("a", f"RECEIPT  ORDER NO {short}"),
            paper("b", f"WARRANTY  ORDER NO {short}", day=3))
        self.assertEqual(joins(graph), {})

    def test_shared_words_do_not_join(self):
        graph = graph_of(
            paper("a", "RECEIPT — NORTHSIDE COFFEE  TOTAL 4.20"),
            paper("b", "RECEIPT — NORTHSIDE COFFEE  TOTAL 3.10", day=3))
        self.assertEqual(joins(graph), {},
                         "a shop name is not a reference; no fuzzy matching")

    def test_contract_page_numbers_do_not_join_unrelated_contracts(self):
        graph = graph_of(
            paper("c1", "CONTRACT — PAGE 2 OF 4  TENANCY"),
            paper("c2", "AGREEMENT — PAGE 2 OF 4  EMPLOYMENT", day=3))
        self.assertEqual(joins(graph), {},
                         "page numbering is not a reference number")

    def test_nothing_joins_without_ocr(self):
        a, b = paper("a", "RECEIPT  ORDER NO 784125"), paper("b", "RECEIPT  ORDER NO 784125", day=3)
        a.ocr_ran = b.ocr_ran = False
        graph = graph_of(a, b)
        self.assertEqual(joins(graph), {})


class ItIsTraversable(unittest.TestCase):
    def test_history_walks_from_the_reference_to_every_asset(self):
        graph = graph_of(
            paper("receipt", "RECEIPT  ORDER NO 784125"),
            paper("warranty", "WARRANTY  ORDER NO 784125", day=3))
        entity = next(e for e in graph.entities.values()
                      if e.name == "Reference 784125")
        history = graph.history(entity.entity_id)
        self.assertTrue(history)
        self.assertEqual(sorted(o.asset_id for o in history), ["receipt", "warranty"])


if __name__ == "__main__":
    unittest.main()
