# -*- coding: utf-8 -*-
"""
Persistence tests — incrementality, checkpointing and resume.

The classifier will run in the same hostile place the indexer does: a phone, in the
background, being killed. These tests are about what survives that, and they set the
same bar C-3 sets for the indexer — a resume must reprocess at most one batch.
"""

import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pvm import pipeline                                     # noqa: E402
from pvm.catalog import BATCH, Catalog, signals_fingerprint  # noqa: E402
from pvm.risk import Risk                                    # noqa: E402
from pvm.signals import AssetSignals, GeoFix, PlaceName      # noqa: E402

LONDON = GeoFix(51.5074, -0.1278)
UK = PlaceName("United Kingdom", "London", 0.9)


def library(n: int):
    return [AssetSignals(f"a{i:05d}",
                         created_at=datetime(2025, 1, 1) + timedelta(hours=i),
                         geo=LONDON, place=UK, content_hash=f"h{i}", dhash=1000 + i)
            for i in range(n)]


class CatalogTestCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "c.sqlite")

    def open(self):
        return Catalog(self.path)


class Incrementality(CatalogTestCase):
    """A4, in the catalogue rather than the index: unchanged assets must not be redone,
    and changed ones must not be missed."""

    def test_a_second_run_over_an_unchanged_library_does_no_work(self):
        assets = library(50)
        c = self.open()
        first = pipeline.run(assets, c)
        c.close()
        self.assertEqual(first.classified, 50)

        c = self.open()
        second = pipeline.run(assets, c)
        c.close()
        self.assertEqual(second.classified, 0)
        self.assertEqual(second.skipped_unchanged, 50)

    def test_an_asset_whose_signals_changed_is_reclassified(self):
        assets = library(20)
        c = self.open(); pipeline.run(assets, c); c.close()

        assets[3].ocr_ran = True
        assets[3].ocr_text = "PASSPORT"
        c = self.open()
        stats = pipeline.run(assets, c)
        paths = [r[0] for r in c.db.execute(
            "SELECT path FROM assignments WHERE asset_id=?", ("a00003",))]
        c.close()
        self.assertEqual(stats.classified, 1)
        self.assertIn("Documents > Identity > Passports", paths)

    def test_changing_a_rule_reclassifies_the_library_with_no_flag_to_remember(self):
        """The engine fingerprint is part of every row. A rule change makes every
        conclusion stale by definition, which is the only version of this that stays
        correct when somebody forgets to pass --force."""
        assets = library(10)
        c = self.open(); pipeline.run(assets, c); c.close()

        c = self.open()
        c._engine = "pretend-the-rules-changed"
        stats = pipeline.run(assets, c)
        c.close()
        self.assertEqual(stats.classified, 10)

    def test_a_deleted_asset_drops_out_of_the_catalogue(self):
        assets = library(30)
        c = self.open(); pipeline.run(assets, c); c.close()

        c = self.open()
        stats = pipeline.run(assets[:25], c)
        remaining = c.stats()["assets"]
        c.close()
        self.assertEqual(stats.forgotten, 5)
        self.assertEqual(remaining, 25)

    def test_the_fingerprint_moves_when_the_text_does_and_not_otherwise(self):
        a = library(1)[0]
        before = signals_fingerprint(a)
        self.assertEqual(before, signals_fingerprint(a))
        a.ocr_text = "RECEIPT"
        self.assertNotEqual(before, signals_fingerprint(a))


class InterruptAndResume(CatalogTestCase):
    def test_a_kill_mid_run_costs_at_most_one_checkpoint_batch(self):
        """C-3 / Playbook E-07. Anything above one batch means the checkpointing is too
        coarse — the same bar `assets_reprocessed_after_resume` sets for the indexer."""
        assets = library(BATCH * 3 + 40)

        class Killed(Exception):
            pass

        c = self.open()
        killed_after = BATCH * 2 + 90
        original = c.upsert
        count = {"n": 0}

        def upsert_then_die(asset, cls, risk, proposal):
            original(asset, cls, risk, proposal)
            count["n"] += 1
            if count["n"] >= killed_after:
                raise Killed()

        c.upsert = upsert_then_die
        with self.assertRaises(Killed):
            pipeline.run(assets, c)
        survived = c.stats()["assets"]
        c.close()

        # Only committed batches survive; the partial batch is rolled back.
        self.assertGreaterEqual(survived, BATCH * 2)
        self.assertLess(survived, killed_after + BATCH)

        c = self.open()
        resumed = pipeline.run(assets, c)
        c.close()
        redone = resumed.classified - (len(assets) - survived)
        self.assertLessEqual(redone, BATCH,
                             f"resume reprocessed {redone} assets; the budget is one batch of {BATCH}")

    def test_the_cursor_never_points_past_committed_work(self):
        assets = library(BATCH + 10)
        c = self.open()
        pipeline.run(assets, c)
        cursor = c.cursor
        known = c.known_ids()
        c.close()
        self.assertIn(cursor, known)


class WhatTheCatalogueOwes(CatalogTestCase):
    def test_the_stored_reason_is_the_reason_that_was_used(self):
        assets = library(5)
        assets[0].ocr_ran = True
        assets[0].ocr_text = "VERIFICATION CODE 4417"
        assets[0].is_screenshot = True
        c = self.open(); pipeline.run(assets, c)
        why = c.why("a00000")
        c.close()
        self.assertTrue(why)
        joined = " ".join(r for rs in why.values() for r in rs)
        self.assertIn("verification code", joined)

    def test_no_assignment_is_ever_written_without_its_evidence(self):
        c = self.open(); pipeline.run(library(60), c)
        orphans = c.db.execute(
            """SELECT COUNT(*) FROM assignments a
               WHERE NOT EXISTS (SELECT 1 FROM evidence e
                                 WHERE e.asset_id=a.asset_id AND e.path=a.path)""").fetchone()[0]
        c.close()
        self.assertEqual(orphans, 0)

    def test_nothing_protected_is_ever_written_as_removable(self):
        assets = library(40)
        assets[1].ocr_ran = True
        assets[1].ocr_text = "PASSPORT"
        c = self.open(); pipeline.run(assets, c)
        bad = c.db.execute(
            "SELECT COUNT(*) FROM proposals WHERE risk>=? AND action='propose_remove'",
            (int(Risk.R4_PEOPLE),)).fetchone()[0]
        c.close()
        self.assertEqual(bad, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
