# -*- coding: utf-8 -*-
"""
Paced ingestion and the Constitution's own KPIs.

Both exist because of PF-12: L1 §24 Gate 1 and Gate 3 mandate paced, progressive
indexing with TTFUV as a P0 metric, and L1 §18 names the KPIs the product is judged
by. None of that was read before the engine was built. These tests are what makes the
clauses checkable rather than remembered.
"""

import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pvm import kpi, pipeline                                    # noqa: E402
from pvm.catalog import Catalog                                  # noqa: E402
from pvm.risk import Action, Risk                                # noqa: E402
from pvm.schedule import (BREADTH_MS, DEPTH_MS, plan_ingestion,   # noqa: E402
                          progress_report)
from pvm.signals import AssetSignals, GeoFix, PlaceName, Tier     # noqa: E402

LONDON = GeoFix(51.5074, -0.1278)
UK = PlaceName("United Kingdom", "London", 0.9)


def library(n, screenshots=0):
    out = []
    for i in range(n):
        a = AssetSignals(f"a{i:05d}", created_at=datetime(2025, 1, 1) + timedelta(hours=i),
                         geo=LONDON, place=UK, content_hash=f"h{i}", dhash=1000 + i)
        if i < screenshots:
            a.is_screenshot = True
            a.ocr_ran = True
            a.ocr_text = "SCREENSHOT"
        out.append(a)
    return out


class BreadthBeforeDepth(unittest.TestCase):
    """L1 §24 Gate 3: 首次使用必须 Progressive Indexing。先给 Quick Wins 和基本目录，
    再逐渐补全深度索引。"""

    def test_breadth_is_orders_of_magnitude_cheaper_than_depth(self):
        self.assertLess(BREADTH_MS[1] * 100, DEPTH_MS[0],
                        "if breadth were not far cheaper, there would be nothing to stage")

    def test_a_hundred_thousand_assets_are_browsable_in_under_a_minute(self):
        plan = plan_ingestion(100_000)
        self.assertLess(plan.breadth.seconds, 60)

    def test_the_user_is_told_what_they_get_before_what_we_are_doing(self):
        msg = plan_ingestion(100_000).user_message()
        self.assertIn("100,000", msg)
        self.assertLess(msg.index("ready"), msg.index("background"))

    def test_a_library_too_large_for_one_run_is_paced_not_refused(self):
        plan = plan_ingestion(100_000)
        self.assertTrue(plan.options)
        self.assertEqual(plan.recommended, "overnight")
        self.assertTrue(any("A3" in n for n in plan.notes),
                        "pacing raises the stakes on resume; the plan must say so")

    def test_a_small_library_is_not_dragged_out_for_no_reason(self):
        self.assertEqual(plan_ingestion(2_000).recommended, "now")

    def test_the_user_is_offered_choices_rather_than_given_a_schedule(self):
        plan = plan_ingestion(100_000)
        self.assertGreaterEqual(len(plan.options), 3)
        for o in plan.options:
            self.assertTrue(o.label and o.days >= 1)

    def test_quoted_figures_are_the_pessimistic_measurement(self):
        """A user is promised the slower of the two measured runs, not the flattering
        one. The two runs were 1.47x apart."""
        slow = plan_ingestion(50_000, pessimistic=True)
        fast = plan_ingestion(50_000, pessimistic=False)
        self.assertGreater(slow.breadth.seconds, fast.breadth.seconds)

    def test_progress_leads_with_what_already_works(self):
        text = progress_report(3_500, 10_000)
        self.assertIn("already findable", text)


class TheKPIsTheProductIsDefinedBy(unittest.TestCase):
    """L1 §18. An excellent F1 with a Human Review Burden of 300 per 1,000 is a failed
    product — the user was handed the work back — and the F1 cannot see it."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.catalog = Catalog(os.path.join(self.dir, "k.sqlite"))

    def tearDown(self):
        self.catalog.close()

    def test_ttfuv_is_reported_and_scales_with_the_library(self):
        self.assertLess(kpi.time_to_first_useful_view(10_000), 10)
        self.assertLess(kpi.time_to_first_useful_view(100_000), 60)

    def test_a_well_understood_library_automates_most_of_itself(self):
        pipeline.run(library(300, screenshots=60), self.catalog)
        r = kpi.report(self.catalog)
        self.assertGreater(r.automation_ratio, 0.8)
        self.assertLess(r.human_review_burden, 200)

    def test_a_library_the_engine_cannot_read_hands_the_work_back_and_says_so(self):
        """The failure mode that matters: when the engine understands nothing, the KPI
        must show the burden landing on the user rather than a comfortable coverage
        number."""
        blind = [AssetSignals(f"x{i}", created_at=datetime(2025, 5, 5)) for i in range(200)]
        pipeline.run(blind, self.catalog)
        r = kpi.report(self.catalog)
        self.assertLess(r.classification_coverage, 0.05)
        self.assertGreater(r.human_review_burden, 900)
        self.assertLess(r.automation_ratio, 0.1)

    def test_the_catastrophic_rate_is_zero_in_the_written_rows_not_only_in_the_code(self):
        assets = library(120)
        assets[7].ocr_ran = True
        assets[7].ocr_text = "PASSPORT"
        pipeline.run(assets, self.catalog)
        self.assertEqual(kpi.catastrophic_error_rate(self.catalog), 0.0)

    def test_timeline_alone_does_not_count_as_coverage(self):
        """Every dated asset lands on the timeline. Counting it would report the
        calendar as an achievement."""
        pipeline.run([AssetSignals(f"t{i}", created_at=datetime(2025, 5, 5))
                      for i in range(50)], self.catalog)
        self.assertEqual(kpi.classification_coverage(self.catalog), 0.0)

    def test_exposure_and_outcome_are_not_conflated(self):
        pipeline.run(library(200), self.catalog)
        exposure = kpi.report(self.catalog)
        outcome = kpi.report(self.catalog, errors_by_asset={})
        self.assertFalse(exposure.outcome_based)
        self.assertTrue(outcome.outcome_based)
        self.assertGreaterEqual(exposure.weighted_error_cost, outcome.weighted_error_cost)

    def test_continuous_hygiene_measures_only_the_new_arrivals(self):
        """§13: the library has to keep working after the first tidy-up. That is the
        product, not a follow-up feature."""
        first = library(100)
        pipeline.run(first, self.catalog)
        arrivals = [AssetSignals(f"new{i}", created_at=datetime(2026, 2, 2),
                                 geo=LONDON, place=UK, content_hash=f"n{i}", dhash=90_000 + i)
                    for i in range(20)]
        pipeline.run(first + arrivals, self.catalog)
        rate = kpi.continuous_hygiene_rate(self.catalog, [a.asset_id for a in arrivals])
        self.assertIsNotNone(rate)
        self.assertGreater(rate, 0.9)

    def test_no_new_arrivals_reports_nothing_rather_than_a_perfect_score(self):
        pipeline.run(library(20), self.catalog)
        self.assertIsNone(kpi.continuous_hygiene_rate(self.catalog, []))


if __name__ == "__main__":
    unittest.main(verbosity=2)
