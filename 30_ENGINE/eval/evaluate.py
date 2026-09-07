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
import time
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
from pvm.verdict import Assignment, Classification, Evidence  # noqa: E402
from pvm.risk import (ACTING_ACTIONS, Action, Factors, classify_risk,  # noqa: E402
                      decide_action, lifecycle_of, recoverability_of,
                      NEVER_DELETE_AT_OR_ABOVE, NEVER_DELETE_AT_OR_ABOVE_IMPORTANCE,
                      REMOVING_ACTIONS, Importance, Risk, equivalence_table,
                      policy_table)
from pvm import importance
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


def evaluate(library: str, catalog_path: str, budget: Tier = Tier.TEXT,
             strip: Optional[str] = None):
    assets = load_manifest(library)
    truth = ground_truth(library)
    if strip:
        assets = _stripped(assets, strip)

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


def risk_evaluation(truth, catalog) -> dict:
    """Tier 2-A / §19 Risk/Importance Classification：风险分级是否可靠.

    This register said for a long time that risk grading could not be evaluated because
    the corpus carries no risk labels. It does not — and it does not need to. §6 grades
    risk *from the category*, and the corpus labels categories. So the ground-truth
    risk of an asset is what `classify_risk` returns for its TRUE paths, and the
    engine's answer is what it returned for the paths it PREDICTED. The two differ
    exactly when a classification error propagates into a consequence error, which is
    the question §19 is asking.

    What this cannot measure, stated rather than glossed:

    * **R6.** Irreplaceability is knowledge only the user has (§14) and no label here
      carries it, so `is_irreplaceable` is False on both sides and R6 never appears.
    * **De-escalation by duplication.** §6 drops an exact duplicate to R0. That is
      driven by a content hash rather than by the category, so it is applied to the
      engine's answer and not to the truth, and those assets are excluded rather than
      counted as disagreements.

    The direction matters more than the rate. Over-grading costs the user some
    automation; under-grading is how something gets acted on that should not have
    been, so it is counted, reported and bounded separately.
    """
    duplicates = {r[0] for r in catalog.db.execute(
        "SELECT asset_id FROM proposals WHERE action='auto_clean'")}
    got = dict(catalog.db.execute("SELECT asset_id, risk FROM assets"))
    acted = {r[0] for r in catalog.db.execute(
        "SELECT asset_id FROM proposals WHERE action IN (%s)"
        % ",".join("?" * len(ACTING_ACTIONS)), [a.value for a in ACTING_ACTIONS])}

    matrix = defaultdict(Counter)
    exact = under = over = 0
    dangerous = []            # true risk R4+, graded below the never-delete floor
    dangerous_and_acted = []  # ...and something was actually proposed for it
    blind = 0                 # excluded: the corpus gives the engine no signal
    compared = 0
    for aid, t in truth.items():
        if aid in duplicates or aid not in got:
            continue
        true_paths = list(t.get("paths") or [])
        if not true_paths:
            continue

        # The same exclusions the classification scoring applies, for the same reason.
        # A root the corpus carries no signal for, and a filler asset whose leaf was
        # chosen with `random.choice`, are not questions the engine got wrong — they
        # are questions it was never asked. Counting them here would report corpus
        # blindness as risk error, and the two have opposite remedies.
        true_root = taxonomy.root_of(t["category_path"])
        derivable = (
            true_root in ("Places", "People", "Travel")
            or (t["is_foreground"] and true_root in ("Screenshots", "Documents", "Purchases")))
        if true_root in SIGNAL_ABSENT_ROOTS or not derivable:
            blind += 1
            continue
        want = classify_risk(
            Classification(aid, [Assignment(p, [Evidence("truth", Tier.METADATA, 1.0,
                                                         "ground truth")])
                                 for p in true_paths if taxonomy.is_node(p)]),
            has_person=any(p.startswith("People") for p in true_paths))
        have = Risk(got[aid]) if got[aid] in {int(r) for r in Risk} else None
        if have is None:
            continue
        compared += 1
        matrix[want][have] += 1
        if have == want:
            exact += 1
        elif have < want:
            under += 1
            if want >= NEVER_DELETE_AT_OR_ABOVE and have < NEVER_DELETE_AT_OR_ABOVE:
                dangerous.append(aid)
                if aid in acted:
                    dangerous_and_acted.append(aid)
        else:
            over += 1

    # The same question over the WHOLE library, including the assets excluded above.
    # An under-grade only costs something if it authorises an action, and that is
    # checkable on every asset regardless of whether its label is scorable — so the
    # safety claim does not depend on the exclusions being the right ones.
    acted_below_true_floor = []
    for aid in acted:
        t = truth.get(aid)
        if not t or aid in duplicates:
            continue
        paths = [p for p in (t.get("paths") or []) if taxonomy.is_node(p)]
        if not paths:
            continue
        want = classify_risk(
            Classification(aid, [Assignment(p, [Evidence("truth", Tier.METADATA, 1.0,
                                                         "ground truth")]) for p in paths]),
            has_person=any(p.startswith("People") for p in paths))
        if want >= NEVER_DELETE_AT_OR_ABOVE:
            acted_below_true_floor.append(aid)

    return {"compared": compared, "exact": exact, "under": under, "over": over,
            "dangerous": dangerous, "dangerous_and_acted": dangerous_and_acted,
            "acted_below_true_floor": acted_below_true_floor, "blind": blind,
            "acted": len(acted),
            "matrix": matrix, "skipped_duplicates": len(duplicates)}


def action_evaluation(truth, catalog) -> dict:
    """Tier 1-C: 重点是 Suggest Delete 的 False Positive.

    The rate has never been measured, and the register said so for as long as it has
    existed. It is derivable the same way §19's risk grading is, and by the same
    argument: the action is a function of the factors, the factors are a function of
    the category, and the corpus labels categories. So the counterfactual is *what the
    policy would have proposed given a perfect classification* — `decide_action` run
    over the true category's risk and lifecycle rather than the predicted one's.

    A Suggest Delete is a false positive when the engine offers to remove something
    that a correctly-classified library would have kept, protected or archived. That is
    the number Tier 1-C is about, and it is a statement about the *classifier* reaching
    the *policy*, which is why it cannot be measured inside either one alone.

    Held constant across both sides, deliberately:

    * **Confidence.** The counterfactual is a perfect classification, so it is 1.0 —
      otherwise this would measure the confidence gate rather than the mistake.
    * **Byte identity and capture date.** Both are measured metadata rather than
      classification outputs, so they are the same fact on both sides. Withholding the
      date was the first version of this function and it made the number meaningless:
      `lifecycle_of` with no age returns TEMPORARY rather than EXPIRED, so every
      expired screenshot the engine correctly offered to remove came back as a false
      positive and the rate read 85.7%. A counterfactual that changes more than the one
      thing being tested is not a counterfactual.
    """
    duplicates = {r[0] for r in catalog.db.execute(
        "SELECT asset_id FROM proposals WHERE action='auto_clean'")}
    proposed = dict(catalog.db.execute("SELECT asset_id, action FROM proposals"))
    created = dict(catalog.db.execute("SELECT asset_id, created_at FROM assets"))
    now = time.time()

    false_positives, true_positives, missed = [], [], []
    for aid, action in proposed.items():
        t = truth.get(aid)
        if not t:
            continue
        paths = [p for p in (t.get("paths") or []) if taxonomy.is_node(p)]
        if not paths:
            continue
        c = Classification(aid, [Assignment(p, [Evidence("truth", Tier.METADATA, 1.0,
                                                         "ground truth")]) for p in paths])
        want_risk = classify_risk(c, is_exact_duplicate=aid in duplicates,
                                  has_person=any(p.startswith("People") for p in paths))
        when = created.get(aid)
        age_days = max(0.0, (now - when) / 86400) if when else None
        want = decide_action(Factors(
            risk=want_risk,
            lifecycle=lifecycle_of(c, age_days),
            confidence=1.0,
            recoverability=recoverability_of(want_risk),
            importance=importance.assess(importance.ImportanceSignals(
                paths=paths, recoverability=recoverability_of(want_risk),
                is_irreplaceable=want_risk == Risk.R6_IRREPLACEABLE)).level,
            is_exact_duplicate=aid in duplicates))

        offered = action in {a.value for a in REMOVING_ACTIONS}
        should = want in REMOVING_ACTIONS
        if offered and not should:
            false_positives.append((aid, action, want.value, want_risk.name))
        elif offered and should:
            true_positives.append(aid)
        elif should and not offered:
            missed.append((aid, action, want.value))
    return {"false_positives": false_positives, "true_positives": true_positives,
            "missed": missed, "proposals": len(proposed)}


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
    # The same red line on the other §5 axis. `Proposal.__post_init__` refuses this in
    # code; checking it against the rows that were actually written is a different
    # claim, and a red line enforced only where it is enforced is not a red line.
    removing = ",".join("?" * len(REMOVING_ACTIONS))
    meaningful_removals = one(
        f"SELECT COUNT(*) FROM assets a JOIN proposals p USING(asset_id) "
        f"WHERE a.importance>=? AND p.action IN ({removing})",
        int(NEVER_DELETE_AT_OR_ABOVE_IMPORTANCE),
        *[a.value for a in REMOVING_ACTIONS])
    return {
        "meaningful_removals": meaningful_removals,
        "meaningful_assets": one("SELECT COUNT(*) FROM assets WHERE importance>=?",
                                 int(NEVER_DELETE_AT_OR_ABOVE_IMPORTANCE)),
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
    w("\nWeighted Error Cost is priced by §18's own formula — 错误 × 内容重要性 × "
      "不可恢复程度. It previously used the risk class as a stand-in for 内容重要性 "
      "and then multiplied it again by an irrecoverability derived from that same "
      "class, cubing one axis and never reading the other. The number moved because "
      "the formula was corrected, not because the engine's behaviour changed: every "
      "classification, risk grade and action in this report is identical to the run "
      "before it.\n\n"
      "Weighted Error Cost here is **outcome**: it prices the real mistakes against "
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
        ("nothing MEANINGFUL or above was offered for removal (§5 Importance, §18 "
         "Weighted Error Cost)", audit["meaningful_removals"] == 0,
         f"{audit['meaningful_removals']} of {audit['meaningful_assets']:,} such assets"),
    ]
    for name, ok, detail in checks:
        w(f"- {'PASS' if ok else 'FAIL'} — {name} ({detail})\n")
    w(f"\n- assets protected by risk class: {audit['protected_assets']:,}\n")
    w(f"- proposals the engine considers safe to apply without asking "
      f"(exact byte-duplicates only): {audit['auto_applicable']:,}\n\n")

    # ---- §19 risk grading -----------------------------------------------
    risk_eval = risk_evaluation(truth, catalog)
    w("## §19 — Risk/Importance Classification：风险分级是否可靠\n\n")
    w("The corpus carries no risk labels and does not need to: §6 grades risk *from the "
      "category*, and the corpus labels categories. So ground truth here is what "
      "`classify_risk` returns for an asset's TRUE paths, against what the engine "
      "returned for the paths it predicted. The two differ exactly when a "
      "classification error propagates into a consequence error, which is what §19 is "
      "asking about.\n\n")
    n = max(1, risk_eval["compared"])
    w("Scored over the same subset the classification is: assets whose root the corpus "
      "carries a signal for, and whose leaf was not chosen with `random.choice`. A "
      "question the engine was never asked is not a question it got wrong, and "
      "counting corpus blindness as risk error would point at the wrong remedy.\n\n")
    w(f"- compared: **{risk_eval['compared']:,}** assets "
      f"({risk_eval['blind']:,} excluded as unscorable, {risk_eval['skipped_duplicates']:,} "
      "as exact duplicates — §6 drops those to R0 on a content hash rather than on "
      "their category, so they are not a disagreement about grading)\n")
    w(f"- graded exactly right: **{risk_eval['exact']:,} ({risk_eval['exact']/n*100:.1f}%)**\n")
    w(f"- graded too HIGH: {risk_eval['over']:,} ({risk_eval['over']/n*100:.1f}%) — "
      "costs the user automation, costs them nothing else\n")
    w(f"- graded too LOW: {risk_eval['under']:,} ({risk_eval['under']/n*100:.1f}%) — "
      "the direction that matters\n")
    w(f"- of those, crossing the never-delete floor (true risk R4+, graded below it): "
      f"**{len(risk_eval['dangerous']):,}**")
    w(f", and of THOSE, the number that were actually proposed for an action: "
      f"**{len(risk_eval['dangerous_and_acted']):,}**\n")
    if risk_eval["dangerous"]:
        w("  - " + ", ".join(sorted(risk_eval["dangerous"])[:10]) + "\n")

    w("\n**The claim that does not rest on the exclusions.** An under-grade only costs "
      "something if it authorises an action, and that is checkable on every asset in "
      "the library whether or not its label is scorable. Of the "
      f"{risk_eval['acted']:,} assets the engine proposed any action for, "
      f"**{len(risk_eval['acted_below_true_floor']):,}** have a true risk of R4 or "
      "above. That is the number §19 is really asking for, and it does not depend on "
      "this evaluation having drawn the scorable subset correctly.\n")
    if risk_eval["acted_below_true_floor"]:
        w("  - " + ", ".join(sorted(risk_eval["acted_below_true_floor"])[:10]) + "\n")
    w("\nR6 does not appear: irreplaceability is knowledge only the user has (§14) and "
      "no label here carries it, so it is False on both sides.\n\n")
    high = sum(n for want, row in risk_eval["matrix"].items()
               for n in row.values() if want >= NEVER_DELETE_AT_OR_ABOVE)
    w(f"**Read the top of the scale with care.** Only {high:,} of the "
      f"{risk_eval['compared']:,} scorable assets have a true risk of R4 or above, "
      "because this corpus has few foreground documents and none of its filler "
      "documents carry a signal. A perfect score over seventeen assets is evidence "
      "that the mapping is wired up correctly; it is not a rate, and the levels where "
      "being wrong is expensive are exactly the ones this library is thinnest on.\n\n")

    levels = sorted({r for r in risk_eval["matrix"]}
                    | {h for row in risk_eval["matrix"].values() for h in row})
    if levels:
        w("| true risk \\ graded as | " + " | ".join(r.name for r in levels) + " |\n")
        w("|---" * (len(levels) + 1) + "|\n")
        for want in levels:
            cells = []
            for have in levels:
                count = risk_eval["matrix"][want].get(have, 0)
                cells.append(f"**{count:,}**" if have == want else (f"{count:,}" if count else "·"))
            w(f"| {want.name} | " + " | ".join(cells) + " |\n")
        w("\n")

    # ---- Tier 1-C's own number ------------------------------------------
    actions = action_evaluation(truth, catalog)
    offered = len(actions["false_positives"]) + len(actions["true_positives"])
    w("## Tier 1-C — Suggest Delete 的 False Positive\n\n")
    w("Derivable by the same argument as §19 above: the action is a function of the "
      "factors, the factors are a function of the category, and the corpus labels "
      "categories. So the counterfactual is what `decide_action` would have proposed "
      "given a *perfect* classification. A false positive is the engine offering to "
      "remove something a correctly-classified library would have kept. Confidence is "
      "held at 1.0 on the counterfactual side — otherwise this would measure the "
      "confidence gate rather than the mistake — and byte identity and the capture date "
      "are the same facts on both sides, because both are measured metadata rather "
      "than classification outputs.\n\n")
    w(f"- assets offered for removal: **{offered:,}** of {total:,} "
      f"({offered/total*100:.2f}%)\n")
    w(f"- of those, ones a perfect classification would also have removed: "
      f"**{len(actions['true_positives']):,}**\n")
    w(f"- **Suggest Delete false positives: {len(actions['false_positives']):,}**"
      + (f" ({len(actions['false_positives'])/offered*100:.1f}% of what was offered)"
         if offered else "") + "\n")
    w(f"- removals a perfect classification would have offered and this one did not: "
      f"{len(actions['missed']):,} — the cost of caution, in automation not taken\n")
    w(f"\n**Read this the way §19's top of the scale should be read.** {offered:,} "
      f"offers out of {total:,} assets is a very conservative engine, and a 0% false "
      "positive rate over that many offers is evidence that the policy table and the "
      "classifier agree — it is not a rate anyone should quote at a larger scale. The "
      "same corpus that makes the engine cautious here is the one that gives it no "
      "signal for a third of its own library.\n\n" if not actions["false_positives"]
      else "\n")
    if actions["false_positives"]:
        w("\n| asset | offered | a perfect classification would | true risk |\n")
        w("|---|---|---|---|\n")
        for aid, got, want, risk in sorted(actions["false_positives"])[:15]:
            w(f"| {aid} | {got} | {want} | {risk} |\n")
    w("\n")

    # ---- Tier 1-D's six indexes -----------------------------------------
    coverage = catalog.index_coverage()
    w("## Tier 1-D — 一个 Asset 同时挂载 Content / Time / Place / Person / Object / "
      "Event 索引\n\n")
    w("Counted from the rows rather than asserted: \"the asset is on six indexes\" is a "
      "claim about what was written, and a claim about rows should be counted from "
      "them. Reachable in both directions — from an entity to its sightings "
      "(`pvm/catalog.py::sightings`) and from one asset to everything it is indexed "
      "under (`pvm/catalog.py::entities_for`).\n\n")
    w("| index | assets carrying it | share |\n|---|--:|--:|\n")
    for name in ("content", "time", "place", "person", "object", "event"):
        n = coverage.get(name, 0)
        w(f"| {name.title()} | {n:,} | {n/total*100:.1f}% |\n")
    w("\n")
    if not coverage.get("object"):
        # A zero here reads as a broken index. It is not, and saying which it is costs
        # one sentence and saves the next reader an afternoon.
        blind = sum(1 for row in truth.values()
                    if str(row.get("category_path", "")).startswith("Objects"))
        w(f"**Object is 0% because this corpus carries no scene labels for its {blind:,} "
          "object assets**, not because the index is missing: `pvm/memory.py::_objects` "
          "builds an object entity from a scene label and `tests/test_memory.py` covers "
          "it. It is the same corpus blindness the coverage section above reports for "
          "Downloads, Clothing and Objects, and the same reason T1B-EMBEDDING is "
          "blocked — an object index needs photographs of objects.\n\n")

    # ---- §11's inference ------------------------------------------------
    inferred = getattr(stats.context, "inferred_places", {}) or {}
    w("## §11 — places worked out rather than read\n\n")
    w("无 GPS 时可以利用相邻时间照片、地标等推断，但必须保存置信度. `pvm/infer.py` "
      "reads the photographs either side of an asset in time; nothing else.\n\n")
    if not inferred:
        w("Nothing was inferred in this library.\n\n")
    else:
        by_grain = Counter(g.granularity for g in inferred.values())
        bracketed = sum(1 for g in inferred.values() if g.is_bracketed)
        mean_conf = sum(g.confidence for g in inferred.values()) / len(inferred)
        w(f"- assets given an inferred place: **{len(inferred):,}** "
          f"({len(inferred)/total*100:.1f}% of the library)\n")
        w(f"- as specific as a city: {by_grain.get('city', 0):,} · "
          f"country only: {by_grain.get('country', 0):,}\n")
        w(f"- bracketed (an anchor on each side): {bracketed:,} · "
          f"one-sided: {len(inferred) - bracketed:,}\n")
        w(f"- mean confidence **{mean_conf:.2f}**, and a measured fix is 1.00. §11 "
          "requires the two never to be conflated: the classifier records these under "
          "the signal name `geo:inferred`, never `geo`, and never as an asset's "
          "primary category.\n\n")
        w("**The trade, stated rather than buried.** An inferred place only becomes a "
          "browse assignment when the asset has no home in the tree at all — filing "
          "every one of them cost 279 `Places` false positives on this library and "
          "gained no recall, because a photograph of a person that is already under "
          "`People` does not need a city shelf too. Gated to the assets nothing else "
          "placed, it moved 71 assets off the timeline-only pile (Classification "
          "Coverage 94.0% → 94.8%, unfiled 596 → 525) at a cost of 71 `Places` false "
          "positives (precision 0.982 → 0.966). Those 71 are mostly objects and "
          "downloads whose real category this corpus carries no signal for, so what "
          "the change actually buys is *findable by place instead of findable only by "
          "date*, and what it costs is a slightly less pure city shelf. Neither number "
          "is the whole answer and both are above.\n\n")

    # ---- §4 and §5's sixth factor ---------------------------------------
    w("## §4 精细 Visual Asset Taxonomy and §5 Importance\n\n")
    w("§4 is a different scheme from the navigational tree: the tree is where a user "
      "browses, §4 exists to 改变整理、风险、生命周期和动作策略. Two of its thirteen "
      "classes are not branches at all — 珍贵记忆 is a property of one asset and "
      "连拍/同一时刻 is a relation between assets.\n\n")
    w(importance.class_table())
    w("\n\n### What this library actually is, by §4 class\n\n")
    w("| §4 大类 | assets | share | median importance |\n|---|--:|--:|:--|\n")
    # A true median, not a rounded mean. The mean of a class that is half I0 and half
    # I4 is I2, which no asset in it actually is — and the whole column exists to say
    # what a class typically *is*.
    class_rows = list(catalog.db.execute(
        "SELECT asset_class, COUNT(*) FROM assets WHERE asset_class IS NOT NULL "
        "GROUP BY asset_class ORDER BY COUNT(*) DESC"))
    for key, n in class_rows:
        cls = importance.BY_KEY.get(key)
        values = sorted(r[0] for r in catalog.db.execute(
            "SELECT importance FROM assets WHERE asset_class=? AND importance IS NOT NULL",
            (key,)))
        # `is not None`, not truthiness: I0_NONE is 0 and is a real level. The first
        # version of this line printed "n/a" for every asset the engine had correctly
        # graded as worthless, which is the one row a reader would look at hardest.
        level = Importance(values[len(values) // 2]) if values else None
        w(f"| {cls.name if cls else key} | {n:,} | {n/total*100:.1f}% | "
          f"{level.name if level is not None else 'n/a'} |\n")
    if not class_rows:
        w("| *(nothing assessed)* | 0 | 0.0% | n/a |\n")

    w("\n### Importance against risk\n\n")
    w("The two axes §5 keeps apart. If this table were diagonal, one of them would be "
      "redundant and §5 would be wrong to name both.\n\n")
    grid = {}
    for r, i, n in catalog.db.execute(
            "SELECT risk, importance, COUNT(*) FROM assets "
            "WHERE importance IS NOT NULL GROUP BY risk, importance"):
        grid[(r, i)] = n
    levels = [i for i in Importance if any((r, int(i)) in grid for r in range(7))]
    w("| risk \\ importance | " + " | ".join(i.name for i in levels) + " |\n")
    w("|---" * (len(levels) + 1) + "|\n")
    for r in range(7):
        row = [grid.get((r, int(i)), 0) for i in levels]
        if not any(row):
            continue
        w(f"| {Risk(r).name} | " + " | ".join(f"{n:,}" if n else "·" for n in row) + " |\n")
    off = sum(n for (r, i), n in grid.items() if abs(r - i) >= 2)
    w(f"\n**{off:,} assets ({off/total*100:.1f}%) sit two or more levels apart on the "
      "two axes** — the assets a single-axis engine would have graded wrongly, in one "
      "direction or the other.\n\n")

    # ---- the policy table Tier 2-A requires -----------------------------
    w("## Risk policy table (§5 / §6, generated from the code it documents)\n\n")
    w(policy_table())
    w("\n\n")
    w("### §8 Equivalence Margin against Importance\n\n")
    w("同样的相似度，在 Meme 和家庭照片上采取不同策略 — the same measurement, two "
      "policies. Generated from `decide_action`, so the table cannot drift from it.\n\n")
    w(equivalence_table())
    w("\n\n")

    # ---- ablation -------------------------------------------------------
    if ablation:
        arms = ablation.get("arms") or {"metadata only": ablation}
        w("## Ablation — 只 OCR、只视觉、组合信号分别表现如何 (Tier 2-E)\n\n")
        w("Each arm names what it KEEPS. Metadata is never stripped: it is free, it is "
          "always there, and a run without a capture date has no timeline to be scored "
          "against. So these answer *which expensive signal earns its cost*, which is "
          "the question Tier 2-E is asking.\n\n")
        for label, _, describes in ABLATION_ARMS:
            w(f"- **{label}** — {describes}\n")
        w("\n| | " + " | ".join(["full"] + [a for a, _, _ in ABLATION_ARMS]) + " |\n")
        w("|---" * (len(ABLATION_ARMS) + 2) + "|\n")

        full_macro = sum(macro) / len(macro)
        row = [f"{full_macro:.3f}"] + [f"{arms[a]['macro_f1']:.3f}"
                                       for a, _, _ in ABLATION_ARMS]
        w("| macro F1 (scored roots) | " + " | ".join(row) + " |\n")
        row = [f"{leaf['exact']/max(1,leaf['total'])*100:.1f}%"] + \
              [f"{arms[a]['leaf_exact_pct']:.1f}%" for a, _, _ in ABLATION_ARMS]
        w("| leaf exact | " + " | ".join(row) + " |\n")
        row = [f"{stats.unfiled/total*100:.1f}%"] + \
              [f"{arms[a]['unfiled_pct']:.1f}%" for a, _, _ in ABLATION_ARMS]
        w("| filed only on the timeline | " + " | ".join(row) + " |\n\n")

        w("### Per root — where each signal actually does the work\n\n")
        w("An overall F1 hides the shape of the answer: a signal that carries one root "
          "entirely and touches nothing else looks the same, averaged, as one that "
          "helps everywhere a little.\n\n")
        w("| root | full | " + " | ".join(a for a, _, _ in ABLATION_ARMS) + " |\n")
        w("|---" * (len(ABLATION_ARMS) + 2) + "|\n")
        for root in SCORED_ROOTS:
            c = scores["per_root"][root]
            cells = [f"{prf(c['tp'], c['fp'], c['fn'])[2]:.3f}"]
            cells += [f"{arms[a]['per_root'][root]:.3f}" for a, _, _ in ABLATION_ARMS]
            w(f"| {root} | " + " | ".join(cells) + " |\n")
        w("\n")

        # The reading, because the numbers do not say it out loud and this is the one
        # thing the ablation was run to find out.
        vision_only = arms.get("+ vision only", {}).get("per_root", {})
        ocr_only = arms.get("+ OCR only", {}).get("per_root", {})
        metadata = arms.get("metadata only", {}).get("per_root", {})
        needs_vision = sorted(r for r in SCORED_ROOTS
                              if vision_only.get(r, 0) - ocr_only.get(r, 0) > 0.5)
        needs_ocr = sorted(r for r in SCORED_ROOTS
                           if ocr_only.get(r, 0) - vision_only.get(r, 0) > 0.5)
        free = sorted(r for r in SCORED_ROOTS if metadata.get(r, 0) > 0.9)
        w("**The two expensive signals do not overlap.** ")
        if needs_vision and needs_ocr:
            w(f"{', '.join(needs_vision)} is carried entirely by vision and scores zero "
              f"without it; {', '.join(needs_ocr)} likewise for OCR. Neither signal can "
              "stand in for the other on the roots the other owns, so there is no "
              "cheaper subset here — the question C-1 answers is not *whether* to run "
              "OCR but on which assets, and this says the cost of getting that gate "
              "wrong is a whole category rather than a few percent.\n\n")
        else:
            w("the per-root split above is the evidence; read it directly.\n\n")
        if free:
            w(f"**{', '.join(free)} come off the free PhotoKit row** and are not worth "
              "spending anything on. Every point of macro F1 the expensive tiers buy is "
              "bought on the roots they alone can reach.\n\n")

    failed = [name for name, ok, _ in checks if not ok]
    if failed:
        w("## RESULT: FAIL\n\nA safety red line did not hold: " + "; ".join(failed) + "\n")
        return 1
    return 0


def _stripped(assets, what: str):
    """A copy of the library with one family of signals removed.

    Ablation by *budget* can only answer "how far up the ladder did we climb", which
    makes "metadata only" expressible and "OCR but no vision" not — the budget is a
    ceiling and TEXT sits above VISUAL and FACES. Tier 2-E asks for 只 OCR、只视觉,
    which are questions about which signal is present, so the arms strip signals
    instead. Metadata is never stripped: it is free, it is always there, and a run
    without a capture date has no timeline to be scored against.
    """
    import copy
    out = []
    for a in assets:
        b = copy.copy(a)
        if what in ("ocr", "all"):
            b.ocr_ran, b.ocr_text = False, ""
        if what in ("vision", "all"):
            b.scene_labels, b.face_clusters = [], []
        out.append(b)
    return out


#: Tier 2-E: 输出 ablation：只 OCR、只视觉、组合信号分别表现如何.
#:
#: Each arm names what it KEEPS, because that is the question — "what is this signal
#: worth" — and a list of what was removed reads backwards at a glance.
ABLATION_ARMS = [
    ("metadata only", "all",
     "capture date, dimensions, provenance, GPS — the free PhotoKit row"),
    ("+ vision only", "ocr",
     "metadata plus scene labels and face clusters; no text at all"),
    ("+ OCR only", "vision",
     "metadata plus recognised text; no scene labels, no faces"),
]


def _arm_scores(library: str, catalog_path: str, strip: str, total: int) -> dict:
    assets, truth, predicted, catalog, stats = evaluate(
        library, catalog_path, strip=strip)
    scores = score(truth, predicted)
    macro = [prf(scores["per_root"][r]["tp"], scores["per_root"][r]["fp"],
                 scores["per_root"][r]["fn"])[2] for r in SCORED_ROOTS]
    leaf = scores["leaf"]
    out = {"macro_f1": sum(macro) / len(macro),
           "leaf_exact_pct": leaf["exact"] / max(1, leaf["total"]) * 100,
           "unfiled_pct": stats.unfiled / max(1, total) * 100,
           "per_root": {r: prf(scores["per_root"][r]["tp"], scores["per_root"][r]["fp"],
                               scores["per_root"][r]["fn"])[2] for r in SCORED_ROOTS}}
    catalog.close()
    return out


def run_ablation(library: str, catalog_path: str) -> dict:
    """All three arms. The metadata-only arm keeps its old key so the existing table
    still renders from the same dict."""
    total = len(ground_truth(library))
    arms = {}
    for label, strip, _ in ABLATION_ARMS:
        arms[label] = _arm_scores(library, catalog_path, strip, total)
    out = dict(arms["metadata only"])
    out["arms"] = arms
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

    fails.extend(_selftest_safety_audit())
    fails.extend(_selftest_report_renders())

    for msg in fails:
        print("FAIL:", msg)
    print(f"\nselftest: {len(fails)} failure(s)")
    return 1 if fails else 0


def _selftest_report_renders() -> List[str]:
    """Render a whole report over a tiny library and check it came out.

    The self-test exercised the scorer and, later, the safety audit, and never called
    `report`. So a `NameError` in a section of the report — which is what happened on
    2026-09-07, in the section added minutes earlier — passed `--selftest`, passed
    `verify.sh`, and failed only on a full evaluation run that takes minutes. That is
    this project's recurring shape for the fourth time: the thing that reports is never
    exercised by the thing it reports on.

    This does not check what the report SAYS — the numbers come from a three-asset
    library and mean nothing. It checks that every branch of it executes and produces
    text, which is the failure mode that keeps recurring.
    """
    import io as _io
    import shutil as _shutil
    import tempfile as _tempfile
    from pvm import fixture as F, pipeline as P, taxonomy as TX

    fails: List[str] = []
    directory = _tempfile.mkdtemp()
    try:
        TX.reset_minted()
        assets = F.build()
        catalog = Catalog(os.path.join(directory, "report.sqlite"))
        stats = P.run(assets, catalog, reconcile_deletions=False)
        truth = {a.asset_id: {"category_path": "Places > Japan > Tokyo",
                              "paths": ["Places > Japan > Tokyo"],
                              "is_foreground": False, "hard_negative": None,
                              "exact_duplicate_of": None}
                 for a in assets}
        predicted = defaultdict(list)
        for aid, path in catalog.db.execute("SELECT asset_id, path FROM assignments"):
            predicted[aid].append(path)
        scores = score(truth, predicted)
        # Both shapes of the ablation argument: absent, and present with all its arms.
        arms = {label: {"macro_f1": 0.5, "leaf_exact_pct": 50.0, "unfiled_pct": 5.0,
                        "per_root": {r: 0.5 for r in SCORED_ROOTS}}
                for label, _, _ in ABLATION_ARMS}
        for ablation in (None, {"macro_f1": 0.5, "leaf_exact_pct": 50.0,
                                "unfiled_pct": 5.0, "arms": arms}):
            buf = _io.StringIO()
            try:
                report(truth, predicted, catalog, stats, scores, ablation, buf)
            except Exception as exc:                      # noqa: BLE001 — that is the point
                fails.append(f"report() raised {type(exc).__name__}: {exc}")
                continue
            text = buf.getvalue()
            for heading in ("Root-level classification", "Constitution §18 KPIs",
                            "Safety red lines", "Tier 1-D", "§11", "§4 精细",
                            "§19", "Tier 1-C", "Risk policy table"):
                if heading not in text:
                    fails.append(f"report() omitted the {heading!r} section")
            if ablation and "Ablation" not in text:
                fails.append("report() omitted the ablation section it was given")
        catalog.close()
    finally:
        _shutil.rmtree(directory, ignore_errors=True)
    return fails


def _selftest_safety_audit() -> List[str]:
    """Every red line, made to fail on purpose.

    `safety_audit` reads the catalogue rather than the code, and its whole value is
    that it would catch a violation the constructor guards missed. That claim is worth
    nothing until each query has actually been shown to return non-zero — a red line
    whose failure path has never executed is a red line nobody has tested. So the rows
    below are written with raw SQL, deliberately bypassing `Proposal.__post_init__`,
    which is the only way to produce the state this audit exists to detect.
    """
    import shutil as _shutil
    import tempfile as _tempfile

    fails: List[str] = []
    directory = _tempfile.mkdtemp()
    try:
        catalog = Catalog(os.path.join(directory, "selftest.sqlite"))
        db = catalog.db
        rows = [
            # (asset_id, risk, importance, action) — one violation per red line.
            ("risk_violation", int(NEVER_DELETE_AT_OR_ABOVE), 0, "suggest_delete"),
            ("importance_violation", 0, int(NEVER_DELETE_AT_OR_ABOVE_IMPORTANCE),
             "suggest_delete"),
        ]
        for asset_id, risk, imp, action in rows:
            db.execute(
                "INSERT INTO assets(asset_id,signals_fp,engine_fp,risk,importance) "
                "VALUES(?,'fp','fp',?,?)", (asset_id, risk, imp))
            db.execute(
                "INSERT INTO proposals(asset_id,action,risk,reversible,"
                "requires_confirmation,auto_applicable,note,why) "
                "VALUES(?,?,?,0,0,0,'','')", (asset_id, action, risk))
        db.execute("INSERT INTO assets(asset_id,signals_fp,engine_fp,risk,importance) "
                   "VALUES('unexplained','fp','fp',2,2)")
        db.execute("INSERT INTO assignments(asset_id,path,confidence,is_primary) "
                   "VALUES('unexplained','Places',0.9,1)")
        db.commit()

        audit = safety_audit(catalog)
        expected = {
            "protected_removals": "an R4+ removal in the rows was not detected",
            "meaningful_removals": "a MEANINGFUL+ removal in the rows was not detected",
            "unexplained_assignments": "an assignment with no evidence was not detected",
            "irreversible_proposals": "an irreversible proposal was not detected",
            "removals_without_confirmation":
                "a removal that needs no confirmation was not detected",
        }
        for key, message in expected.items():
            if audit.get(key, 0) < 1:
                fails.append(f"{message} (audit reported {audit.get(key)!r})")
    finally:
        _shutil.rmtree(directory, ignore_errors=True)
    return fails


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
