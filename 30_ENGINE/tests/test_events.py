# -*- coding: utf-8 -*-
"""
§11: 时间 + 地点 + 人物 + 内容可以自动形成 Event / Trip 候选.

Trip was the only candidate the engine derived, so a Saturday in Brighton with twenty
photographs had no event at all and the only thing the library could say about it was
the date. These are the other two the metadata pass can support honestly.

Neither mints a browse folder. Travel is a run of days, and putting a Saturday afternoon
on that shelf beside a fortnight in Japan makes the shelf mean less — the first trip
detector already taught this project that lesson by producing 53 "trips" of two photos
each. They live in the memory graph, which is where §10's Relations path enters from.
"""

from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pvm import memory
from pvm.classifier import Classifier
from pvm.context import (MIN_DAY_OUT_ASSETS, MIN_GATHERING_ASSETS,
                         MIN_GATHERING_PEOPLE, build_context)
from pvm.signals import AssetSignals, FaceCluster, GeoFix, PlaceName

LONDON = (51.5074, -0.1278)
BRIGHTON = (50.8225, -0.1372)     # ~75 km from London... below AWAY_KM
EDINBURGH = (55.9533, -3.1883)    # ~530 km — unambiguously away


def shot(aid, when, coords=None, city=None, country=None, people=()):
    a = AssetSignals(aid)
    a.created_at, a.source = when, "camera"
    if coords:
        a.geo = GeoFix(lat=coords[0], lon=coords[1])
        a.place = PlaceName(country=country, city=city, confidence=0.9)
    a.face_clusters = [FaceCluster(f"c-{n.lower()}", n) for n in people]
    return a


def home_library(days=40):
    """Enough evening captures in London for home to be learned."""
    return [shot(f"home-{i}", datetime(2025, 1, 1, 21) + timedelta(days=i),
                 LONDON, "London", "United Kingdom") for i in range(days)]


class DaysOut(unittest.TestCase):
    def _library(self, count):
        out = home_library()
        base = datetime(2025, 6, 14, 11)
        for i in range(count):
            out.append(shot(f"out-{i}", base + timedelta(minutes=25 * i),
                            EDINBURGH, "Edinburgh", "United Kingdom"))
        return out

    def test_a_day_away_from_home_becomes_an_event(self):
        ctx = build_context(self._library(MIN_DAY_OUT_ASSETS))
        self.assertEqual(len(ctx.days_out), 1)
        day = ctx.days_out[0]
        self.assertEqual(day.city, "Edinburgh")
        self.assertEqual(day.asset_count, MIN_DAY_OUT_ASSETS)
        self.assertIn("Edinburgh", day.label)

    def test_a_couple_of_photographs_is_not_an_occasion(self):
        ctx = build_context(self._library(MIN_DAY_OUT_ASSETS - 1))
        self.assertEqual(ctx.days_out, [],
                         "the bar is high on purpose — the first trip detector "
                         "produced 53 trips of two photos each")

    def test_it_is_not_a_trip(self):
        ctx = build_context(self._library(MIN_DAY_OUT_ASSETS))
        self.assertEqual(ctx.trips, [],
                         "one day is not a run of days; calling it a trip would put a "
                         "Saturday on the same shelf as a fortnight in Japan")

    def test_days_inside_a_trip_are_not_surfaced_twice(self):
        out = home_library()
        for day in range(6):
            for i in range(6):
                out.append(shot(f"trip-{day}-{i}",
                                datetime(2025, 7, 1 + day, 10) + timedelta(minutes=25 * i),
                                EDINBURGH, "Edinburgh", "United Kingdom"))
        ctx = build_context(out)
        self.assertEqual(len(ctx.trips), 1)
        self.assertEqual(ctx.days_out, [],
                         "a day inside a trip is part of the trip; two events over the "
                         "same photographs makes both of them mean less")

    def test_nothing_is_derived_without_a_home_to_be_away_from(self):
        base = datetime(2025, 6, 14, 11)
        assets = [shot(f"out-{i}", base + timedelta(minutes=25 * i),
                       EDINBURGH, "Edinburgh", "United Kingdom")
                  for i in range(MIN_DAY_OUT_ASSETS)]
        ctx = build_context(assets)
        # With no home cluster, "away" has no meaning — and the detector must not
        # invent one by treating the only cluster as somewhere else.
        self.assertEqual(ctx.days_out, [])


class Gatherings(unittest.TestCase):
    def _session(self, count, people):
        base = datetime(2025, 9, 6, 15)
        return home_library() + [
            shot(f"party-{i}", base + timedelta(minutes=2 * i), people=people)
            for i in range(count)]

    def test_several_named_people_across_a_session(self):
        ctx = build_context(self._session(MIN_GATHERING_ASSETS, ("Anna", "Ben")))
        self.assertEqual(len(ctx.gatherings), 1)
        gathering = ctx.gatherings[0]
        self.assertEqual(gathering.people, ("Anna", "Ben"))
        self.assertIn("Anna", gathering.label)

    def test_one_photograph_of_two_people_is_not_an_occasion(self):
        ctx = build_context(self._session(MIN_GATHERING_ASSETS - 1, ("Anna", "Ben")))
        self.assertEqual(ctx.gatherings, [])

    def test_one_person_photographed_a_lot_is_not_a_gathering(self):
        ctx = build_context(self._session(20, ("Anna",)))
        self.assertEqual(ctx.gatherings, [],
                         f"a gathering needs {MIN_GATHERING_PEOPLE} named people")

    def test_unnamed_faces_do_not_count(self):
        """§16 forbids inferring anything further about an unidentified face —
        including that they were at an occasion together."""
        base = datetime(2025, 9, 6, 15)
        assets = home_library()
        for i in range(MIN_GATHERING_ASSETS):
            a = shot(f"party-{i}", base + timedelta(minutes=2 * i))
            a.face_clusters = [FaceCluster("c-1", None), FaceCluster("c-2", None)]
            assets.append(a)
        ctx = build_context(assets)
        self.assertEqual(ctx.gatherings, [])


class TheyReachTheMemoryGraph(unittest.TestCase):
    def _graph(self, assets):
        ctx = build_context(assets)
        cl = Classifier(ctx)
        classifications = {a.asset_id: cl.classify(a) for a in assets}
        return ctx, memory.build(assets, classifications, ctx)

    def test_a_gathering_is_an_event_entity_with_its_photos_attached(self):
        base = datetime(2025, 9, 6, 15)
        assets = home_library() + [
            shot(f"party-{i}", base + timedelta(minutes=2 * i), people=("Anna", "Ben"))
            for i in range(MIN_GATHERING_ASSETS)]
        ctx, graph = self._graph(assets)
        events = [e for e in graph.entities.values() if e.kind.value == "event"]
        self.assertTrue(any("Anna" in e.name for e in events),
                        f"gatherings {ctx.gatherings} did not become entities")
        event = next(e for e in events if "Anna" in e.name)
        seen = [o for o in graph.observations if o.entity_id == event.entity_id]
        self.assertEqual(len(seen), MIN_GATHERING_ASSETS)

    def test_an_event_says_why_it_is_believed_to_exist(self):
        base = datetime(2025, 9, 6, 15)
        assets = home_library() + [
            shot(f"party-{i}", base + timedelta(minutes=2 * i), people=("Anna", "Ben"))
            for i in range(MIN_GATHERING_ASSETS)]
        _, graph = self._graph(assets)
        for entity in graph.entities.values():
            self.assertTrue(entity.evidence,
                            f"{entity.name} exists with no account of why")

    def test_a_day_out_is_an_event_entity(self):
        base = datetime(2025, 6, 14, 11)
        assets = home_library() + [
            shot(f"out-{i}", base + timedelta(minutes=25 * i),
                 EDINBURGH, "Edinburgh", "United Kingdom")
            for i in range(MIN_DAY_OUT_ASSETS)]
        _, graph = self._graph(assets)
        events = [e for e in graph.entities.values() if e.kind.value == "event"]
        self.assertTrue(any("Edinburgh" in e.name for e in events))


if __name__ == "__main__":
    unittest.main()
