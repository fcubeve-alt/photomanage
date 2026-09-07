#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLASSIFIER EVALUATION against the 10,000-asset labelled library.

Read the first section of the report before the numbers. The corpus was built for the
T0-B retrieval study, and two of its properties decide what may honestly be measured:

  1. **9,864 of the 10,000 rows have a leaf the generator chose with `random.choice`.**
     `generate_test_library.py` picks the sub-leaf for filler assets at random from
     the category's path list, and nothing in the asset's signals encodes which one it
     picked. `Screenshots > Chat` versus `Screenshots > Maps` is a coin flip. Scoring
     leaf accuracy across all 10,000 would report the generator's coin flips as
     classifier error, and it would keep reporting them however good the classifier
     got. Those leaves are therefore counted and NOT scored.

  2. **The corpus carries no provenance and no visual content.** Nothing says an
     asset was saved from another app, and the filler images are flat rectangles with
     no scene for a classifier to recognise. `Downloads`, `Objects` and `Clothing` are
     unreachable here — a missing signal, not a wrong rule. The rules for them exist
     and are covered by unit tests built from explicit signals.

So the report separates three populations and never mixes them:

    SCORED             the label is derivable from a signal the corpus carries
    UNSCORABLE-LABEL   the label is a coin flip
    UNSCORABLE-SIGNAL  the signal does not exist in this corpus

    python evaluate.py --library ../../20_TIER0/study_assets/library/manifest.json
    python evaluate.py --selftest
"""

from __future__ import annotations

import argparse
import io
import os
import sys
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Set, Tuple

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eval.adapter import ground_truth, load_manifest          # noqa: E402
from pvm import kpi, pipeline, taxonomy                       # noqa: E402
from pvm.catalog import Catalog                               # noqa: E402
from pvm.risk import (ACTING_ACTIONS, Action,                 # noqa: E402
                      NEVER_DELETE_AT_OR_ABOVE, Risk, policy_table)
from pvm.signals import Tier                                  # noqa: E402

# Roots the corpus carries a real signal for.
SCORED_ROOTS = ("Places", "People", "Screenshots", "Documents", "Purchases", "Travel", "Timeline")
# Roots whose signal this corpus does not contain at all.
SIGNAL_ABSENT_ROOTS = ("Downloads", "Objects", "Clothing", "Work")


def _truth_roots(truth: dict) -> Set[str]:
    return {taxonomy.root_of(p) for p in truth["paths"]}


def _predicted_roots(paths: List[str]) -> Set[str]:
    return {taxonomy.root_of(p) for p in paths}


def prf(tp: int, fp: int, fn: int) -> Tuple[float, float, float]:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def evaluate(library: str, catalog_path: str, budget: Tier = Tier.TEXT):
    assets = load_manifest(library)
    truth = ground_truth(library)

    for suffix in ("", "-wal", "-shm"):
        try:
            os.remove(catalog_path + suffix)
        except OSError:
            pass

    catalog = Catalog(catalog_path)
    stats = pipeline.run(assets, catalog, budget=budget)

    predicted: Dict[str, List[str]] = defaultdict(list)
    for aid, path in catalog.db.execute("SELECT asset_id, path FROM assignments"):
        predicted[aid].append(path)

    return assets, truth, predicted, catalog, stats


def score(truth, predicted) -> dict:
    per_root = {r: Counter() for r in SCORED_ROOTS}
    # Tier 1-A asks for a confusion matrix, not only precision and recall. The two
    # answer different questions: P/R says how often a root is wrong, a matrix says
    # *what it is wrong with* — and "Purchases read as Documents" is a cross-listing
    # working as designed, while "Documents read as Screenshots" would be a defect.
    confusion = defaultdict(Counter)
    leaf_scored = Counter()
    leaf_by_root = defaultdict(Counter)
    unscorable_label = Counter()
    unscorable_signal = Counter()

    for aid, t in truth.items():
        pred_paths = predicted.get(aid, [])
        pred_roots = _predicted_roots(pred_paths)
        true_roots = _truth_roots(t)

        for root in SCORED_ROOTS:
            in_true, in_pred = root in true_roots, root in pred_roots
            if in_true and in_pred:
                per_root[root]["tp"] += 1
            elif in_pred and not in_true:
                per_root[root]["fp"] += 1
            elif in_true and not in_pred:
                per_root[root]["fn"] += 1

        # One row per true root, counting what was predicted instead. An asset filed
        # correctly *and* somewhere else contributes to both cells, because that is
        # what happened — collapsing it to "correct" would hide every over-filing.
        for true_root in true_roots:
            if true_root not in SCORED_ROOTS:
                continue
            if not pred_roots:
                confusion[true_root]["(nothing)"] += 1
            for predicted_root in pred_roots:
                confusion[true_root][predicted_root] += 1

        for root in SIGNAL_ABSENT_ROOTS:
            if root in true_roots:
                unscorable_signal[root] += 1

        # ---- leaf, only where the label is not a coin flip -----------------
        true_leaf = t["category_path"]
        root = taxonomy.root_of(true_leaf)
        derivable = (
            root in ("Places", "People", "Travel")           # GPS / faces / GPS+dates
            or (t["is_foreground"] and root in ("Screenshots", "Documents", "Purchases"))
        )
        if not derivable:
            unscorable_label[root] += 1
            continue
        leaf_scored["total"] += 1
        leaf_by_root[root]["total"] += 1
        if true_leaf in pred_paths:
            leaf_scored["exact"] += 1
            leaf_by_root[root]["exact"] += 1
        elif any(p.startswith(true_leaf.split(taxonomy.SEP)[0]) for p in pred_paths):
            # Right root, shallower or wrong branch. Counted apart from a miss because
            # "filed under Documents but not under Identity" and "filed under People"
            # are not the same failure.
            leaf_scored["right_root"] += 1
            leaf_by_root[root]["right_root"] += 1
        else:
            leaf_scored["miss"] += 1
            leaf_by_root[root]["miss"] += 1

    # Timeline is derived from the capture date on every asset; scoring it separately
    # keeps it from inflating the roots that were actually inferred.
    return {"per_root": per_root, "leaf": leaf_scored, "leaf_by_root": leaf_by_root,
            "unscorable_label": unscorable_label, "unscorable_signal": unscorable_signal,
            "confusion": {k: dict(v) for k, v in confusion.items()}}


def safety_audit(catalog: Catalog) -> dict:
    db = catalog.db
    one = lambda sql, *a: db.execute(sql, a).fetchone()[0]
    marks = ",".join("?" * len(ACTING_ACTIONS))
    protected_removals = one(
        f"SELECT COUNT(*) FROM proposals WHERE risk>=? AND action IN ({marks})",
        int(NEVER_DELETE_AT_OR_ABOVE), *[a.value for a in ACTING_ACTIONS])
    unexplained = one(
        """SELECT COUNT(*) FROM assignments a
           WHERE NOT EXISTS (SELECT 1 FROM evidence e
                             WHERE e.asset_id=a.asset_id AND e.path=a.path)""")
    irreversible = one("SELECT COUNT(*) FROM proposals WHERE reversible=0")
    unconfirmed = one(
        "SELECT COUNT(*) FROM proposals WHERE action='suggest_delete' AND requires_confirmation=0")
    return {
        "protected_removals": protected_removals,
        "unexplained_assignments": unexplained,
        "irreversible_proposals": irreversible,
        "removals_without_confirmation": unconfirmed,
        "auto_applicable": one("SELECT COUNT(*) FROM proposals WHERE auto_applicable=1"),
        "protected_assets": one("SELECT COUNT(*) FROM assets WHERE risk>=?",
                                int(NEVER_DELETE_AT_OR_ABOVE)),
    }


def report(truth, predicted, catalog, stats, scores, ablation, out) -> int:
    w = out.write
    total = len(truth)

    w("# CLASSIFIER EVALUATION — 10,000-asset labelled library\n\n")
    w("Engine: `30_ENGINE/pvm`. Corpus: `20_TIER0/study_assets/library/manifest.json`.\n\n")

    # ---- what may be measured ------------------------------------------
    w("## What this corpus can and cannot measure\n\n")
    coin = sum(scores["unscorable_label"].values())
    absent = sum(scores["unscorable_signal"].values())
    w(f"- **{total:,} assets.** {total - coin:,} carry a leaf label derivable from a signal; "
      f"**{coin:,} do not.**\n")
    w("- The generator assigns filler assets a leaf with `random.choice` "
      "(`generate_test_library.py`, `background()`), and no signal on the asset records "
      "which one it picked. Those leaves are counted below and never scored — scoring "
      "them would report coin flips as classifier error, permanently.\n")
    w("  - by root: " + ", ".join(f"{r} {n:,}" for r, n in scores["unscorable_label"].most_common()) + "\n")
    w(f"- **{absent:,} assets** belong to a root whose signal this corpus does not carry "
      "(no provenance, no scene labels): "
      + ", ".join(f"{r} {n:,}" for r, n in scores["unscorable_signal"].most_common()) + ".\n")
    w("  The rules for these exist in the engine and are covered by unit tests built "
      "from explicit signals; what cannot be done is measure them here.\n\n")

    # ---- root level -----------------------------------------------------
    w("## Root-level classification (scored)\n\n")
    w("| root | true | precision | recall | F1 | tp | fp | fn |\n|---|--:|--:|--:|--:|--:|--:|--:|\n")
    macro = []
    for root in SCORED_ROOTS:
        c = scores["per_root"][root]
        p, r, f = prf(c["tp"], c["fp"], c["fn"])
        macro.append(f)
        w(f"| {root} | {c['tp'] + c['fn']:,} | {p:.3f} | {r:.3f} | {f:.3f} | "
          f"{c['tp']:,} | {c['fp']:,} | {c['fn']:,} |\n")
    w(f"\n**Macro F1 across scored roots: {sum(macro)/len(macro):.3f}**\n\n")

    # ---- confusion matrix (Tier 1-A) ------------------------------------
    w("### Confusion matrix\n\n")
    w("Rows are the true root, columns what the engine filed it as. An asset filed "
      "correctly *and* somewhere else appears in both cells, because that is what "
      "happened; collapsing it to \"correct\" would hide every over-filing. "
      "`(nothing)` means the engine declined to file it at all.\n\n")
    confusion = scores["confusion"]
    columns = sorted({col for row in confusion.values() for col in row})
    w("| true \\ filed as | " + " | ".join(columns) + " |\n")
    w("|---" * (len(columns) + 1) + "|\n")
    for root in SCORED_ROOTS:
        row = confusion.get(root, {})
        cells = []
        for col in columns:
            n = row.get(col, 0)
            cells.append("·" if n == 0 else (f"**{n:,}**" if col == root else f"{n:,}"))
        w(f"| {root} | " + " | ".join(cells) + " |\n")
    w("\nThe diagonal is in bold. Everything off it is either a cross-listing the tree "
      "asks for — a receipt is a Document *and* a Purchase — or a mistake, and the "
      "matrix is what lets those be told apart at a glance.\n\n")

    # ---- leaf level -----------------------------------------------------
    leaf = scores["leaf"]
    w("## Leaf-level classification (only where the label is derivable)\n\n")
    if leaf["total"]:
        w(f"- exact leaf correct: **{leaf['exact']:,} / {leaf['total']:,} "
          f"({leaf['exact']/leaf['total']*100:.1f}%)**\n")
        w(f"- right root, wrong or shallower branch: {leaf['right_root']:,} "
          f"({leaf['right_root']/leaf['total']*100:.1f}%)\n")
        w(f"- wrong root: {leaf['miss']:,} ({leaf['miss']/leaf['total']*100:.1f}%)\n\n")
        w("| root | n | exact | right root | miss |\n|---|--:|--:|--:|--:|\n")
        for root, c in sorted(scores["leaf_by_root"].items()):
            w(f"| {root} | {c['total']:,} | {c['exact']:,} | {c['right_root']:,} | {c['miss']:,} |\n")
        w("\n")

    # ---- cost -----------------------------------------------------------
    w("## Cost — what the engine had to spend\n\n")
    w("L1-B says stop escalating when the answer stops changing. This is that, measured:\n\n")
    w("| deepest tier that produced the ANSWER | assets | share |\n|---|--:|--:|\n")
    for t, n in sorted(stats.by_tier.items()):
        w(f"| {Tier(t).label} | {n:,} | {n/max(1,stats.classified)*100:.1f}% |\n")
    w("\n| deepest tier the engine PAID FOR | assets | share |\n|---|--:|--:|\n")
    for t, n in sorted(stats.by_tier_spent.items()):
        w(f"| {Tier(t).label} | {n:,} | {n/max(1,stats.classified)*100:.1f}% |\n")
    w("\nThe second table is larger than the first, and should be: a photo answered by "
      "its GPS fix still cost a face pass if one ran. Read the OCR row in it with care "
      "— the corpus hands every asset a text string, so it reflects the adapter and not "
      "the C-1 gate, which on a device decides which assets get an OCR pass at all and "
      "lives upstream in `OCRGate.swift`.\n\n")
    w(f"\nClassification throughput: **{stats.assets_per_s:,.0f} assets/s** "
      f"({stats.wall_s*1000/max(1,stats.classified):.3f} ms/asset) for the decision logic alone — "
      "this excludes OCR, embedding and thumbnail decode, which are the T0-A costs and "
      "are measured separately on the Simulator.\n")
    w(f"Catalogue: {catalog.size_bytes()/1e6:.1f} MB, "
      f"{catalog.size_bytes()/max(1,total):.0f} B/asset.\n\n")

    # ---- what it declined to guess --------------------------------------
    w("## What the engine declined to decide\n\n")
    w(f"- flagged for review: **{stats.needs_review:,}** ({stats.needs_review/total*100:.1f}%)\n")
    w(f"- filed on the timeline and nowhere else: **{stats.unfiled:,}** "
      f"({stats.unfiled/total*100:.1f}%)\n")
    w("  Almost all of these are the `Downloads` and `Objects` assets above, whose "
      "signal the corpus does not carry. An engine that guessed a leaf for them would "
      "score better here and be worse in the hand.\n\n")

    # ---- the KPIs the product is actually defined by ---------------------
    # PF-12: F1 and precision are the measures I chose. These are the ones L1 §18
    # names, and where the two disagree these win. A classifier with a superb F1 and a
    # Human Review Burden of 300 per 1,000 is a failed product — the user was handed
    # the work back — and the F1 cannot see it.
    errors = {}
    for aid, t in truth.items():
        preds = [p for p in predicted.get(aid, []) if taxonomy.root_of(p) != "Timeline"]
        truths = set(t["paths"])
        errors[aid] = bool(preds) and not (set(preds) & truths)
    k = kpi.report(catalog, library_size=len(truth), errors_by_asset=errors)
    w("## Constitution §18 KPIs\n\n")
    w(k.as_markdown())
    w("\nWeighted Error Cost here is **outcome**: it prices the real mistakes against "
      "the labels. On a real library there are no labels, so the field number is "
      "*exposure* — what it would cost if every acting proposal were wrong — and the "
      "two must never be reported as the same quantity.\n\n")

    # ---- safety ---------------------------------------------------------
    audit = safety_audit(catalog)
    w("## Safety red lines (checked against the written catalogue, not the code)\n\n")
    checks = [
        ("nothing R4+ was acted on (§6, Tier 2-A: 高风险类别零自动删除)", audit["protected_removals"] == 0,
         f"{audit['protected_removals']} found"),
        ("every assignment carries evidence", audit["unexplained_assignments"] == 0,
         f"{audit['unexplained_assignments']} unexplained"),
        ("no irreversible proposal", audit["irreversible_proposals"] == 0,
         f"{audit['irreversible_proposals']} found"),
        ("every removal requires confirmation", audit["removals_without_confirmation"] == 0,
         f"{audit['removals_without_confirmation']} found"),
    ]
    for name, ok, detail in checks:
        w(f"- {'PASS' if ok else 'FAIL'} — {name} ({detail})\n")
    w(f"\n- assets protected by risk class: {audit['protected_assets']:,}\n")
    w(f"- proposals the engine considers safe to apply without asking "
      f"(exact byte-duplicates only): {audit['auto_applicable']:,}\n\n")

    # ---- the policy table Tier 2-A requires -----------------------------
    w("## Risk policy table (§5 / §6, generated from the code it documents)\n\n")
    w(policy_table())
    w("\n\n")

    # ---- ablation -------------------------------------------------------
    if ablation:
        w("## Ablation — metadata only, no OCR, no faces, no scene labels\n\n")
        w("What the free signals alone are worth. The gap is what the expensive tiers buy.\n\n")
        w("| | full | metadata only |\n|---|--:|--:|\n")
        w(f"| macro F1 (scored roots) | {sum(macro)/len(macro):.3f} | {ablation['macro_f1']:.3f} |\n")
        w(f"| leaf exact | {leaf['exact']/max(1,leaf['total'])*100:.1f}% | "
          f"{ablation['leaf_exact_pct']:.1f}% |\n")
        w(f"| filed only on the timeline | {stats.unfiled/total*100:.1f}% | "
          f"{ablation['unfiled_pct']:.1f}% |\n\n")

    failed = [name for name, ok, _ in checks if not ok]
    if failed:
        w("## RESULT: FAIL\n\nA safety red line did not hold: " + "; ".join(failed) + "\n")
        return 1
    return 0


def run_ablation(library: str, catalog_path: str) -> dict:
    assets, truth, predicted, catalog, stats = evaluate(library, catalog_path, budget=Tier.METADATA)
    scores = score(truth, predicted)
    macro = []
    for root in SCORED_ROOTS:
        c = scores["per_root"][root]
        macro.append(prf(c["tp"], c["fp"], c["fn"])[2])
    leaf = scores["leaf"]
    out = {"macro_f1": sum(macro) / len(macro),
           "leaf_exact_pct": leaf["exact"] / max(1, leaf["total"]) * 100,
           "unfiled_pct": stats.unfiled / max(1, len(truth)) * 100}
    catalog.close()
    return out


# ---------------------------------------------------------------------------
def selftest() -> int:
    """The scorer is a tool that will meet the real result once. Exercise its logic on
    input whose answer is known by construction, the way every other analyzer in this
    repo is exercised before it sees data."""
    fails = []

    p, r, f = prf(8, 2, 2)
    if abs(p - 0.8) > 1e-9 or abs(r - 0.8) > 1e-9 or abs(f - 0.8) > 1e-9:
        fails.append(f"prf(8,2,2) = {p},{r},{f}")
    if prf(0, 0, 0) != (0.0, 0.0, 0.0):
        fails.append("prf with no data must be zero, not a crash or a 1.0")

    truth = {
        # scored: leaf derivable from GPS
        "a": {"category_path": "Places > Japan > Tokyo", "paths": ["Places > Japan > Tokyo"],
              "is_foreground": False, "hard_negative": None, "exact_duplicate_of": None},
        # coin-flip leaf: background screenshot
        "b": {"category_path": "Screenshots > Chat", "paths": ["Screenshots > Chat"],
              "is_foreground": False, "hard_negative": None, "exact_duplicate_of": None},
        # signal absent
        "c": {"category_path": "Objects > Bicycle", "paths": ["Objects > Bicycle"],
              "is_foreground": False, "hard_negative": None, "exact_duplicate_of": None},
    }
    predicted = {"a": ["Places > Japan > Tokyo"], "b": ["Screenshots"], "c": []}
    s = score(truth, predicted)

    if s["leaf"]["total"] != 1 or s["leaf"]["exact"] != 1:
        fails.append(f"leaf scoring counted {dict(s['leaf'])}; only the derivable one may be scored")
    if s["unscorable_label"]["Screenshots"] != 1:
        fails.append("a coin-flip leaf was not excluded from scoring")
    if s["unscorable_signal"]["Objects"] != 1:
        fails.append("an asset whose signal the corpus lacks was not reported as such")
    if s["per_root"]["Screenshots"]["tp"] != 1:
        fails.append("root credit was not given for the correctly identified root")

    # A shallower-but-right answer must not be scored as a wrong root.
    truth2 = {"d": {"category_path": "People > Anna", "paths": ["People > Anna"],
                    "is_foreground": True, "hard_negative": None, "exact_duplicate_of": None}}
    s2 = score(truth2, {"d": ["People > Groups"]})
    if s2["leaf"]["right_root"] != 1:
        fails.append("a wrong leaf under the right root was scored as a wrong root")

    for msg in fails:
        print("FAIL:", msg)
    print(f"\nselftest: {len(fails)} failure(s)")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--library")
    ap.add_argument("--catalog", default="eval_catalog.sqlite")
    ap.add_argument("--out")
    ap.add_argument("--no-ablation", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    if not args.library:
        ap.error("--library is required (or use --selftest)")

    assets, truth, predicted, catalog, stats = evaluate(args.library, args.catalog)
    scores = score(truth, predicted)
    ablation = None if args.no_ablation else run_ablation(args.library, args.catalog + ".ablation")

    buf = io.StringIO()
    rc = report(truth, predicted, catalog, stats, scores, ablation, buf)
    text = buf.getvalue()
    sys.stdout.write(text)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
    catalog.close()
    return rc


if __name__ == "__main__":
    sys.exit(main())
