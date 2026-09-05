#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T0-B and T0-D analyzers — verdicts computed from pre-registered thresholds.

Thresholds come from the protocols and were fixed before any participant was
recruited (AB-7). They are not revisable to fit the data, so they live in code as
constants and the verdict is arithmetic, not narrative.

SEPARATION RULE (Owner instruction, DEC-014) is ENFORCED, not merely respected:
this tool refuses to emit a combined verdict, writes two separate deliverables, and
will abort if asked to read one study's data into the other's analysis. T0-B and
T0-D answer different questions, can dissociate in both directions, and neither may
be cited as evidence for the other.

Honesty features that are easy to omit and expensive to lack:
  · Wilson confidence intervals on every proportion. At n=10, "70%" is 7 people and
    the interval is enormous. Reporting the point estimate alone would overstate
    what a ten-person study can support.
  · Sessions failing the fair-configuration check are EXCLUDED from data and counted
    as pilots (PF-07). A rigged win is worse than a loss.
  · Cohen's kappa on the two blind coders for P-2. Agreement that is no better than
    chance means the coding is not evidence.
  · A blank counter-evidence field is reported as a finding about the session, not
    silently treated as "nothing went wrong" (AB-6, AB-12).

    python analyze_studies.py b --csv-participants t0b_participants.csv --csv-tasks t0b_tasks.csv
    python analyze_studies.py d --csv t0d_participants.csv
    python analyze_studies.py selftest
"""

import argparse, csv, io, math, os, sys, statistics
from collections import defaultdict
from datetime import datetime
# Output is UTF-8 regardless of console locale (PF-10 — cp936 cannot encode the
# report glyphs and the tool would die after doing all the work).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


MIN_N = 15   # protocol §8.1: raised from 10 — at n=10 only a UNANIMOUS
             # result can clear a 70% threshold, so 10 and 70% were
             # mutually inconsistent (DEC-021)

# --- pre-registered thresholds, protocol T0-B §8 ---------------------------
P = {
    "P1_prefer_prototype": 0.70,
    "P2_structural_reason": 0.70,
    "P3_tasks_won_min": 4,          # of 6 retrieval tasks, on median time AND steps
    "P5_level1_correct": 0.60,
    "P5_full_path_correct": 0.40,
    "P6_spontaneous_organised": 0.50,
}
# --- pre-registered thresholds, protocol T0-D §7 ---------------------------
D = {
    "DP1_assisted_or_autonomous": 0.70,
    "DP2_autonomous": 0.40,
    "DP3_comprehend_20s": 0.70,
    "DP4_identify_work_done": 0.60,
    "DP5_protect_high_risk": 0.80,
    "DP5_auto_low_risk": 0.60,
    "DP6_recoverability_shift": 0.50,
}
RETRIEVAL_TASKS = ["T1", "T2", "T3", "T4", "T5", "T6"]   # T7 is the inverted effort task
HIGH_RISK = ["tol_id", "tol_contract"]
LOW_RISK = ["tol_code", "tol_meme"]


def yes(v):
    return str(v).strip().lower() in ("y", "yes", "true", "1")


def num(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def wilson(k, n, z=1.96):
    """95% CI for a proportion. At small n the interval is the honest headline."""
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (p, max(0.0, centre - half), min(1.0, centre + half))


def prop_line(label, k, n, threshold):
    p, lo, hi = wilson(k, n)
    verdict = "PASS" if p >= threshold else "FAIL"
    # If the threshold sits inside the CI, the study cannot actually resolve it.
    inconclusive = lo < threshold < hi
    note = "  ← CI spans the threshold; underpowered to decide" if inconclusive else ""
    return (f"| {label} | {k}/{n} | {p*100:.0f}% | {lo*100:.0f}–{hi*100:.0f}% | "
            f"{threshold*100:.0f}% | **{verdict}**{note} |", verdict, inconclusive)


def cohens_kappa(a, b):
    """Agreement between two blind coders, corrected for chance."""
    pairs = [(x, y) for x, y in zip(a, b) if x and y]
    if not pairs:
        return None
    labels = sorted({v for pr in pairs for v in pr})
    n = len(pairs)
    obs = sum(1 for x, y in pairs if x == y) / n
    exp = sum((sum(1 for x, _ in pairs if x == L) / n) *
              (sum(1 for _, y in pairs if y == L) / n) for L in labels)
    if exp >= 1.0:
        return 1.0
    return (obs - exp) / (1 - exp)


def usable(rows, flag="fair_config_ok"):
    """PF-07: sessions without a verified fair configuration are pilots, not data."""
    good = [r for r in rows if yes(r.get(flag))]
    pilots = [r for r in rows if not yes(r.get(flag))]
    return good, pilots


# ===========================================================================
# T0-B
# ===========================================================================

def analyse_b(participants, tasks):
    good, pilots = usable(participants)
    n = len(good)
    L, w = [], None
    w = L.append

    w("# T0-B · RETRIEVAL ENTRY — results")
    w(f"Generated {datetime.now().isoformat(timespec='seconds')} by `analyze_studies.py`")
    w("")
    w("> **This file contains T0-B only.** T0-D results live in a separate deliverable "
      "and neither study may be cited as evidence for the other (DEC-014).")
    w("")
    w(f"Participants recorded: **{len(participants)}** · usable: **{n}** · "
      f"excluded as pilots (fair-configuration not verified): **{len(pilots)}**")
    if pilots:
        w("")
        w("Excluded sessions — PF-07, a rigged win is worse than a loss:")
        for r in pilots:
            w(f"- {r.get('pid')} — {r.get('notes') or 'fair_config_ok not set'}")
    w("")
    if n < MIN_N:
        w(f"> ⚠️ **UNDERPOWERED — {n} usable participants, protocol requires ≥ {MIN_N}.** "
          f"Figures below are reported for completeness. **No PASS may be claimed from "
          f"this sample**, and the Tier 0 gate must record the study as incomplete.")
        w("")

    w("## Pre-registered criteria")
    w("")
    w("| Criterion | Count | Rate | 95% CI | Threshold | Verdict |")
    w("|---|---|---|---|---|---|")

    results, inconclusive_any = {}, False

    k = sum(1 for r in good if str(r.get("forced_choice", "")).strip().lower()
            in ("prototype", "b", "proto"))
    line, v, inc = prop_line("**P-1** prefers prototype as first stop", k, n,
                             P["P1_prefer_prototype"])
    w(line); results["P-1"] = v; inconclusive_any |= inc

    choosers = [r for r in good if str(r.get("forced_choice", "")).strip().lower()
                in ("prototype", "b", "proto")]
    k2 = sum(1 for r in choosers if str(r.get("reason_code_c1", "")).strip().upper() == "STRUCTURAL")
    line, v, inc = prop_line("**P-2** of those, structural reason (coder 1)",
                             k2, len(choosers), P["P2_structural_reason"])
    w(line); results["P-2"] = v; inconclusive_any |= inc

    k5a = sum(1 for r in good if yes(r.get("passport_pred_proto_level1")))
    line, v, inc = prop_line("**P-5a** passport predicted, level 1", k5a, n,
                             P["P5_level1_correct"])
    w(line); inconclusive_any |= inc
    k5b = sum(1 for r in good if yes(r.get("passport_pred_proto_full")))
    line, v2, inc = prop_line("**P-5b** passport predicted, FULL path", k5b, n,
                              P["P5_full_path_correct"])
    w(line); results["P-5"] = "PASS" if v == "PASS" and v2 == "PASS" else "FAIL"
    inconclusive_any |= inc

    k6 = sum(1 for r in good if yes(r.get("org_vocab_proto")))
    line, v, inc = prop_line("**P-6** spontaneous 'it is organised' remark", k6, n,
                             P["P6_spontaneous_organised"])
    w(line); results["P-6"] = v; inconclusive_any |= inc
    w("")

    # ---- P-3: per-task median comparison ---------------------------------
    ok_pids = {r["pid"] for r in good}
    by = defaultdict(lambda: defaultdict(list))
    for t in tasks:
        if t.get("pid") not in ok_pids:
            continue
        arm = str(t.get("arm", "")).strip().lower()
        arm = "proto" if arm in ("b", "proto", "prototype") else "apple"
        by[t.get("task")][arm].append(t)

    w("## P-3 · Task performance (median, usable sessions only)")
    w("")
    w("| Task | Apple time | Proto time | Apple steps | Proto steps | Proto wins both |")
    w("|---|---|---|---|---|---|")
    wins = 0
    for task in RETRIEVAL_TASKS:
        a, b = by[task]["apple"], by[task]["proto"]
        if not a or not b:
            w(f"| {task} | — | — | — | — | NO DATA |")
            continue
        at = statistics.median(num(x.get("time_s")) for x in a)
        bt = statistics.median(num(x.get("time_s")) for x in b)
        as_ = statistics.median(num(x.get("steps")) for x in a)
        bs = statistics.median(num(x.get("steps")) for x in b)
        won = bt < at and bs < as_
        wins += 1 if won else 0
        w(f"| {task} | {at:.0f}s | {bt:.0f}s | {as_:.0f} | {bs:.0f} | "
          f"{'yes' if won else 'no'} |")
    v3 = "PASS" if wins >= P["P3_tasks_won_min"] else "FAIL"
    results["P-3"] = v3
    w("")
    w(f"**P-3: prototype wins both medians on {wins} of {len(RETRIEVAL_TASKS)} tasks "
      f"(threshold ≥{P['P3_tasks_won_min']}) → {v3}**")
    w("")

    # ---- T7 baseline ------------------------------------------------------
    t7 = [t for t in tasks if t.get("task") == "T7" and t.get("pid") in ok_pids]
    if t7:
        w("## T7 · Manual burst cleanup — the baseline our differentiator must beat")
        med = statistics.median(num(x.get("time_s")) for x in t7)
        w("")
        w(f"Median {med:.0f}s to manually keep the best of 8 near-identical frames. "
          f"Nothing was built to solve this (DEC-011); the number exists so Tier 2-B "
          f"has something measured to improve on.")
        w("")

    # ---- coder agreement --------------------------------------------------
    kap = cohens_kappa([r.get("reason_code_c1") for r in choosers],
                       [r.get("reason_code_c2") for r in choosers])
    w("## Coder agreement (P-2)")
    w("")
    if kap is None:
        w("**No second coder recorded.** P-2 requires blind coding by two people; "
          "a single coder's classification of their own study is not evidence.")
        results["P-2"] = "NO DATA"
    else:
        quality = ("poor — the coding is not evidence" if kap < 0.4 else
                   "moderate" if kap < 0.6 else "substantial" if kap < 0.8 else "strong")
        w(f"Cohen's kappa = **{kap:.2f}** ({quality}).")
        if kap < 0.4:
            w("")
            w("> Agreement barely above chance. **P-2 should be treated as NO DATA** "
              "until the coding scheme is tightened and re-run.")
            results["P-2"] = "NO DATA"
    w("")

    # ---- overall ----------------------------------------------------------
    w("## Verdict")
    w("")
    overall = ("PASS" if results.get("P-1") == "PASS" and results.get("P-3") == "PASS"
               else "GO WITH CONSTRAINTS" if results.get("P-1") == "PASS"
               else "FAIL")
    if n < MIN_N:
        overall = "INCOMPLETE (underpowered)"
    w(f"**{overall}** — PASS requires P-1 and P-3.")
    w("")
    for k_, v_ in results.items():
        w(f"- {k_}: {v_}")
    if overall == "FAIL":
        w("")
        w("> Per Tier 0 §3, a B FAIL is a **NO-GO / PIVOT**, not a prompt to add "
          "features. The differentiation would not have been established.")
    if inconclusive_any:
        w("")
        w("> ⚠️ One or more thresholds fall **inside** the confidence interval. The "
          "sample cannot resolve those criteria in either direction; report them as "
          "undecided rather than as a result.")

    # ---- counter-evidence -------------------------------------------------
    w("")
    w("## Counter-evidence (AB-6)")
    w("")
    blank = [r["pid"] for r in good if not str(r.get("counter_evidence", "")).strip()]
    if blank:
        w(f"**{len(blank)} of {n} sessions recorded no counter-evidence at all** "
          f"({', '.join(blank)}). This is reported as a finding about those sessions, "
          f"not as an absence of problems. A usability session in which nothing "
          f"confused anyone is rare enough to be worth doubting.")
    else:
        w("Counter-evidence recorded for every session.")
    for r in good:
        ce = str(r.get("counter_evidence", "")).strip()
        if ce:
            w(f"- **{r['pid']}**: {ce}")

    w("")
    w("## Limitations (must appear in the summary, not a footnote)")
    w("- **L-1** The prototype's catalogue and category tree were hand-made for the "
      "test library. A PASS shows the interface concept works *if* the engine can be "
      "built — which Tier 1 must prove separately.")
    w("- **L-2** Participants navigated a persona library, not their own life.")
    w("- **L-3** Novelty may inflate preference; P-2 exists to detect it.")
    w("- **L-6** Arm B is a web prototype, arm A a native app. This works *against* "
      "arm B, so a PASS is conservative.")
    return "\n".join(L)


# ===========================================================================
# T0-D
# ===========================================================================

def analyse_d(rows):
    n = len(rows)
    L = []
    w = L.append
    w("# T0-D · AUTONOMOUS MANAGEMENT VALUE PROPOSITION — results")
    w(f"Generated {datetime.now().isoformat(timespec='seconds')} by `analyze_studies.py`")
    w("")
    w("> **This file contains T0-D only.** T0-B results live in a separate deliverable "
      "and neither study may be cited as evidence for the other (DEC-014).")
    w("")
    w("Constitution §7 requires that the automation-tolerance bet be validated by real "
      "user testing rather than engineer assumption. This is that test.")
    w("")
    w(f"Participants: **{n}**")
    if n < MIN_N:
        w("")
        w(f"> ⚠️ **UNDERPOWERED — {n} participants, protocol requires ≥ {MIN_N}.** "
          f"No PASS may be claimed from this sample.")
    w("")
    w("## Pre-registered criteria")
    w("")
    w("| Criterion | Count | Rate | 95% CI | Threshold | Verdict |")
    w("|---|---|---|---|---|---|")

    res, inc_any = {}, False
    mode = [str(r.get("mode_choice", "")).strip() for r in rows]

    k = sum(1 for m in mode if m in ("2", "3"))
    line, v, inc = prop_line("**D-P1** chose assisted or autonomous over full control",
                             k, n, D["DP1_assisted_or_autonomous"])
    w(line); res["D-P1"] = v; inc_any |= inc

    k = sum(1 for m in mode if m == "3")
    line, v, inc = prop_line("**D-P2** chose fully autonomous", k, n, D["DP2_autonomous"])
    w(line); res["D-P2"] = v; inc_any |= inc

    k = sum(1 for r in rows if 0 < num(r.get("ledger_comprehension_s"), 999) <= 20)
    line, v, inc = prop_line("**D-P3** understood the ledger within 20s", k, n,
                             D["DP3_comprehend_20s"])
    w(line); res["D-P3"] = v; inc_any |= inc

    k = sum(1 for r in rows if yes(r.get("identified_work_done")))
    line, v, inc = prop_line("**D-P4** identified unprompted that work was done", k, n,
                             D["DP4_identify_work_done"])
    w(line); res["D-P4"] = v; inc_any |= inc

    prot = sum(1 for r in rows if all(str(r.get(c, "")).strip().lower() == "never"
                                      for c in HIGH_RISK))
    line, vp, incp = prop_line("**D-P5a** protect ID *and* contract", prot, n,
                               D["DP5_protect_high_risk"])
    w(line); inc_any |= incp
    auto = sum(1 for r in rows if all(str(r.get(c, "")).strip().lower() == "auto"
                                      for c in LOW_RISK))
    line, va, inca = prop_line("**D-P5b** auto-handle expired codes *and* dup memes",
                               auto, n, D["DP5_auto_low_risk"])
    w(line); inc_any |= inca
    res["D-P5"] = "PASS" if vp == "PASS" and va == "PASS" else "FAIL"

    k = sum(1 for r in rows if yes(r.get("recoverability_changed")))
    line, v, inc = prop_line("**D-P6** recoverability shifted at least one answer", k, n,
                             D["DP6_recoverability_shift"])
    w(line); res["D-P6"] = v; inc_any |= inc
    w("")

    # ---- risk gradient: the shape matters more than any single number ------
    w("## Is tolerance actually risk-graded? (D-4)")
    w("")
    order = [("tol_code", "expired verification code", "R1"),
             ("tol_meme", "meme downloaded 4x", "R0"),
             ("tol_burst", "8 near-identical burst frames", "R2"),
             ("tol_meal", "photo of a meal", "R2"),
             ("tol_receipt", "receipt", "R4"),
             ("tol_workdoc", "work document screenshot", "R4"),
             ("tol_family", "family photo", "R3/R6"),
             ("tol_id", "ID card", "R5"),
             ("tol_contract", "signed contract", "R5")]
    w("| Content | §6 level | auto | ask | never |")
    w("|---|---|---|---|---|")
    autos = []
    for col, label, lvl in order:
        vals = [str(r.get(col, "")).strip().lower() for r in rows]
        a, k_, nv = vals.count("auto"), vals.count("ask"), vals.count("never")
        autos.append(a / n if n else 0)
        w(f"| {label} | {lvl} | {a} | {k_} | {nv} |")
    w("")
    low_mean = statistics.mean(autos[:2]) if n else 0
    high_mean = statistics.mean(autos[-2:]) if n else 0
    graded = low_mean > high_mean + 0.3
    w(f"Auto-handling rate: low-risk (R0/R1) **{low_mean*100:.0f}%** vs high-risk (R5) "
      f"**{high_mean*100:.0f}%** → pattern is **{'GRADED' if graded else 'FLAT'}**.")
    if not graded:
        w("")
        w("> ⚠️ **This is the important negative result.** A flat pattern means the "
          "entire R0–R6 architecture rests on a distinction users do not actually make. "
          "Report it plainly; do not average it away.")
    w("")

    # ---- review burden ----------------------------------------------------
    cross = [num(r.get("queue_crossover")) for r in rows if num(r.get("queue_crossover")) > 0]
    if cross:
        med = statistics.median(cross)
        w("## Human Review Burden — first empirical §18 target")
        w("")
        w(f"Median crossover from *handled for me* to *homework*: **{med:.0f} items** "
          f"out of ~10,000 → **{med/10:.1f} per 1,000 assets**.")
        w("")
        w("This replaces an engineering guess with a measured number and should become "
          "the §18 Human Review Burden target. It also replaces the invented \"23\" in "
          "the T0-C2 landing copy.")
        w("")

    # ---- ledger variants --------------------------------------------------
    w("## Ledger variants")
    w("")
    w("| Variant | n | understood ≤20s | said work was done | chose autonomous |")
    w("|---|---|---|---|---|")
    for var in ("V1", "V2", "V3", "V4"):
        vr = [r for r in rows if str(r.get("ledger_variant", "")).strip().upper() == var]
        if not vr:
            w(f"| {var} | 0 | — | — | — |"); continue
        c = sum(1 for r in vr if 0 < num(r.get("ledger_comprehension_s"), 999) <= 20)
        d_ = sum(1 for r in vr if yes(r.get("identified_work_done")))
        a = sum(1 for r in vr if str(r.get("mode_choice", "")).strip() == "3")
        w(f"| {var} | {len(vr)} | {c}/{len(vr)} | {d_}/{len(vr)} | {a}/{len(vr)} |")
    w("")
    w("> **V1 vs V4 is the sharpest comparison available**: identical facts, opposite "
      "order. If V4 reads as homework and V1 as a service, presentation — not "
      "capability — is carrying the value proposition.")
    w("")

    # ---- verdict ----------------------------------------------------------
    w("## Verdict")
    w("")
    overall = ("PASS" if res.get("D-P1") == "PASS" and res.get("D-P5") == "PASS"
               else "GO WITH CONSTRAINTS" if res.get("D-P1") == "PASS"
               else "FAIL")
    if n < MIN_N:
        overall = "INCOMPLETE (underpowered)"
    w(f"**{overall}** — PASS requires D-P1 **and** D-P5.")
    w("")
    for k_, v_ in res.items():
        w(f"- {k_}: {v_}")
    if res.get("D-P1") == "PASS" and res.get("D-P2") == "FAIL":
        w("")
        w("> **GO WITH CONSTRAINTS reading:** users want assistance but not full "
          "autonomy. Ship Version 2 as the default and make Version 3 opt-in. "
          "Constitution §5/§17 are unaffected — only the *default* changes.")
    if res.get("D-P1") == "FAIL":
        w("")
        w("> ⛔ **D-P1 FAIL contradicts Constitution §5–§7 and §17.** Per PF-08 this is "
          "**escalated to the Owner as a potential Kill result** and must not be "
          "quietly redesigned around.")
    if inc_any:
        w("")
        w("> ⚠️ One or more thresholds fall inside the confidence interval; those "
          "criteria are undecided, not decided.")

    w("")
    w("## Counter-evidence (AB-12)")
    w("")
    blank = [r.get("pid") for r in rows if not str(r.get("counter_evidence", "")).strip()]
    if blank:
        w(f"**{len(blank)} of {n} sessions recorded none** ({', '.join(map(str, blank))}). "
          f"§7 is a bet, and this study exists to be able to lose. A sheet with no "
          f"counter-evidence is a sheet that was not filled in properly.")
    for r in rows:
        ce = str(r.get("counter_evidence", "")).strip()
        if ce:
            w(f"- **{r.get('pid')}**: {ce}")
    w("")
    w("## Limitation (summary, not a footnote)")
    w("- **L-4** The ledger numbers were prepared for a test library. This validates "
      "the product *model*, not the engine. The question asked was not \"does our AI "
      "work\" but \"do users want an AI that does this at all\".")
    return "\n".join(L)


# ===========================================================================

SELF_B_P = """pid,fair_config_ok,forced_choice,reason_code_c1,reason_code_c2,passport_pred_proto_level1,passport_pred_proto_full,org_vocab_proto,counter_evidence,notes
P01,yes,prototype,STRUCTURAL,STRUCTURAL,y,y,y,"got lost in Places once",
P02,yes,prototype,STRUCTURAL,STRUCTURAL,y,y,y,,
P03,yes,apple,OTHER,OTHER,n,n,n,"said ours felt like a website",
P04,yes,prototype,STRUCTURAL,NOVELTY,y,n,y,"expected search on the home screen",
P05,yes,prototype,STRUCTURAL,STRUCTURAL,y,y,n,,
P06,yes,prototype,NOVELTY,NOVELTY,y,n,y,"liked the look more than the structure",
P07,yes,prototype,STRUCTURAL,STRUCTURAL,y,y,y,,
P08,yes,prototype,STRUCTURAL,STRUCTURAL,n,n,y,"Objects category confused them",
P09,no,prototype,STRUCTURAL,STRUCTURAL,y,y,y,,People indexing had not finished
P10,yes,prototype,STRUCTURAL,STRUCTURAL,y,y,n,,
P11,yes,apple,OTHER,OTHER,n,n,n,"preferred what they already knew",
"""

SELF_B_T = "pid,task,arm,success,time_s,steps\n" + "\n".join(
    f"P{i:02d},{t},{arm},F,{base},{steps}"
    for i in range(1, 12) if i != 9
    for t, (at, ast, bt, bst) in {
        "T1": (62, 9, 21, 4), "T2": (95, 14, 44, 7), "T3": (71, 11, 26, 5),
        "T4": (48, 7, 30, 5), "T5": (88, 13, 52, 9), "T6": (77, 12, 33, 6),
        "T7": (110, 18, 104, 17),
    }.items()
    for arm, base, steps in (("apple", at, ast), ("proto", bt, bst))
)

SELF_D = """pid,ledger_variant,mode_choice,ledger_comprehension_s,identified_work_done,tol_code,tol_meme,tol_burst,tol_meal,tol_receipt,tol_workdoc,tol_family,tol_id,tol_contract,recoverability_changed,queue_crossover,counter_evidence
P01,V1,3,12,y,auto,auto,auto,ask,ask,ask,ask,never,never,y,80,"wanted to see the 23 first"
P02,V2,2,18,y,auto,auto,ask,ask,ask,never,never,never,never,y,80,
P03,V3,2,25,n,auto,auto,auto,auto,ask,ask,never,never,never,n,300,"did not trust it without seeing what was protected"
P04,V4,1,14,y,ask,auto,ask,ask,never,never,never,never,never,n,23,"felt like a to-do list"
P05,V1,3,9,y,auto,auto,auto,ask,ask,ask,ask,never,never,y,80,
P06,V2,3,16,y,auto,auto,auto,ask,ask,ask,never,never,never,y,80,
P07,V3,2,22,y,auto,auto,ask,ask,ask,ask,never,never,never,y,80,"asked twice whether delete meant delete"
P08,V4,2,19,n,auto,auto,ask,ask,ask,never,never,never,never,n,23,"read it as homework"
P09,V1,3,11,y,auto,auto,auto,ask,ask,ask,ask,never,never,y,80,
P10,V2,2,17,y,auto,auto,ask,ask,never,ask,never,never,never,y,80,
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("study", choices=["b", "d", "selftest"])
    ap.add_argument("--csv", default=None)
    ap.add_argument("--csv-participants", default=None)
    ap.add_argument("--csv-tasks", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    def rd(path_or_text, is_text=False):
        f = io.StringIO(path_or_text) if is_text else open(path_or_text, newline="",
                                                           encoding="utf-8")
        return list(csv.DictReader(f))

    if a.study == "selftest":
        print("SELFTEST — synthetic sessions, no participant involved.\n"
              "T0-B: 11 recorded, 1 excluded as a pilot, coder disagreement present.\n"
              "T0-D: tolerance deliberately risk-graded; V4 chosen by the two who read "
              "it as homework.\n" + "=" * 70)
        print(analyse_b(rd(SELF_B_P, True), rd(SELF_B_T, True)))
        print("\n" + "=" * 70 + "\n")
        print(analyse_d(rd(SELF_D, True)))
        return

    if a.study == "b":
        if not (a.csv_participants and a.csv_tasks):
            sys.exit("T0-B needs --csv-participants and --csv-tasks")
        text = analyse_b(rd(a.csv_participants), rd(a.csv_tasks))
        default_out = "../evidence/RETRIEVAL_ENTRY_USABILITY_TIER0.md"
    else:
        if not a.csv:
            sys.exit("T0-D needs --csv")
        rows = rd(a.csv)
        # Enforce the separation rule structurally, not by convention.
        if rows and "forced_choice" in rows[0]:
            sys.exit("aborting: this looks like T0-B participant data. The two studies "
                     "are recorded separately and must not be analysed together "
                     "(DEC-014).")
        text = analyse_d(rows)
        default_out = "../evidence/AUTONOMOUS_MGMT_VALUE_PROP_TIER0.md"

    out = a.out or os.path.join(os.path.dirname(os.path.abspath(__file__)), default_out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(text)
    print(text)
    print(f"\nwritten to {out}")


if __name__ == "__main__":
    main()
