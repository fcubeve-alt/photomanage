# -*- coding: utf-8 -*-
"""
Change-driven processing: what it saves, and the four ways it would lose data.

The saving is easy and the correctness is not, so most of this file is about the
frames that must NOT be skipped.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pvm.deltas import (CUT_BITS, Frame, MAX_SKIP_RUN, estimate_cost,  # noqa: E402
                        select_keyframes)
from pvm.signals import hamming                                        # noqa: E402


def sequence(n, drift_per_frame, cut_every=None, seed=0xC0FFEE):
    frames, h = [], seed
    for i in range(n):
        if cut_every and i and i % cut_every == 0:
            h ^= 0xFFFF0000FFFF0000
        else:
            for k in range(drift_per_frame):
                h ^= 1 << ((i * 7 + k * 13) % 64)
        frames.append(Frame(i, h & ((1 << 64) - 1), i / 30))
    return frames


def naive_pairwise(frames, drift_bits=8):
    """The rule as it is usually stated: compare each frame with the one before it.
    Kept here as the thing being argued against, so the argument is testable."""
    processed = [0]
    for i in range(1, len(frames)):
        if hamming(frames[i].dhash, frames[i - 1].dhash) >= drift_bits:
            processed.append(i)
    return processed


class ItSavesRealWork(unittest.TestCase):
    def test_a_static_shot_costs_almost_nothing(self):
        c = estimate_cost(select_keyframes(sequence(600, 0)))
        self.assertGreater(c.saved_fraction, 0.80)

    def test_a_moving_shot_still_saves_more_than_half(self):
        c = estimate_cost(select_keyframes(sequence(600, 3)))
        self.assertGreater(c.saved_fraction, 0.50)

    def test_the_gates_own_cost_is_counted_not_hidden(self):
        """Every frame still pays decode plus hash. A saving that ignores what the
        gate costs is not a measurement."""
        r = select_keyframes(sequence(600, 0))
        c = estimate_cost(r)
        self.assertGreater(c.delta_ms, 0)
        self.assertLess(c.saved_fraction, 1.0)


class DriftIsInvisiblePairwiseAndObviousCumulatively(unittest.TestCase):
    """The correction. Comparing each frame to the one before it fails on a slow pan:
    every adjacent pair looks the same, so nothing is processed, while the start and
    end of the sequence are different scenes."""

    def test_pairwise_comparison_sleeps_through_a_slow_pan(self):
        frames = sequence(600, 1)
        self.assertLessEqual(len(naive_pairwise(frames)), 2,
                             "the naive rule was expected to skip essentially everything")
        # ...and the sequence really did change end to end, so that is data loss.
        self.assertGreater(hamming(frames[0].dhash, frames[-1].dhash), CUT_BITS)

    def test_comparing_against_the_last_keyframe_catches_it(self):
        r = select_keyframes(sequence(600, 1))
        self.assertGreater(r.processed, 20)
        self.assertLess(r.processed, 200, "it should still be saving most of the work")

    def test_no_keyframe_is_ever_far_from_the_frames_it_stands_for(self):
        """The property that makes the saving safe: every skipped frame is within the
        drift threshold of the keyframe representing it."""
        frames = sequence(600, 1)
        r = select_keyframes(frames)
        by_index = {f.index: f for f in frames}
        current = None
        for d in r.decisions:
            if d.process:
                current = by_index[d.index]
                continue
            self.assertLess(hamming(by_index[d.index].dhash, current.dhash), CUT_BITS,
                            f"frame {d.index} was skipped but is a scene away from its keyframe")


class TheFramesThatMustNeverBeSkipped(unittest.TestCase):
    def test_a_document_sequence_is_processed_in_full(self):
        """Contract page 1 and page 2 look near-identical and say different things."""
        r = select_keyframes(sequence(200, 0), is_document=True)
        self.assertEqual(r.processed, r.total)

    def test_a_failed_hash_never_authorises_a_skip(self):
        """FC-1a: dHash returns 0 for a class of ordinary images AND for every
        failure, so a failure is indistinguishable from a perfect match — and a
        perfect match is exactly what would license skipping."""
        frames = [Frame(0, 0xABCD)] + [Frame(i, 0) for i in range(1, 50)]
        r = select_keyframes(frames)
        self.assertEqual(r.processed, r.total)

    def test_the_last_frame_is_always_looked_at(self):
        r = select_keyframes(sequence(600, 0))
        self.assertIn(599, r.keyframes)

    def test_a_scene_cut_is_never_skipped(self):
        frames = sequence(600, 0, cut_every=60)
        r = select_keyframes(frames)
        for cut in range(60, 600, 60):
            self.assertIn(cut, r.keyframes, f"the cut at frame {cut} was skipped")

    def test_drift_slower_than_the_threshold_is_still_sampled(self):
        """Insurance against a pan so slow it never crosses the threshold: the run cap
        forces a look regardless of what the hashes say."""
        flat = [Frame(i, 0xAAAABBBBCCCCDDDD) for i in range(400)]
        r = select_keyframes(flat)
        gaps = [b - a for a, b in zip(r.keyframes, r.keyframes[1:])]
        self.assertTrue(gaps)
        self.assertLessEqual(max(gaps), MAX_SKIP_RUN + 1)


class Edges(unittest.TestCase):
    def test_an_empty_sequence_is_not_a_crash(self):
        r = select_keyframes([])
        self.assertEqual(r.total, 0)
        self.assertEqual(r.processed_fraction, 0.0)

    def test_a_single_frame_is_processed(self):
        r = select_keyframes([Frame(0, 0x1234)])
        self.assertEqual(r.processed, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
