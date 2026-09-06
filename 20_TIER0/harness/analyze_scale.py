#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T0-A SCALE SWEEP analyzer — answers "how many photos can this actually take?"

Input: the `PVM_SCALE_RESULT {...}` lines printed by `ScaleBenchmarkTests.swift`
(any file containing them: an xcodebuild log is fine).

Output: measured per-asset cost, a linearity check, and the library-size ceiling
that follows from those costs under the budgets already pre-registered in
`T0A_DEVICE_BENCHMARK_HARNESS_SPEC.md` §8 — imported from `analyze_benchmark.py`
so the two analyzers cannot drift apart.

WHAT THIS MAY AND MAY NOT CONCLUDE (PF-01, P-02):
  · Every number in the input came from the iOS Simulator on a macOS CI runner.
    That is a desktop-class arm64 CPU with no thermal ceiling, no battery, no
    Neural Engine and no photo library.
  · So the ceiling computed here is an OPTIMISTIC CEILING, stamped as such. It can
    say "even the ceiling is too low" — which would be decisive — but it can never
    say "an iPhone passes A1". Only a device can.
  · The device band is a PREDICTION from a stated derate assumption, never a
    measurement, and is printed as a range with the assumption visible.

    python analyze_scale.py --log test.log
    python analyze_scale.py --selftest
"""

import argparse, io, json, os, re, sys

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from analyze_benchmark import BUDGET  # single source of truth for the §8 budgets

MARKER = "PVM_SCALE_RESULT "
HOST_MARKER = "PVM_SCALE_HOST "

# PREDICTION, not measurement. A phone core is slower than a CI Mac core and has a
# thermal ceiling the runner does not; against that, Vision runs on the ANE on device
# and on the CPU in the Simulator, which pushes the other way. The honest statement is
# a wide band with the assumption named, not a single confident multiplier.
DERATE = (2.0, 5.0)   # device wall time = simulator wall time x this range

LIBRARY_SIZES = [5_000, 10_000, 30_000, 50_000, 100_000]


def parse(text):
    rows, host = [], None
    for line in text.splitlines():
        line = line.strip()
        if HOST_MARKER in line:
            host = line.split(HOST_MARKER, 1)[1].strip()
        if MARKER in line:
            payload = line.split(MARKER, 1)[1].strip()
            # xcodebuild sometimes appends its own trailing noise to a printed line.
            end = payload.rfind("}")
            if end == -1:
                continue
            try:
                rows.append(json.loads(payload[:end + 1]))
            except json.JSONDecodeError:
                continue
    rows.sort(key=lambda r: r["n"])
    return rows, host


def fmt_duration(seconds):
    if seconds < 90:
        return f"{seconds:.0f} s"
    if seconds < 5400:
        return f"{seconds/60:.1f} min"
    return f"{seconds/3600:.1f} h"


def linearity(rows):
    """Per-asset cost must stay flat as N grows. If it climbs, something in the
    pipeline is superlinear (an unbounded cache, an index rebuild per row) and the
    extrapolation below is worthless — that finding matters more than the number."""
    if len(rows) < 2:
        return None, "only one corpus size — linearity unknown, extrapolation is unchecked"
    first, last = rows[0]["ms_per_asset"], rows[-1]["ms_per_asset"]
    if first <= 0:
        return None, "zero cost per asset — measurement is broken"
    drift = last / first
    if drift <= 1.25:
        return True, f"flat within 25% ({first:.1f} -> {last:.1f} ms/asset over n={rows[0]['n']}..{rows[-1]['n']})"
    return False, (f"per-asset cost GREW {drift:.2f}x ({first:.1f} -> {last:.1f} ms/asset "
                   f"over n={rows[0]['n']}..{rows[-1]['n']}) — superlinear, do not extrapolate")


def report(rows, host, out):
    w = out.write
    if not rows:
        w("NO DATA — no PVM_SCALE_RESULT lines found.\n")
        w("A missing measurement is never a soft PASS. Check whether the sweep was\n"
          "skipped (grep the log for PVM_SCALE_ENV_CHECK).\n")
        return 2

    best = rows[-1]           # largest corpus = most trustworthy per-asset cost
    lin_ok, lin_note = linearity(rows)

    w("# T0-A SCALE SWEEP — measured\n\n")
    w("**Source: iOS Simulator on a macOS CI runner. NOT a device result (P-02, PF-01).**\n")
    w("No thermal, battery, jetsam or Neural Engine number can come from here, and the\n")
    w("throughput below is an optimistic ceiling for a phone rather than a phone number.\n\n")
    if host:
        w(f"Host: `{host}`\n\n")

    w("## Measured per-asset cost\n\n")
    w("| n | wall | ms/asset | assets/s | decode | L1 | OCR (per OCR'd) | OCR (amortised) | embed | store | gate ratio | peak MB | index B/asset |\n")
    w("|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|\n")
    for r in rows:
        w(f"| {r['n']} | {fmt_duration(r['wall_s'])} | {r['ms_per_asset']:.1f} | {r['assets_per_s']:.1f} | "
          f"{r['decode_ms_per_asset']:.1f} | {r['l1_ms_per_asset']:.1f} | {r['ocr_ms_per_ocr_asset']:.1f} | "
          f"{r['ocr_ms_per_asset']:.1f} | {r['embed_ms_per_asset']:.1f} | {r['store_ms_per_asset']:.2f} | "
          f"{r['ocr_gate_ratio']*100:.0f}% | {r['peak_footprint_mb']:.0f} | {r['index_bytes_per_asset']:.0f} |\n")
    w("\nAll times are milliseconds per asset unless the column says otherwise.\n\n")

    w("## Linearity\n\n")
    w(f"{'OK' if lin_ok else ('UNKNOWN' if lin_ok is None else 'FAIL')} — {lin_note}\n\n")

    # ---- where the cost actually goes -------------------------------------
    stages = [("thumbnail decode", best["decode_ms_per_asset"]),
              ("L1 signals (dHash + text likelihood)", best["l1_ms_per_asset"]),
              ("OCR gate decision", best["gate_ms_per_asset"]),
              ("gated OCR (amortised over all assets)", best["ocr_ms_per_asset"]),
              ("embedding (feature print)", best["embed_ms_per_asset"]),
              ("SQLite upsert", best["store_ms_per_asset"])]
    total = sum(v for _, v in stages) or 1.0
    w("## Where the time goes (n=%d)\n\n" % best["n"])
    w("| stage | ms/asset | share |\n|---|--:|--:|\n")
    for name, v in sorted(stages, key=lambda x: -x[1]):
        w(f"| {name} | {v:.2f} | {v/total*100:.0f}% |\n")
    w("\n")

    # C-1's own prediction, now checkable.
    ocr_share = best["ocr_ms_per_asset"] / total * 100
    embed_share = best["embed_ms_per_asset"] / total * 100
    w("**C-1 check.** The spec predicted OCR would dominate per-asset cost by roughly "
      f"an order of magnitude over embedding, so that the *gate ratio* — not raw OCR "
      f"speed — would decide A1. Measured at a {best['ocr_gate_ratio']*100:.0f}% gate ratio: "
      f"OCR is {ocr_share:.0f}% of per-asset cost and embedding is {embed_share:.0f}%. ")
    if best["ocr_ms_per_ocr_asset"] > 0 and best["embed_ms_per_asset"] > 0:
        ratio = best["ocr_ms_per_ocr_asset"] / best["embed_ms_per_asset"]
        w(f"Per asset actually OCR'd, OCR costs {ratio:.1f}x an embedding.\n\n")
        if ratio >= 5:
            w("Prediction holds on this host.\n\n")
        else:
            w("**On this host the prediction is inverted — and this is the one number in "
              "the table that the Simulator is least entitled to decide.** "
              "`VNGenerateImageFeaturePrintRequest` is precisely the stage that runs on "
              "the Neural Engine on a device and on the CPU here, so the embedding cost "
              "measured above is inflated by an unknown factor that Vision's text "
              "recognition does not pay in the same proportion. The honest reading is "
              "that C-1 is **now in doubt and no longer safe to design around**, not "
              "that it is refuted: refuting it needs a device. What follows either way "
              "is that the embedding — not the OCR gate — is where the next optimisation "
              "belongs unless a device says otherwise, because the gate can at best "
              "remove a stage that costs a fraction of the one nothing gates.\n\n")
    else:
        w("\n\n")

    # ---- the answer the Owner asked for -----------------------------------
    ms = best["ms_per_asset"]
    w("## Ceiling — how many photos fit the budget\n\n")
    w("Budgets are the ones pre-registered in spec §8, unchanged: "
      f"foreground cold index ≤ {BUDGET['cold_foreground_100k_s']/60:.0f} min, "
      f"background cold index ≤ {BUDGET['cold_background_100k_s']/3600:.0f} h.\n\n")

    w("### A · Simulator ceiling (measured, optimistic)\n\n")
    w("| library | index time | vs 90 min foreground | vs 8 h background |\n|--:|--:|:--|:--|\n")
    for n in LIBRARY_SIZES:
        t = n * ms / 1000
        fg = "fits" if t <= BUDGET["cold_foreground_100k_s"] else f"over by {fmt_duration(t - BUDGET['cold_foreground_100k_s'])}"
        bg = "fits" if t <= BUDGET["cold_background_100k_s"] else f"over by {fmt_duration(t - BUDGET['cold_background_100k_s'])}"
        w(f"| {n:,} | {fmt_duration(t)} | {fg} | {bg} |\n")
    max_fg = int(BUDGET["cold_foreground_100k_s"] * 1000 / ms)
    max_bg = int(BUDGET["cold_background_100k_s"] * 1000 / ms)
    w(f"\n**Ceiling: {max_fg:,} assets in the 90-minute foreground budget; "
      f"{max_bg:,} assets in the 8-hour background budget.**\n\n")
    w("**This is one sample, not a constant.** Two runs of identical code over an "
      "identical corpus on 2026-09-06 came back at 104.7 and 154.1 ms/asset — a 1.47x "
      "spread, and ceilings of 51,567 and 35,049 from the same commit. Shared CI "
      "runners contend for CPU; the deterministic outputs (index bytes, memory growth, "
      "gate ratio, failure count) matched exactly across both, so the variance is the "
      "host and not the harness. Quote the ceiling as a band, never as a figure, and "
      "treat a single run's number as the sample it is.\n\n")

    w("### B · Device band (PREDICTION — no device has run this)\n\n")
    w(f"Assumption, stated so it can be attacked: a phone takes **{DERATE[0]:.0f}x to "
      f"{DERATE[1]:.0f}x** the Simulator's wall time for this pipeline. Nothing here "
      "measures that factor; it is a modelling band, and the real number replaces it the "
      "day HG-1 clears.\n\n")
    w("| library | device index time (band) | 90-min foreground |\n|--:|--:|:--|\n")
    for n in LIBRARY_SIZES:
        lo, hi = n * ms / 1000 * DERATE[0], n * ms / 1000 * DERATE[1]
        verdict = ("fits" if hi <= BUDGET["cold_foreground_100k_s"]
                   else "fails" if lo > BUDGET["cold_foreground_100k_s"] else "straddles the budget")
        w(f"| {n:,} | {fmt_duration(lo)} – {fmt_duration(hi)} | {verdict} |\n")
    w(f"\n**Predicted device ceiling in the 90-minute foreground budget: "
      f"{int(max_fg / DERATE[1]):,} – {int(max_fg / DERATE[0]):,} assets.** PREDICTION, "
      "not a result. It may never be written into `DEVICE_BENCHMARK_TIER0.csv`.\n\n")

    # ---- supporting budgets -----------------------------------------------
    w("## Supporting budgets\n\n")
    bpa = best["index_bytes_per_asset"]
    ok_idx = bpa <= BUDGET["index_bytes_per_asset"]
    emb = best["embedding_bytes_per_asset"]
    w(f"- Index size: **{bpa:.0f} B/asset** vs budget {BUDGET['index_bytes_per_asset']} — "
      f"{'within budget' if ok_idx else 'OVER BUDGET'}. "
      f"At 100k that is {bpa*100_000/1e9:.2f} GB.\n")
    w(f"  The embedding blob alone is {emb:.0f} B/asset")
    if not ok_idx and emb > 0:
        w(f", i.e. the whole overage and then some: everything else comes to "
          f"{bpa - emb:.0f} B/asset, which is inside the budget on its own.\n")
        w("  So this is a design choice to make, not a bug to fix — store the feature "
          "print and pay the bytes, quantise it, or recompute it on demand and pay the "
          "time again. The budget was written before anyone knew what a feature print "
          "weighed.\n")
    else:
        w(".\n")
    growth = best["peak_footprint_mb"] - best["start_footprint_mb"]
    w(f"- Memory: **{growth:+.0f} MB of growth** across the run (absolute footprint "
      f"{best['peak_footprint_mb']:.0f} MB). Read the growth, not the absolute: the "
      "absolute includes the whole test host inside a Simulator and is not a phone "
      "number, while growth that tracks n is a leak wherever it runs. The Simulator has "
      "no jetsam, so neither figure is an A3 result.\n")
    w(f"- Failed assets: {best['failed']} of {best['n']}.\n\n")

    # ---- what this cannot say ---------------------------------------------
    w("## What this run still cannot answer\n\n")
    w("- **A2 thermal** — the Simulator has no thermal state. Untested.\n")
    w("- **A3 survivability** — no jetsam, no BGProcessingTask expiry. Untested, and A3 is the fatal one.\n")
    w("- **A4 incrementality** — needs a real `PHPhotoLibraryChangeObserver` on a real library. Untested.\n")
    w("- **iCloud** — no optimised-storage library exists here, so the §6 variable is untouched.\n")
    w("- **Video** — MNI-2 / FC-2: images only. A mixed library is worse than this.\n")
    w("- **The stage mix itself** — the Simulator has no Neural Engine, so the split "
      "between the embedding and OCR above is the least transferable row in the report. "
      "The total is an optimistic ceiling; the *proportions* may not survive contact "
      "with an ANE at all.\n")
    w("- **FC-1** — the dHash is computed and never used to skip work, so every duplicate "
      "pays full price. The number above measures the naive pipeline, and is pessimistic "
      "by exactly the duplicate rate.\n")
    return 0 if lin_ok is not False else 1


SELFTEST_LOG = """
noise before
PVM_SCALE_HOST cores=4 active=4 ram_gb=14.0 os=Version 18.0
2026-09-06 10:00:00 PVM_SCALE_RESULT {"n":200,"indexed":200,"failed":0,"wall_s":8.000,"ms_per_asset":40.000,"assets_per_s":25.000,"decode_ms_per_asset":12.000,"l1_ms_per_asset":1.000,"gate_ms_per_asset":0.010,"ocr_ms_per_ocr_asset":60.000,"ocr_ms_per_asset":15.000,"embed_ms_per_asset":11.000,"store_ms_per_asset":0.500,"ocr_attempted":50,"ocr_gated_out":150,"ocr_gate_ratio":0.250,"embed_attempted":200,"start_footprint_mb":40.000,"peak_footprint_mb":95.000,"index_bytes_total":320000,"index_bytes_per_asset":1600.000,"embedding_bytes_per_asset":1200.000}
PVM_SCALE_RESULT {"n":1000,"indexed":1000,"failed":0,"wall_s":41.000,"ms_per_asset":41.000,"assets_per_s":24.390,"decode_ms_per_asset":12.500,"l1_ms_per_asset":1.000,"gate_ms_per_asset":0.010,"ocr_ms_per_ocr_asset":61.000,"ocr_ms_per_asset":15.250,"embed_ms_per_asset":11.200,"store_ms_per_asset":0.500,"ocr_attempted":250,"ocr_gated_out":750,"ocr_gate_ratio":0.250,"embed_attempted":1000,"start_footprint_mb":40.000,"peak_footprint_mb":98.000,"index_bytes_total":1600000,"index_bytes_per_asset":1600.000,"embedding_bytes_per_asset":1200.000}
trailing noise
"""


def selftest():
    fails = []

    rows, host = parse(SELFTEST_LOG)
    if len(rows) != 2:
        fails.append(f"parse: expected 2 rows, got {len(rows)}")
    if host is None or "cores=4" not in host:
        fails.append("parse: host line not captured")
    if rows and rows[0]["n"] > rows[-1]["n"]:
        fails.append("parse: rows are not sorted ascending by n")

    ok, note = linearity(rows)
    if ok is not True:
        fails.append(f"linearity: flat input judged {ok} ({note})")

    superlinear = [dict(rows[0]), dict(rows[1])]
    superlinear[1]["ms_per_asset"] = 400.0
    ok2, _ = linearity(superlinear)
    if ok2 is not False:
        fails.append("linearity: a 10x cost climb was not caught")

    ok3, _ = linearity(rows[:1])
    if ok3 is not None:
        fails.append("linearity: a single size should be UNKNOWN, not a verdict")

    # A ceiling must fall out of arithmetic, not vibes: 41 ms/asset, 5400 s budget.
    buf = io.StringIO()
    report(rows, host, buf)
    text = buf.getvalue()
    expected_fg = f"{int(BUDGET['cold_foreground_100k_s'] * 1000 / 41.0):,}"
    if expected_fg not in text:
        fails.append(f"ceiling: expected {expected_fg} assets in the foreground budget, not found")
    if "NOT a device result" not in text:
        fails.append("report: the non-device stamp is missing — PF-01 guard gone")
    if "PREDICTION" not in text:
        fails.append("report: the device band is not stamped PREDICTION")

    # NO DATA must never read as a pass.
    empty = io.StringIO()
    rc = report([], None, empty)
    if rc == 0 or "NO DATA" not in empty.getvalue():
        fails.append("empty input did not produce a hard NO DATA")

    for f in fails:
        print("FAIL:", f)
    print(f"\nselftest: {len(fails)} failure(s)")
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--log", help="file containing PVM_SCALE_RESULT lines (e.g. an xcodebuild log)")
    ap.add_argument("--out", help="write the markdown report here as well as to stdout")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    if not args.log:
        ap.error("--log is required (or use --selftest)")

    with open(args.log, "r", encoding="utf-8", errors="replace") as fh:
        rows, host = parse(fh.read())

    buf = io.StringIO()
    rc = report(rows, host, buf)
    text = buf.getvalue()
    sys.stdout.write(text)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
    return rc


if __name__ == "__main__":
    sys.exit(main())
