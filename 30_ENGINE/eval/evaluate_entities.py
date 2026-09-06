# -*- coding: utf-8 -*-
"""
GATE 2 EVALUATION — Tier 1-B's numbers.

    输出 Precision / Recall / F1、False Merge / False Split，Document 类别单独统计
    （这是风险最高的类别）。
    PASS 标准：Document 类别的 False Merge 率极低（错误合并证件/合同的代价远高于
    漏检），整体 Same-Entity 判断明显优于「靠用户自己肉眼分辨」。   — L2 Tier 1-B

Three things this report insists on, because each is a way the number could flatter:

* **UNCERTAIN is not an error and not a success.** The Constitution says low confidence
  goes to the Review Queue and nothing else. So it is counted in its own column, as
  review burden (§18), and never rounded into either side. A resolver that answered
  UNCERTAIN to everything would score zero false merges here and be visibly useless in
  the burden column — which is the point of showing both.
* **False Merge is reported for documents on its own line**, because that is the one
  Tier 1-B fails on.
* **The corpus is hand-built.** `eval/entity_pairs.py` says so at length; this report
  repeats it, because a scoreboard travels further than the file behind it.

    python evaluate_entities.py
    python evaluate_entities.py --selftest
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eval import entity_pairs                                  # noqa: E402
from pvm.classifier import Classifier                          # noqa: E402
from pvm.context import build_context                          # noqa: E402
from pvm.resolver import Verdict, resolve                      # noqa: E402


class Tally:
    def __init__(self):
        self.true_positive = 0     # truth same, called same
        self.true_negative = 0     # truth different, called different
        self.false_merge = 0       # truth different, called same  ← the expensive one
        self.false_split = 0       # truth same, called different
        self.review_same = 0       # truth same, called uncertain
        self.review_diff = 0       # truth different, called uncertain

    @property
    def n(self) -> int:
        return (self.true_positive + self.true_negative + self.false_merge
                + self.false_split + self.review_same + self.review_diff)

    @property
    def truth_same(self) -> int:
        return self.true_positive + self.false_split + self.review_same

    @property
    def truth_different(self) -> int:
        return self.true_negative + self.false_merge + self.review_diff

    @property
    def precision(self) -> float:
        called = self.true_positive + self.false_merge
        return self.true_positive / called if called else float("nan")

    @property
    def recall(self) -> float:
        """Against every truly-same pair — so a pair sent to review costs recall.
        It should: the user still had to do the work."""
        return self.true_positive / self.truth_same if self.truth_same else float("nan")

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        if p != p or r != r or (p + r) == 0:
            return float("nan")
        return 2 * p * r / (p + r)

    @property
    def false_merge_rate(self) -> float:
        return self.false_merge / self.truth_different if self.truth_different else float("nan")

    @property
    def false_split_rate(self) -> float:
        return self.false_split / self.truth_same if self.truth_same else float("nan")

    @property
    def review_rate(self) -> float:
        return (self.review_same + self.review_diff) / self.n if self.n else float("nan")


def _pct(x: float) -> str:
    return "—" if x != x else f"{x * 100:.1f}%"


def run() -> Tuple[Dict[str, Tally], List[str]]:
    pairs = entity_pairs.build()

    # Classify every asset first: the resolver dispatches on what the classifier
    # decided, so evaluating it against hand-assigned categories would be measuring a
    # resolver that will never exist.
    assets = [a for p in pairs for a in (p.a, p.b)]
    context = build_context(assets)
    classifier = Classifier(context)
    classifications = {a.asset_id: classifier.classify(a) for a in assets}

    by_category: Dict[str, Tally] = defaultdict(Tally)
    overall = Tally()
    hard = Tally()
    lines: List[str] = []

    for pair in pairs:
        r = resolve(pair.a, pair.b,
                    classifications[pair.a.asset_id], classifications[pair.b.asset_id])
        for tally in (by_category[pair.category], overall,
                      *( [hard] if pair.hard_negative else [] )):
            if r.verdict is Verdict.UNCERTAIN:
                if pair.same:
                    tally.review_same += 1
                else:
                    tally.review_diff += 1
            elif r.verdict is Verdict.SAME:
                if pair.same:
                    tally.true_positive += 1
                else:
                    tally.false_merge += 1
            else:
                if pair.same:
                    tally.false_split += 1
                else:
                    tally.true_negative += 1

        truth = "same" if pair.same else "different"
        mark = {"same": "MERGE", "different": "SPLIT", "uncertain": "REVIEW"}[r.verdict.value]
        wrong = ((r.verdict is Verdict.SAME and not pair.same)
                 or (r.verdict is Verdict.DIFFERENT and pair.same))
        flag = "  ✗ WRONG" if wrong else ""
        lines.append(
            f"| {pair.pair_id} | {pair.category} | {'yes' if pair.hard_negative else ''} "
            f"| {truth} | {mark}{flag} | {r.resolver} | {r.why()} |")

    by_category["ALL"] = overall
    by_category["hard negatives"] = hard
    return by_category, lines


def report() -> str:
    tallies, lines = run()
    out: List[str] = []
    w = out.append

    w("# Gate 2 — Category-Specific Entity Resolver\n")
    w("Generated by `eval/evaluate_entities.py`. **The corpus is hand-built.** The 10k")
    w("labelled library carries category labels and no same-entity labels, so there was")
    w("nothing to measure against; `eval/entity_pairs.py` constructs the pairs, hard")
    w("negatives included, and says why each is labelled as it is. These are cases a")
    w("person wrote down, not a sample of a real library — a resolver tuned until this")
    w("goes green is tuned to this file. Read it as evidence about the hard negatives,")
    w("not as a population estimate.\n")
    w(f"{entity_pairs.summary()}.\n")

    w("## Per category\n")
    w("| category | pairs | precision | recall | F1 | False Merge | False Split | to review |")
    w("|---|--:|--:|--:|--:|--:|--:|--:|")
    order = [k for k in ("document", "screenshot", "object", "photo") if k in tallies]
    for key in order + ["hard negatives", "ALL"]:
        t = tallies[key]
        if t.n == 0:
            continue
        w(f"| {key} | {t.n} | {_pct(t.precision)} | {_pct(t.recall)} | {_pct(t.f1)} "
          f"| {t.false_merge} ({_pct(t.false_merge_rate)}) "
          f"| {t.false_split} ({_pct(t.false_split_rate)}) | {_pct(t.review_rate)} |")

    doc = tallies.get("document")
    w("\n## The number Tier 1-B passes or fails on\n")
    if doc and doc.n:
        w(f"**Document False Merge: {doc.false_merge} of {doc.truth_different} "
          f"different-document pairs ({_pct(doc.false_merge_rate)}).**\n")
        w("Wrongly merging two people's ID cards costs far more than missing a match,")
        w("so the resolver is built to be asymmetric: a document merges on a shared")
        w("identifier or a shared holder, never on looking the same. The price is paid")
        w("in the review column, which is the trade Tier 1-B asks for.\n")
    else:
        w("No document pairs were scored — that is a broken run, not a pass.\n")

    w("## Every pair\n")
    w("| pair | category | hard | truth | verdict | resolver | why |")
    w("|---|---|---|---|---|---|---|")
    out.extend(lines)

    w("\n## What this does not measure\n")
    w("* Real libraries. Hand-built pairs cannot report a rate that transfers.")
    w("* Two views of one object. `obj-same-chair-other-angle` is labelled SAME and is")
    w("  expected to come back REVIEW: without a visual embedding nothing in this build")
    w("  joins two angles of one chair. Tier 1-B names embeddings for exactly this, and")
    w("  the pair is kept in the set so the gap shows up in the numbers rather than in")
    w("  a footnote.")
    w("* Whether the resolver beats a person doing it by eye — Tier 1-B's second PASS")
    w("  criterion needs users, which is T0-B.")
    return "\n".join(out)


def selftest() -> int:
    """Guard the guard. A scoreboard that cannot fail is not a measurement."""
    failures = []
    tallies, lines = run()

    if tallies["ALL"].n != len(entity_pairs.build()):
        failures.append("the tally lost pairs — every pair must land in exactly one cell")
    if not lines:
        failures.append("no pairs were scored; an empty report would print as a pass")
    if tallies["document"].n < 8:
        failures.append("too few document pairs to say anything about the risky category")
    if tallies["hard negatives"].n < 5:
        failures.append("too few hard negatives; the easy cases are not the test")

    # An always-UNCERTAIN resolver must not be able to score well.
    blind = Tally()
    blind.review_same, blind.review_diff = 5, 5
    if blind.recall == blind.recall and blind.recall > 0:
        failures.append("review must cost recall, or refusing to answer would score")
    if blind.false_merge_rate != 0.0:
        failures.append("an all-review resolver should show zero false merges — "
                        "which is why the review column has to be printed beside it")

    for f in failures:
        print(f"SELFTEST FAIL: {f}")
    print(f"selftest: {len(failures)} failure(s)")
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out", help="write the report here as well as to stdout")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    text = report()
    print(text)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
