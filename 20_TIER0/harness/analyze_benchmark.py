#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T0-A analyzer — turns DEVICE_BENCHMARK_TIER0.csv into an A1–A4 verdict.

The verdict is COMPUTED from the budgets pre-registered in
`T0A_DEVICE_BENCHMARK_HARNESS_SPEC.md` §8, before any device existed. It is not
interpreted afterwards. That is the whole point: thresholds set in advance cannot
drift to meet the data (AB-7), and "the numbers looked alright" is not a PASS.

PF-01 is enforced in code, not by good intentions:
  · Rows are MEASURED data only.
  · Where 100k was not reached on a device, the analyzer will extrapolate — and the
    result is stamped PROJECTION and can NEVER produce a PASS. It can only produce
    a warning or a FAIL.

Also checks the CSV header against the Swift `MetricsCSV.header`, so a schema change
on one side of the language boundary cannot silently misalign the analysis.

    python analyze_benchmark.py --csv DEVICE_BENCHMARK_TIER0.csv
    python analyze_benchmark.py --selftest      # exercise the logic with no device
"""

import argparse, csv, io, os, re, sys, statistics
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SWIFT_CSV = os.path.join(HERE, "PVMBench", "MetricsCSV.swift")

# ---------------------------------------------------------------------------
# PRE-REGISTERED BUDGETS — spec §8. Do not edit to fit results.
# ---------------------------------------------------------------------------
BUDGET = {
    "cold_foreground_100k_s":   90 * 60,   # ≤ 90 min on the lowest tier
    "cold_background_100k_s":    8 * 3600, # ≤ 8 h, resumable, overnight on charge
    "incremental_100_assets_s":  60,       # continuous hygiene must feel immediate
    "first_screen_stall_ms":     3000,     # CD-2
    "thermal_critical_s":        0,        # zero tolerance
    "thermal_serious_frac":      0.05,     # < 5% of run duration
    "battery_pct_per_10k":       8,
    "index_bytes_per_asset":     2048,     # ≤ 2 KB → ≤ 200 MB at 100k
    "resume_reprocess_max":      200,      # one checkpoint batch (C-3)
}

# Neural Engine generation drives the gradient, not the marketing name.
CHIP_ORDER = ["A10", "A11", "A12", "A13", "A14", "A15", "A16", "A17", "A18", "A19"]

MODEL_CHIP = {
    "iPhone9":  "A10",  # iPhone 7 — no ANE, excluded (DEC-008)
    "iPhone10": "A11", "iPhone11": "A12", "iPhone12": "A13", "iPhone13": "A14",
    "iPhone14": "A15", "iPhone15": "A16", "iPhone16": "A17", "iPhone17": "A18",
    "iPhone18": "A19",
}


def chip_for(model, declared):
    if declared and declared.strip():
        return declared.strip().upper()
    m = re.match(r"(iPhone\d+)", model or "")
    return MODEL_CHIP.get(m.group(1), "?") if m else "?"


def chip_rank(chip):
    return CHIP_ORDER.index(chip) if chip in CHIP_ORDER else -1


def num(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def truthy(v):
    return str(v).strip().lower() in ("true", "1", "yes")


# ---------------------------------------------------------------------------

class Verdict:
    def __init__(self, code, detail, projected=False):
        self.code = code          # PASS | FAIL | NO DATA | PROJECTION
        self.detail = detail
        self.projected = projected

    def __str__(self):
        mark = {"PASS": "PASS", "FAIL": "FAIL",
                "NO DATA": "NO DATA", "PROJECTION": "PROJ"}[self.code]
        return f"{mark:<8} {self.detail}"


def scale_to_100k(rows):
    """Fit assets/sec from measured runs and project a 100k wall time.
    Returns (seconds, basis) or (None, reason)."""
    pts = [(int(num(r["assets_indexed"])), num(r["wall_time_s"]))
           for r in rows if num(r["wall_time_s"]) > 0 and num(r["assets_indexed"]) > 0]
    if not pts:
        return None, "no usable rows"
    rates = [n / t for n, t in pts]
    rate = statistics.median(rates)
    if rate <= 0:
        return None, "non-positive rate"
    biggest = max(n for n, _ in pts)
    return 100_000 / rate, f"median {rate:.1f} assets/s, largest measured run {biggest:,}"


def analyse_device(model, rows):
    chip = chip_for(model, rows[0].get("chip"))
    cold = [r for r in rows if r["run_type"] in ("cold", "resume")]
    fg = [r for r in cold if not truthy(r.get("required_full_rescan"))]
    inc = [r for r in rows if r["run_type"] == "incremental"]
    bg = [r for r in rows if r["run_type"] == "background"]

    out = {"model": model, "chip": chip, "rank": chip_rank(chip), "rows": len(rows)}

    # ---- A1 throughput -----------------------------------------------------
    measured_100k = [r for r in cold if int(num(r["assets_indexed"])) >= 95_000]
    if measured_100k:
        worst = max(num(r["wall_time_s"]) for r in measured_100k)
        ok = worst <= BUDGET["cold_foreground_100k_s"]
        out["A1"] = Verdict("PASS" if ok else "FAIL",
                            f"100k measured in {worst/60:.0f} min "
                            f"(budget {BUDGET['cold_foreground_100k_s']/60:.0f} min)")
    elif cold:
        proj, basis = scale_to_100k(cold)
        if proj is None:
            out["A1"] = Verdict("NO DATA", basis)
        else:
            over = proj > BUDGET["cold_foreground_100k_s"]
            # A projection may FAIL (if even the optimistic case blows the budget)
            # but it may never PASS. PF-01.
            out["A1"] = Verdict(
                "FAIL" if over else "PROJECTION",
                f"100k NOT measured; projected {proj/60:.0f} min ({basis})"
                + (" — exceeds budget" if over else " — within budget but UNMEASURED"),
                projected=True)
    else:
        out["A1"] = Verdict("NO DATA", "no cold/resume runs")

    # ---- A2 thermal --------------------------------------------------------
    if cold:
        crit = sum(num(r["thermal_critical_s"]) for r in cold)
        ser = sum(num(r["thermal_serious_s"]) for r in cold)
        dur = sum(num(r["wall_time_s"]) for r in cold) or 1
        frac = ser / dur
        ok = crit <= BUDGET["thermal_critical_s"] and frac < BUDGET["thermal_serious_frac"]
        out["A2"] = Verdict("PASS" if ok else "FAIL",
                            f"critical {crit:.0f}s (budget 0), serious {frac*100:.1f}% "
                            f"of run (budget <{BUDGET['thermal_serious_frac']*100:.0f}%)")
    else:
        out["A2"] = Verdict("NO DATA", "no cold runs")

    # ---- A3 survivability — the FATAL one ---------------------------------
    resumes = [r for r in rows if r["run_type"] == "resume" or truthy(r.get("resumed_ok"))]
    if resumes:
        worst_re = max(int(num(r["assets_reprocessed_after_resume"])) for r in resumes)
        recovered = any(truthy(r.get("index_state_recovered_after_kill")) for r in resumes)
        ok = worst_re <= BUDGET["resume_reprocess_max"]
        detail = (f"resumed, worst reprocess {worst_re} assets "
                  f"(budget ≤{BUDGET['resume_reprocess_max']} = one checkpoint batch)")
        if not recovered:
            detail += "; NOTE index_state_recovered_after_kill never true — "
            detail += "CD-5 (recovery across process death) not demonstrated"
        out["A3"] = Verdict("PASS" if ok else "FAIL", detail)
    else:
        out["A3"] = Verdict("NO DATA", "no resume runs — A3 is the fatal claim, do not skip it")

    # ---- A4 incrementality -------------------------------------------------
    if inc:
        forced = [r for r in inc if truthy(r.get("required_full_rescan"))]
        saw_updates = any(int(num(r.get("delta_updated", 0))) > 0 for r in inc)
        per100 = []
        for r in inc:
            n = int(num(r["assets_indexed"]))
            if n > 0:
                per100.append(num(r["wall_time_s"]) / n * 100)
        speed_ok = (not per100) or max(per100) <= BUDGET["incremental_100_assets_s"]
        if forced:
            out["A4"] = Verdict("FAIL",
                                f"{len(forced)}/{len(inc)} incremental runs required a FULL RESCAN "
                                f"(change token expired) — the index cannot be maintained without "
                                f"periodically re-reading the library")
        elif not speed_ok:
            out["A4"] = Verdict("FAIL",
                                f"delta too slow: {max(per100):.0f}s per 100 assets "
                                f"(budget {BUDGET['incremental_100_assets_s']}s)")
        elif not saw_updates:
            out["A4"] = Verdict("NO DATA",
                                "no run ever observed an UPDATED asset — the edit-an-old-asset "
                                "sub-test was not performed, so the case that broke the old "
                                "implementation is still unexercised")
        else:
            src = {r.get("delta_source", "?") for r in inc}
            out["A4"] = Verdict("PASS",
                                f"delta-only, updates observed, sources {sorted(src)}")
    else:
        out["A4"] = Verdict("NO DATA", "no incremental runs")

    # ---- supporting budgets ------------------------------------------------
    extras = []
    ipa = [num(r["index_bytes_per_asset"]) for r in cold if num(r["index_bytes_per_asset"]) > 0]
    if ipa:
        worst = max(ipa)
        extras.append(("index size", worst <= BUDGET["index_bytes_per_asset"],
                       f"{worst:.0f} B/asset (budget {BUDGET['index_bytes_per_asset']})"))
    batt = [num(r["battery_drain_pct_per_10k"]) for r in cold
            if num(r["battery_drain_pct_per_10k"]) > 0]
    if batt:
        worst = max(batt)
        extras.append(("battery", worst <= BUDGET["battery_pct_per_10k"],
                       f"{worst:.1f}% per 10k (budget {BUDGET['battery_pct_per_10k']}%)"))
    stall = [num(r["first_screen_stall_ms"]) for r in rows if num(r["first_screen_stall_ms"]) > 0]
    if stall:
        worst = max(stall)
        extras.append(("CD-2 first-screen stall", worst <= BUDGET["first_screen_stall_ms"],
                       f"{worst:.0f} ms (budget {BUDGET['first_screen_stall_ms']} ms)"))
    out["extras"] = extras

    core = [out["A1"], out["A2"], out["A3"], out["A4"]]
    out["supported"] = all(v.code == "PASS" for v in core)
    out["blocked_by"] = [k for k in ("A1", "A2", "A3", "A4") if out[k].code != "PASS"]
    return out


def check_schema(rows_header):
    """The CSV is written by Swift and read by Python. A change on either side would
    silently misalign every column, so compare them explicitly."""
    if not os.path.exists(SWIFT_CSV):
        return None
    src = open(SWIFT_CSV, encoding="utf-8").read()
    m = re.search(r"static let header = \[(.*?)\]\.joined", src, re.S)
    if not m:
        return None
    swift_cols = re.findall(r'"([a-z0-9_]+)"', m.group(1))
    if swift_cols == list(rows_header):
        return f"schema OK — {len(swift_cols)} columns, matches MetricsCSV.swift"
    only_swift = [c for c in swift_cols if c not in rows_header]
    only_csv = [c for c in rows_header if c not in swift_cols]
    return ("SCHEMA MISMATCH between MetricsCSV.swift and the CSV\n"
            f"    only in Swift: {only_swift}\n    only in CSV:   {only_csv}")


def report(devices, schema_note, out_path=None):
    L = []
    w = L.append
    w("# DEVICE_BENCHMARK_TIER0 — A1–A4 analysis")
    w(f"Generated {datetime.now().isoformat(timespec='seconds')} by `analyze_benchmark.py`")
    w("")
    w("Verdicts are computed from the budgets pre-registered in "
      "`T0A_DEVICE_BENCHMARK_HARNESS_SPEC.md` §8, before any device existed. "
      "They are not interpreted after the fact (AB-7).")
    w("")
    if schema_note:
        w(f"> {schema_note}")
        w("")

    w("## Per-device")
    w("")
    w("| Device | Chip | A1 throughput | A2 thermal | A3 survivability | A4 incremental | Supported |")
    w("|---|---|---|---|---|---|---|")
    for d in devices:
        w(f"| {d['model']} | {d['chip']} | {d['A1'].code} | {d['A2'].code} | "
          f"{d['A3'].code} | {d['A4'].code} | {'YES' if d['supported'] else 'no'} |")
    w("")

    for d in devices:
        w(f"### {d['model']}  ·  {d['chip']}  ·  {d['rows']} rows")
        for k in ("A1", "A2", "A3", "A4"):
            w(f"- **{k}** — {d[k]}")
        for name, ok, detail in d["extras"]:
            w(f"- {name}: {'ok' if ok else 'OVER BUDGET'} — {detail}")
        w("")

    # ---- minimum supported model, by the rule fixed in advance -------------
    w("## Minimum supported model")
    w("")
    w("> Rule, fixed before any measurement: a device is supported if it meets the A1 "
      "time budget, the A2 thermal budget and A4 at its realistic library size. The "
      "minimum supported model is the **oldest device that passes**. Choosing a "
      "minimum model first and then testing it was explicitly rejected.")
    w("")
    ranked = sorted([d for d in devices if d["rank"] >= 0], key=lambda d: d["rank"])
    passing = [d for d in ranked if d["supported"]]
    if not ranked:
        w("**NO DATA** — no device rows with a recognisable chip.")
    elif not passing:
        w("**NO DEVICE PASSES.** Blocked by: "
          + ", ".join(sorted({b for d in ranked for b in d['blocked_by']})))
        w("")
        w("Per Tier 0 §2, an A1-only failure is survivable and degrades the product to "
          "a reduced scope (recent N months). **An A3 failure is fatal** — an index that "
          "cannot survive interruption cannot exist on a phone.")
    else:
        lo = passing[0]
        w(f"**{lo['model']} ({lo['chip']})** — the oldest device meeting every budget.")
        failed_below = [d for d in ranked if d["rank"] < lo["rank"]]
        if failed_below:
            w("")
            w("Older devices tested and not supported:")
            for d in failed_below:
                w(f"- {d['model']} ({d['chip']}) — failed {', '.join(d['blocked_by'])}")
        else:
            w("")
            w("⚠️ No older device was tested, so this is the oldest device **available**, "
              "not a measured floor. The true minimum could be lower.")

    # ---- honesty checks ---------------------------------------------------
    w("")
    w("## Evidence quality")
    projected = [d for d in devices if any(getattr(d[k], "projected", False)
                                           for k in ("A1", "A2", "A3", "A4"))]
    if projected:
        w("")
        w("⚠️ **Projected, not measured.** These devices never ran a 100k library; "
          "their A1 figure is extrapolated from smaller runs and is stamped PROJECTION. "
          "A projection can FAIL a budget but can never PASS one (PF-01):")
        for d in projected:
            w(f"- {d['model']}: {d['A1'].detail}")
    nodata = [(d["model"], k) for d in devices for k in ("A1", "A2", "A3", "A4")
              if d[k].code == "NO DATA"]
    if nodata:
        w("")
        w("**Missing data** — these claims are untested, not passed:")
        for model, k in nodata:
            w(f"- {model} · {k}")
    if not projected and not nodata:
        w("")
        w("All four claims measured on every device listed. No projections, no gaps.")

    text = "\n".join(L)
    if out_path:
        open(out_path, "w", encoding="utf-8").write(text)
    return text


def load(path):
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        return list(r), r.fieldnames


SELFTEST_ROWS = """device_model,chip,ram_gb,ios_version,library_size,storage_state,run_type,wall_time_s,assets_indexed,assets_failed,throughput_assets_per_s,peak_mem_mb,mem_footprint_at_kill,avg_cpu_pct,thermal_nominal_s,thermal_fair_s,thermal_serious_s,thermal_critical_s,battery_start_pct,battery_end_pct,battery_drain_pct_per_10k,index_bytes_total,index_bytes_per_asset,interrupted_count,resumed_ok,assets_reprocessed_after_resume,ocr_attempted,ocr_gated_out,embed_attempted,icloud_fetch_required_count,icloud_fetch_skipped_count,real_asset_count,synthetic_asset_count,first_screen_stall_ms,cold_launch_to_first_asset_ms,index_state_recovered_after_kill,bg_expiration_events,memory_warnings,ocr_ms_per_asset,embed_ms_per_asset,delta_source,delta_inserted,delta_updated,delta_deleted,delta_discovery_s,required_full_rescan,notes
"iPhone14,5",A15,6,18.5,100000,all-local,cold,4200,100000,12,23.8,410,0,72,3900,280,20,0,100,74,2.6,150000000,1500,1,false,0,25000,75000,100000,0,100000,4000,96000,1800,320,false,0,1,64,11,,0,0,0,0,false,
"iPhone14,5",A15,6,18.5,100000,all-local,resume,900,100000,0,111,395,0,68,880,20,0,0,74,71,0.3,150000000,1500,1,true,180,0,0,0,0,100000,4000,96000,0,310,true,0,0,0,0,0,0,0,false,
"iPhone14,5",A15,6,18.5,100000,all-local,incremental,14,120,0,8.6,180,0,30,14,0,0,0,71,71,0,150200000,1501,0,false,0,30,90,120,0,120,4000,96000,0,0,false,0,0,0,0,persistent-token,95,25,3,0.4,false,
"iPhone11,8",A12,3,16.7,30000,icloud-optimised,cold,3100,30000,240,9.7,290,0,88,1200,900,900,100,100,68,10.7,52000000,1733,2,false,0,9000,21000,30000,1200,28800,30000,0,4200,900,false,0,4,140,26,,0,0,0,0,false,
"iPhone11,8",A12,3,16.7,30000,icloud-optimised,incremental,40,100,0,2.5,210,0,44,40,0,0,0,68,68,0,52100000,1736,0,false,0,25,75,100,0,100,30000,0,0,0,false,0,0,0,0,token-expired-full-rescan,0,0,0,3.1,true,
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="DEVICE_BENCHMARK_TIER0.csv")
    ap.add_argument("--out", default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        print("SELFTEST — synthetic rows, no device involved.\n"
              "Device 1 (A15) should pass everything. Device 2 (A12) should FAIL A2 on "
              "thermal and FAIL A4 on an expired token.\n")
        f = io.StringIO(SELFTEST_ROWS)
        r = csv.DictReader(f)
        rows, header = list(r), r.fieldnames
        schema = None
    else:
        if not os.path.exists(args.csv):
            sys.exit(f"not found: {args.csv}\n"
                     "Export it from the device (Share sheet) and pass --csv.")
        rows, header = load(args.csv)
        schema = check_schema(header)
        if schema and schema.startswith("SCHEMA MISMATCH"):
            print(schema)
            sys.exit("aborting: refusing to analyse a CSV whose columns do not match the writer")

    if not rows:
        sys.exit("no rows")

    # Device identifiers from uname() ALWAYS contain a comma ("iPhone14,5"), so they
    # must be quoted in CSV. If they are not, every column silently shifts by one and
    # the analysis is garbage that still looks plausible.
    suspect = [r["device_model"] for r in rows
               if r.get("device_model") and "," not in r["device_model"]
               and r["device_model"].lower().startswith("iphone")]
    if suspect:
        sys.exit(f"aborting: device_model has no comma ({suspect[0]!r}). The CSV was "
                 "almost certainly written unquoted and every column is shifted.")

    by_model = {}
    for row in rows:
        by_model.setdefault(row["device_model"], []).append(row)

    devices = [analyse_device(m, rs) for m, rs in by_model.items()]
    devices.sort(key=lambda d: (d["rank"], d["model"]))

    text = report(devices, schema, args.out)
    print(text)
    if args.out:
        print(f"\nwritten to {args.out}")


if __name__ == "__main__":
    main()
