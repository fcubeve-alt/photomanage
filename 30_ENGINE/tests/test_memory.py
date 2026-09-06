# -*- coding: utf-8 -*-
"""
Tests for the visual memory graph.

§2 lists Remember among the ten things the product *is*, and §15 builds every later
service on top of it. Filing a photo on a shelf is not remembering it; the graph is
what lets the library answer L1-B's own worked example — *"我的红色行李箱最后在哪里
出现过？"* — instead of only "you have some objects".

So these tests are mostly about what the graph is **not allowed to claim**. A memory
that overstates is worse than no memory: it is a confident wrong answer about the
user's own life, which is the failure §11 and §16 exist to prevent.

    python -m unittest discover -s tests -v
"""

import os
import sys
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pvm import fixture, memory                                         # noqa: E402
from pvm.classifier import Classifier                                   # noqa: E402
from pvm.context import build_context                                   # noqa: E402
from pvm.memory import (Entity, EntityKind, MemoryGraph, Observation,   # noqa: E402
                        VideoMemoryRecord, video_record)
from pvm.signals import (AssetSignals, FaceCluster, GeoFix, PlaceName,  # noqa: E402
                         SceneLabel, Tier)
from pvm.verdict import Evidence                                        # noqa: E402

LONDON = GeoFix(51.5074, -0.1278)
TOKYO = GeoFix(35.6762, 139.6503)
UK_LONDON = PlaceName("United Kingdom", "London", 0.9)
JP_TOKYO = PlaceName("Japan", "Tokyo", 0.9)


def asset(aid, when=None, **kw) -> AssetSignals:
    a = AssetSignals(aid, created_at=when or datetime(2025, 6, 18, 14), **kw)
    a.pixel_w, a.pixel_h, a.byte_size = 4032, 3024, 500_000
    a.content_hash = f"sha::{aid}"
    return a


def graph_of(assets):
    ctx = build_context(assets)
    clf = Classifier(ctx)
    return memory.build(assets, {a.asset_id: clf.classify(a) for a in assets}, ctx)


class EvidenceIsMandatory(unittest.TestCase):
    """§10's red line, applied to entities. A thing the library claims exists has to
    be able to say why it thinks so — otherwise it is an assertion, not a memory."""

    def test_entity_without_evidence_cannot_be_built(self):
        with self.assertRaises(ValueError):
            Entity("person:nobody", EntityKind.PERSON, "Nobody")

    def test_every_entity_the_builder_produces_can_explain_itself(self):
        g = graph_of(fixture.build())
        self.assertTrue(g.entities, "the fixture must produce entities at all")
        for entity in g.entities.values():
            self.assertTrue(entity.evidence, f"{entity.entity_id} has no evidence")
            self.assertTrue(entity.why().strip(), f"{entity.entity_id} explains nothing")
            self.assertGreater(entity.confidence, 0.0)

    def test_every_observation_carries_a_reason(self):
        g = graph_of(fixture.build())
        self.assertTrue(g.observations)
        for o in g.observations:
            self.assertTrue(o.reason.strip(), f"{o.entity_id}@{o.asset_id} has no reason")


class PeopleAndPlaces(unittest.TestCase):

    def test_named_faces_become_people_and_unnamed_ones_do_not(self):
        g = graph_of([
            asset("p1", face_clusters=[FaceCluster("c-anna", "Anna")]),
            asset("p2", face_clusters=[FaceCluster("c-unknown", None)]),
        ])
        people = [e.name for e in g.entities.values() if e.kind == EntityKind.PERSON]
        self.assertEqual(["Anna"], people,
                         "an unnamed cluster is a face, not a person the user has named")

    def test_a_gps_place_is_measured_and_an_inferred_one_says_so(self):
        measured = graph_of([asset("m", geo=GeoFix(LONDON.lat, LONDON.lon, source="exif"),
                                   place=UK_LONDON)])
        inferred = graph_of([asset("i", geo=GeoFix(LONDON.lat, LONDON.lon, source="inferred"),
                                   place=UK_LONDON)])
        self.assertFalse(measured.observations[0].is_inferred)
        self.assertTrue(all(o.is_inferred for o in inferred.observations),
                        "§11: a place derived from neighbours must not look like a fix")

    def test_the_answer_shows_the_hedge_when_the_place_was_inferred(self):
        g = graph_of([asset("i", face_clusters=[FaceCluster("c", "Anna")],
                            geo=GeoFix(LONDON.lat, LONDON.lon, source="inferred"), place=UK_LONDON)])
        answer = g.answer_where_last_seen("Anna")
        self.assertIn("inferred", answer,
                      "an inference dressed as a measurement is the failure §11 names")


class ObjectsAreNamedByWhatWasRecognised(unittest.TestCase):
    """The point of keeping a memory separate from the catalogue.

    `Objects` is not an extensible root and its leaves are coarse. A suitcase files
    under `Objects > Other` — a shelf that names nothing. The entity must still be a
    *suitcase*, or the worked example below has no chance of working.
    """

    def test_a_suitcase_is_a_suitcase_even_though_the_shelf_is_other(self):
        g = graph_of([asset("s", scene_labels=[SceneLabel("suitcase", 0.8)])])
        objects = [e for e in g.entities.values() if e.kind == EntityKind.OBJECT]
        self.assertEqual(1, len(objects))
        self.assertEqual("Suitcase", objects[0].name)
        self.assertEqual("Objects > Other", objects[0].category_path,
                         "the coarse shelf is kept, not hidden — both are true")

    def test_no_entity_is_ever_called_other(self):
        g = graph_of(fixture.build() + [asset("obj", scene_labels=[])])
        for entity in g.entities.values():
            self.assertNotIn(entity.name.lower(), ("other", "other documents"),
                             "a shelf named Other names nothing; it cannot be an entity")

    def test_the_worked_example_from_L1B(self):
        """*"我的红色行李箱最后在哪里出现过？"* — and the honest half of the answer."""
        g = graph_of([
            asset("t1", when=datetime(2025, 4, 11, 10), geo=TOKYO, place=JP_TOKYO,
                  scene_labels=[SceneLabel("suitcase", 0.8)]),
            asset("t2", when=datetime(2025, 4, 19, 18), geo=LONDON, place=UK_LONDON,
                  scene_labels=[SceneLabel("suitcase", 0.8)]),
        ])
        answer = g.answer_where_last_seen("my red suitcase")

        # The part it can answer: when, and where.
        self.assertIn("19 April 2025", answer)
        self.assertIn("London", answer)
        # The part it must not pretend to answer. Per-category entity resolution
        # (§24 Gate 2) is not built, so "red" is a word the library cannot act on and
        # has to admit to rather than silently drop.
        self.assertIn("red", answer)
        self.assertIn("may not be yours", answer)

    def test_a_full_match_carries_no_spurious_caveat(self):
        g = graph_of([asset("s", scene_labels=[SceneLabel("suitcase", 0.8)],
                            geo=LONDON, place=UK_LONDON)])
        self.assertNotIn("may not be yours", g.answer_where_last_seen("suitcase"))

    def test_nothing_known_is_said_plainly(self):
        g = graph_of([asset("a", geo=LONDON, place=UK_LONDON)])
        self.assertIn("Nothing in the library",
                      g.answer_where_last_seen("my grandmother's ring"))


class DocumentsAndPurchases(unittest.TestCase):

    def test_a_passport_photo_is_evidence_about_a_passport(self):
        g = graph_of([asset("d", ocr_ran=True, ocr_text="PASSPORT",
                            geo=LONDON, place=UK_LONDON)])
        docs = [e.name for e in g.entities.values() if e.kind == EntityKind.DOCUMENT]
        self.assertIn("Passport", docs,
                      "singular: one photo shows one passport, not a shelf of them")

    def test_a_receipt_and_its_order_confirmation_are_one_purchase(self):
        """§15 Purchase & Warranty Memory. Two documents, one thing you own."""
        g = graph_of([
            asset("r", when=datetime(2026, 3, 15), ocr_ran=True,
                  ocr_text="RECEIPT — HEADPHONES £129.00"),
            asset("o", when=datetime(2026, 3, 14), is_screenshot=True, source="screenshot",
                  ocr_ran=True, ocr_text="ORDER CONFIRMATION — HEADPHONES"),
        ])
        purchases = [e for e in g.entities.values() if e.kind == EntityKind.PURCHASE]
        self.assertEqual(1, len(purchases), "one purchase, evidenced twice")
        self.assertEqual("Headphones", purchases[0].name)
        self.assertEqual(2, len(g.history(purchases[0].entity_id)))

    def test_a_receipt_that_names_nothing_stays_a_receipt(self):
        g = graph_of([asset("r", ocr_ran=True, ocr_text="RECEIPT 14.02.2026 TOTAL 9.99")])
        purchases = [e.name for e in g.entities.values() if e.kind == EntityKind.PURCHASE]
        self.assertEqual(["Purchase"], purchases,
                         "inventing a product name out of a total is exactly the "
                         "confident guess §11 forbids")


class TripsBecomeEvents(unittest.TestCase):

    def test_a_trip_in_the_context_becomes_an_event_with_its_photos(self):
        g = graph_of(fixture.build())
        events = [e for e in g.entities.values() if e.kind == EntityKind.EVENT]
        self.assertEqual(1, len(events), "the fixture contains exactly one trip")
        self.assertIn("Tokyo", events[0].name)
        self.assertGreaterEqual(len(g.history(events[0].entity_id)), 12,
                                "§11: the user should never build a travel album by hand")


class NoRelationshipInference(unittest.TestCase):
    """§15 and §16. The graph may record that two people appear together. It may not
    conclude what they are to each other, and it never characterises anyone."""

    def test_co_occurrence_is_a_count_and_nothing_more(self):
        g = graph_of(fixture.build())
        pairs = g.co_occurring("person:anna", kind=EntityKind.PERSON)
        self.assertEqual([("person:ben", 1)], pairs)
        for _, value in pairs:
            self.assertIsInstance(value, int,
                                  "a count is an observation; a label would be a claim")

    def test_the_graph_has_no_kind_for_a_relationship(self):
        kinds = {k.value for k in EntityKind}
        for forbidden in ("relationship", "partner", "family", "friend", "colleague"):
            self.assertNotIn(forbidden, kinds)


class HistoryAndOrdering(unittest.TestCase):

    def test_history_is_oldest_first_and_undated_sightings_survive(self):
        g = MemoryGraph()
        e = Evidence("scene_labels", Tier.VISUAL, 0.7, "a suitcase was recognised")
        g.add_entity(Entity("object:suitcase", EntityKind.OBJECT, "Suitcase", [e]))
        for when in (datetime(2025, 5, 1), None, datetime(2024, 1, 1)):
            g.observe(Observation("object:suitcase", f"a{when}", when, None, 0.7, "seen"))

        history = g.history("object:suitcase")
        self.assertEqual(3, len(history), "an undated sighting is still a sighting")
        self.assertEqual(datetime(2024, 1, 1), history[0].when)
        self.assertIsNone(history[-1].when)

    def test_an_entity_with_no_dated_sighting_has_no_last(self):
        g = MemoryGraph()
        e = Evidence("scene_labels", Tier.VISUAL, 0.7, "recognised")
        g.add_entity(Entity("object:suitcase", EntityKind.OBJECT, "Suitcase", [e]))
        g.observe(Observation("object:suitcase", "a", None, None, 0.7, "seen"))
        self.assertIsNone(g.last_seen("object:suitcase"))
        self.assertIn("no “last”", g.answer_where_last_seen("suitcase"))


class RepeatsAreFlaggedNotCollapsed(unittest.TestCase):
    """Two photos of one thing in one moment say one thing twice. Two photos of one
    thing on two days say two things — and collapsing those would delete the only
    information the memory exists to hold."""

    def test_a_repeat_within_a_moment_is_flagged_and_nothing_is_dropped(self):
        base = datetime(2025, 6, 18, 14, 0, 0)
        assets = [
            asset("card-a", when=base, ocr_ran=True, ocr_text="ID CARD"),
            asset("card-b", when=base + timedelta(seconds=3), ocr_ran=True,
                  ocr_text="ID CARD"),
        ]
        ctx = build_context(assets)
        clf = Classifier(ctx)
        cs = {a.asset_id: clf.classify(a) for a in assets}
        g = memory.build(assets, cs, ctx, moment_groups=[["card-a", "card-b"]])

        self.assertEqual({"card-a", "card-b"}, {o.asset_id for o in g.observations},
                         "no sighting is dropped — a flag is not a deletion")
        repeats = [o for o in g.observations if o.repeats]
        self.assertTrue(repeats)
        self.assertTrue(all(o.asset_id == "card-b" for o in repeats),
                        "the earliest member is the anchor, not a repeat of itself")
        self.assertTrue(all(o.repeats == "card-a" for o in repeats))

    def test_two_occasions_are_two_sightings_not_a_repeat(self):
        """The bug this replaced: dedup's `same_entity` groups photos of one subject
        taken *on different occasions*, and feeding those in marked the second visit as
        a duplicate of the first. In a memory that is the opposite of true."""
        g = graph_of([
            asset("a1", when=datetime(2025, 8, 3), geo=LONDON, place=UK_LONDON,
                  face_clusters=[FaceCluster("c-anna", "Anna")]),
            asset("a2", when=datetime(2025, 8, 11), geo=TOKYO, place=JP_TOKYO,
                  face_clusters=[FaceCluster("c-anna", "Anna")]),
        ])
        history = g.history("person:anna")
        self.assertEqual(2, len(history))
        self.assertTrue(all(o.repeats is None for o in history))
        self.assertIn("Tokyo", g.answer_where_last_seen("Anna"))

    def test_the_pipeline_does_not_mark_separate_occasions_as_repeats(self):
        """End to end, through the real relation groups rather than a hand-built one."""
        from pvm.catalog import Catalog
        catalog = Catalog(":memory:")
        try:
            memory_pipeline = __import__("pvm.pipeline", fromlist=["run"])
            memory_pipeline.run(fixture.build(), catalog)
            flagged = catalog.db.execute(
                """SELECT o.asset_id FROM observations o
                   WHERE o.entity_id='person:anna' AND o.reason LIKE '%again%'""").fetchall()
            self.assertEqual([], flagged,
                             "photos of Anna days apart are separate sightings")
        finally:
            catalog.close()


class VideoLeavesARecordNotFrames(unittest.TestCase):
    """L1-B §4: what a video must leave behind is *"这个视频对用户个人视觉记忆真正贡献
    的新信息"* — Date / Place / Person / Object / Event / segment / frames."""

    def video(self):
        a = asset("v", when=datetime(2025, 4, 12, 9), geo=TOKYO, place=JP_TOKYO,
                  media_type="video", duration_s=60.0)
        a.face_clusters = [FaceCluster("c-anna", "Anna")]
        return a

    def test_runs_of_keyframes_become_segments_not_timestamps(self):
        record = video_record(self.video(), [0, 1, 2, 90, 91], frame_rate=30.0)
        self.assertEqual([(0.0, 2 / 30.0), (3.0, 91 / 30.0)], record.segments,
                         "two things happened, not five frames were interesting")

    def test_a_single_keyframe_is_a_zero_length_segment_not_a_crash(self):
        record = video_record(self.video(), [45], frame_rate=30.0)
        self.assertEqual([(1.5, 1.5)], record.segments)

    def test_no_keyframes_means_no_segments(self):
        record = video_record(self.video(), [], frame_rate=30.0)
        self.assertEqual([], record.segments)
        self.assertEqual([], record.representative_frames)

    def test_the_record_carries_every_field_L1B_asks_for(self):
        assets = [self.video()]
        ctx = build_context(assets)
        record = video_record(self.video(), [0, 1, 2], frame_rate=30.0, context=ctx)
        self.assertIsInstance(record, VideoMemoryRecord)
        summary = record.summary()
        for field_name in ("Date:", "Place:", "Person:", "Representative frames:"):
            self.assertIn(field_name, summary)
        self.assertIn("Anna", summary)
        self.assertIn("Tokyo", summary)

    def test_the_record_says_how_much_of_the_video_it_skipped(self):
        record = video_record(self.video(), [0, 1, 2], frame_rate=30.0)
        self.assertTrue(record.evidence)
        self.assertIn("repeated", record.evidence[0].reason,
                      "the saving is part of the record, not a hidden optimisation")


class Determinism(unittest.TestCase):

    def test_building_the_same_library_twice_gives_the_same_memory(self):
        assets = fixture.build()
        first, second = graph_of(assets), graph_of(assets)
        self.assertEqual(first.stats(), second.stats())
        self.assertEqual(sorted(first.entities), sorted(second.entities))


if __name__ == "__main__":
    unittest.main(verbosity=2)
