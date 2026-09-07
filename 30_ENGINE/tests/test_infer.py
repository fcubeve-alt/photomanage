# -*- coding: utf-8 -*-
"""
§11 无 GPS 时可以利用相邻时间照片、地标等推断，但必须保存置信度.

Most of these tests are about what the inference REFUSES. That is deliberate: a place
inference that fires often is easy and wrong, and the expensive failure is a photograph
filed under a city its owner was not in. The engine already had the machinery to hold
an inference honestly and nothing that produced one; the risk in changing that is
entirely on the side of claiming too much.
"""

from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pvm import infer
from pvm.context import build_context
from pvm.infer import (AGREE_KM, BASE_CONFIDENCE, MAX_GAP, MAX_ONE_SIDED_GAP,
                       MIN_CONFIDENCE, infer_places)
from pvm.signals import AssetSignals, GeoFix, PlaceName

TOKYO = (35.6762, 139.6503)
YOKOHAMA = (35.4437, 139.6380)          # ~26 km from Tokyo, a different city
SHIBUYA = (35.6580, 139.7016)           # ~5 km from Tokyo, same city
LONDON = (51.5074, -0.1278)
T0 = datetime(2025, 4, 12, 12, 0, 0)


def asset(aid, minutes, coords=None, city=None, country=None, **kw):
    a = AssetSignals(asset_id=aid, created_at=T0 + timedelta(minutes=minutes))
    if coords is not None:
        a.geo = GeoFix(lat=coords[0], lon=coords[1], source=kw.pop("geo_source", "exif"))
        a.place = PlaceName(country=country, city=city, confidence=0.9)
    for k, v in kw.items():
        setattr(a, k, v)
    return a


class WhatItInfers(unittest.TestCase):
    def test_a_photo_between_two_in_the_same_city(self):
        out = infer_places([
            asset("before", -8, TOKYO, "Tokyo", "Japan"),
            asset("target", 0),
            asset("after", 12, SHIBUYA, "Tokyo", "Japan"),
        ])
        got = out["target"]
        self.assertEqual(got.place.city, "Tokyo")
        self.assertEqual(got.granularity, "city")
        self.assertTrue(got.is_bracketed)
        self.assertEqual(sorted(got.anchors), ["after", "before"])

    def test_the_fix_it_writes_declares_itself_inferred(self):
        out = infer_places([asset("b", -5, TOKYO, "Tokyo", "Japan"),
                            asset("t", 0),
                            asset("a", 5, TOKYO, "Tokyo", "Japan")])
        self.assertEqual(out["t"].geo.source, "inferred")
        # And GeoFix's own confidence must not read as measured.
        self.assertLess(out["t"].geo.confidence, 1.0)

    def test_confidence_is_saved_and_falls_with_the_gap(self):
        """§11: 必须保存置信度. Not a constant applied downstream — a field."""
        close = infer_places([asset("b", -2, TOKYO, "Tokyo", "Japan"),
                              asset("t", 0),
                              asset("a", 2, TOKYO, "Tokyo", "Japan")])["t"]
        far = infer_places([asset("b", -100, TOKYO, "Tokyo", "Japan"),
                            asset("t", 0),
                            asset("a", 100, TOKYO, "Tokyo", "Japan")])["t"]
        self.assertGreater(close.confidence, far.confidence)
        self.assertLessEqual(close.confidence, BASE_CONFIDENCE)
        self.assertGreaterEqual(far.confidence, MIN_CONFIDENCE)

    def test_one_sided_is_weaker_than_bracketed_at_the_same_gap(self):
        gap = 10
        bracketed = infer_places([asset("b", -gap, TOKYO, "Tokyo", "Japan"),
                                  asset("t", 0),
                                  asset("a", gap, TOKYO, "Tokyo", "Japan")])["t"]
        one_sided = infer_places([asset("b", -gap, TOKYO, "Tokyo", "Japan"),
                                  asset("t", 0)])["t"]
        self.assertGreater(bracketed.confidence, one_sided.confidence)
        self.assertFalse(one_sided.is_bracketed)
        self.assertIn("nearest photo", one_sided.reason)

    def test_the_reason_says_no_location_was_saved(self):
        for assets in ([asset("b", -5, TOKYO, "Tokyo", "Japan"), asset("t", 0),
                        asset("a", 5, TOKYO, "Tokyo", "Japan")],
                       [asset("b", -5, TOKYO, "Tokyo", "Japan"), asset("t", 0)]):
            got = infer_places(assets)["t"]
            self.assertIn("no location was saved", got.reason)


class TheConstantsMeanWhatTheySay(unittest.TestCase):
    """The reach limits must be the actual reach.

    The first version of `_confidence` decayed towards zero and then refused anything
    under `MIN_CONFIDENCE`, so `MAX_GAP = 2 hours` was really 52 minutes and a
    one-sided inference was refused at every gap including zero. Two other tests caught
    the symptom; this catches the cause, which is the one that will come back.
    """

    def _bracketed_at(self, minutes):
        return infer_places([asset("b", -minutes, TOKYO, "Tokyo", "Japan"),
                             asset("t", 0),
                             asset("a", minutes, TOKYO, "Tokyo", "Japan")]).get("t")

    def _one_sided_at(self, minutes):
        return infer_places([asset("b", -minutes, TOKYO, "Tokyo", "Japan"),
                             asset("t", 0)]).get("t")

    def test_a_bracketed_inference_reaches_max_gap(self):
        limit = int(MAX_GAP.total_seconds() / 60)
        self.assertIsNotNone(self._bracketed_at(limit - 1),
                             f"MAX_GAP says {limit} minutes; it did not reach "
                             f"{limit - 1}")
        self.assertIsNone(self._bracketed_at(limit + 1))

    def test_a_one_sided_inference_reaches_its_own_limit(self):
        limit = int(MAX_ONE_SIDED_GAP.total_seconds() / 60)
        self.assertIsNotNone(self._one_sided_at(limit - 1),
                             f"MAX_ONE_SIDED_GAP says {limit} minutes; it did not "
                             f"reach {limit - 1}")
        self.assertIsNone(self._one_sided_at(limit + 1))

    def test_confidence_stays_inside_its_stated_band(self):
        for minutes in range(0, int(MAX_GAP.total_seconds() / 60), 7):
            got = self._bracketed_at(minutes)
            if got is None:
                continue
            self.assertLessEqual(got.confidence, BASE_CONFIDENCE)
            self.assertGreaterEqual(got.confidence, MIN_CONFIDENCE)

    def test_it_never_claims_as_much_as_a_measurement(self):
        got = self._bracketed_at(0)
        self.assertLess(got.confidence, 1.0)
        self.assertLess(got.place.confidence, 1.0)


class MinimumNecessaryInference(unittest.TestCase):
    """L1-B: claim the most specific thing the evidence supports, then stop."""

    def test_two_cities_one_country_infers_the_country_only(self):
        out = infer_places([
            asset("before", -30, TOKYO, "Tokyo", "Japan"),
            asset("target", 0),
            asset("after", 30, YOKOHAMA, "Yokohama", "Japan"),
        ])
        # Tokyo and Yokohama are ~26 km apart, just past AGREE_KM, so this pair is
        # rejected outright. Bring them inside the radius with a nearer anchor and the
        # country rung is what should be reached.
        self.assertNotIn("target", out)

        out = infer_places([
            asset("before", -30, TOKYO, "Tokyo", "Japan"),
            asset("target", 0),
            asset("after", 30, SHIBUYA, "Kawasaki", "Japan"),
        ])
        got = out["target"]
        self.assertEqual(got.granularity, "country")
        self.assertIsNone(got.place.city)
        self.assertEqual(got.place.country, "Japan")
        self.assertIn("the city is not certain", got.reason)

    def test_anchors_far_apart_infer_nothing(self):
        out = infer_places([
            asset("before", -30, TOKYO, "Tokyo", "Japan"),
            asset("target", 0),
            asset("after", 30, LONDON, "London", "United Kingdom"),
        ])
        self.assertNotIn("target", out,
                         "a photo between Tokyo and London is in neither, and picking "
                         "the nearer anchor would be an invention")

    def test_agree_km_is_the_line(self):
        a = GeoFix(*TOKYO)
        self.assertGreater(a.km_to(GeoFix(*YOKOHAMA)), AGREE_KM)
        self.assertLess(a.km_to(GeoFix(*SHIBUYA)), AGREE_KM)


class WhatItRefuses(unittest.TestCase):
    def test_a_measured_fix_is_never_overwritten(self):
        out = infer_places([asset("b", -5, TOKYO, "Tokyo", "Japan"),
                            asset("t", 0, LONDON, "London", "United Kingdom"),
                            asset("a", 5, TOKYO, "Tokyo", "Japan")])
        self.assertNotIn("t", out)

    def test_a_screenshot_gets_no_place(self):
        out = infer_places([asset("b", -5, TOKYO, "Tokyo", "Japan"),
                            asset("t", 0, is_screenshot=True),
                            asset("a", 5, TOKYO, "Tokyo", "Japan")])
        self.assertNotIn("t", out,
                         "a screenshot taken while in Tokyo was not taken in Tokyo")

    def test_a_download_gets_no_place(self):
        out = infer_places([asset("b", -5, TOKYO, "Tokyo", "Japan"),
                            asset("t", 0, source="downloaded"),
                            asset("a", 5, TOKYO, "Tokyo", "Japan")])
        self.assertNotIn("t", out)

    def test_a_screenshot_is_not_used_as_an_anchor(self):
        out = infer_places([asset("b", -5, TOKYO, "Tokyo", "Japan", is_screenshot=True),
                            asset("t", 0)])
        self.assertNotIn("t", out)

    def test_beyond_the_bracketed_reach_nothing_is_claimed(self):
        far = int(MAX_GAP.total_seconds() / 60) + 5
        out = infer_places([asset("b", -far, TOKYO, "Tokyo", "Japan"),
                            asset("t", 0),
                            asset("a", far, TOKYO, "Tokyo", "Japan")])
        self.assertNotIn("t", out)

    def test_beyond_the_one_sided_reach_nothing_is_claimed(self):
        far = int(MAX_ONE_SIDED_GAP.total_seconds() / 60) + 5
        out = infer_places([asset("b", -far, TOKYO, "Tokyo", "Japan"), asset("t", 0)])
        self.assertNotIn("t", out)

    def test_a_distant_anchor_does_not_veto_a_close_one(self):
        """One side hours away and the other five minutes away must still infer."""
        out = infer_places([
            asset("b", -5, TOKYO, "Tokyo", "Japan"),
            asset("t", 0),
            asset("a", int(MAX_GAP.total_seconds() / 60) + 60, TOKYO, "Tokyo", "Japan"),
        ])
        self.assertIn("t", out)
        self.assertFalse(out["t"].is_bracketed)

    def test_an_asset_with_no_timestamp_is_left_alone(self):
        a = AssetSignals(asset_id="t")
        out = infer_places([asset("b", -5, TOKYO, "Tokyo", "Japan"), a])
        self.assertNotIn("t", out)

    def test_a_library_with_no_fixes_infers_nothing_rather_than_crashing(self):
        self.assertEqual(infer_places([asset("t", 0), asset("u", 5)]), {})

    def test_mixed_aware_and_naive_timestamps_do_not_raise(self):
        from datetime import timezone
        b = asset("b", -5, TOKYO, "Tokyo", "Japan")
        b.created_at = b.created_at.replace(tzinfo=timezone.utc)
        out = infer_places([b, asset("t", 0), asset("a", 5, TOKYO, "Tokyo", "Japan")])
        self.assertIn("t", out)


class ThroughTheClassifier(unittest.TestCase):
    def test_an_inferred_place_is_filed_and_says_it_was_inferred(self):
        from pvm.classifier import Classifier
        assets = [asset("b", -5, TOKYO, "Tokyo", "Japan"),
                  asset("t", 0),
                  asset("a", 5, TOKYO, "Tokyo", "Japan")]
        ctx = build_context(assets)
        c = Classifier(ctx).classify(assets[1])
        places = [x for x in c.assignments if x.path.startswith("Places")]
        self.assertEqual(len(places), 1)
        self.assertTrue(places[0].path.startswith("Places > Japan"))
        signals = {e.signal for e in places[0].evidence}
        self.assertIn("geo:inferred", signals)
        self.assertNotIn("geo", signals,
                         "a guess must not be able to look like a measurement")

    def test_an_inferred_place_is_never_the_primary_category(self):
        from pvm.classifier import Classifier
        assets = [asset("b", -5, TOKYO, "Tokyo", "Japan"),
                  asset("t", 0),
                  asset("a", 5, TOKYO, "Tokyo", "Japan")]
        ctx = build_context(assets)
        c = Classifier(ctx).classify(assets[1])
        for x in c.assignments:
            if x.path.startswith("Places"):
                self.assertFalse(x.is_primary)

    def test_a_measured_place_still_outweighs_an_inferred_one(self):
        from pvm.classifier import Classifier
        assets = [asset("b", -5, TOKYO, "Tokyo", "Japan"),
                  asset("t", 0),
                  asset("a", 5, TOKYO, "Tokyo", "Japan")]
        ctx = build_context(assets)
        cl = Classifier(ctx)
        measured = cl.classify(assets[0])
        inferred = cl.classify(assets[1])
        m = next(x for x in measured.assignments if x.path.startswith("Places"))
        i = next(x for x in inferred.assignments if x.path.startswith("Places"))
        self.assertGreater(m.confidence, i.confidence)

    def test_home_is_learned_from_measured_fixes_only(self):
        """An inferred place feeding the home cluster would be the system learning
        from its own guesses."""
        assets = [asset("b", -5, TOKYO, "Tokyo", "Japan"),
                  asset("t", 0),
                  asset("a", 5, TOKYO, "Tokyo", "Japan")]
        ctx = build_context(assets)
        self.assertEqual(ctx.home_sample_size, 1)   # one date, from the two anchors


class ThroughTheMemory(unittest.TestCase):
    def test_the_graph_marks_an_inferred_place_as_inferred(self):
        from pvm import memory
        from pvm.classifier import Classifier
        from pvm.signals import FaceCluster
        target = asset("t", 0)
        target.face_clusters = [FaceCluster(cluster_id="c1", name="Anna")]
        assets = [asset("b", -5, TOKYO, "Tokyo", "Japan"), target,
                  asset("a", 5, TOKYO, "Tokyo", "Japan")]
        ctx = build_context(assets)
        cl = Classifier(ctx)
        classifications = {x.asset_id: cl.classify(x) for x in assets}
        graph = memory.build(assets, classifications, ctx)
        seen = [o for o in graph.observations if o.asset_id == "t"]
        self.assertTrue(seen)
        for o in seen:
            self.assertEqual(o.place, "Tokyo")
            self.assertEqual(o.place_source, "inferred")
            self.assertTrue(o.place_is_inferred)


if __name__ == "__main__":
    unittest.main()
