# T0-A · SCALE SWEEP — first measured Tier 0-A data

**Status: MEASURED, on the iOS Simulator. NOT a device result.** No A1–A4 verdict is
recorded from this file and none may be written into `DEVICE_BENCHMARK_TIER0.csv`,
which accepts device measurements only (PF-01, P-02).

## Provenance

| | |
|---|---|
| Workflow | `.github/workflows/t0a-scale.yml`, runs **34022334180** and **34023173268** |
| Commits | `c01d9a6` and `210be7c` on `claude/classification-program-dev-yk88jj` (harness identical in both) |
| Runner | GitHub Actions `macos-15`, standard arm64, Xcode 16.4 |
| Simulator host | 3 cores, 7 GB, iOS 26.2 (23C54) |
| Corpus | synthetic, generated in-process; 200 / 1000 / 3000 assets, 25% text-bearing |
| Artifacts | `t0a-scale` ids 9986053936 and 9986414069, each holding `scale_results.txt` and the raw log |
| Cost | $0. HG-1 is still open; nothing here needed it |

## Headline

**105–154 ms per asset**, flat across a fifteen-fold range of corpus sizes within each
run. Two runs, not one, and the reason for the range is finding 0 below.

| | run 1 | run 2 |
|---|--:|--:|
| ms/asset at n=3000 | 104.7 | 154.1 |
| Simulator ceiling, 90-minute foreground budget | 51,567 | 35,049 |
| Simulator ceiling, 8-hour background budget | 275,026 | 186,932 |
| Device band, 90-min foreground — **PREDICTION, no device has run this** | 10,313 – 25,783 | 7,009 – 17,524 |

**Read the ceiling as roughly 35k–52k assets in the 90-minute foreground budget, and
roughly 7k–26k on the predicted device band.** The device band assumes a phone takes
2×–5× the Simulator's wall time — a modelling assumption stated so it can be attacked,
not a measurement, replaced by real numbers the day HG-1 clears.

So: a 100k library does not fit the 90-minute foreground budget on either run's
optimistic ceiling, and fits the 8-hour background budget on both with room to spare.
A library up to roughly 30k fits both budgets even on the slower run. The Owner's own
framing — that 100k is far above what most people hold, and 10k is already a large
library — is the right one to design against, and both runs are consistent with it.

## Findings

**0 · A single run is a sample, not a constant — and the harness is not the variable.**
The two runs above are the same harness over the same corpus at the same sizes, 1.47×
apart. Everything deterministic matched *exactly* across both — 4,219 index bytes per
asset, 3,072-byte embedding, +404 MB growth, 2,308 MB peak, 52% gate ratio, zero
failures — so the variance is CPU contention on a shared runner, not the measurement.
Two consequences: quote this ceiling as a band and never as a figure, and note that a
number which moves 47% between two runs of the same code on the same host is not a
number anyone should be making an irreversible architecture decision from. A device
measurement is what settles A1; this is what tells you roughly where to look.

**1 · C-1's central prediction is now in doubt.** *(Reproduced in both runs: embedding
84% and 85%, OCR 6% in both.)* The spec predicted OCR would dominate
per-asset cost by roughly an order of magnitude over embedding, which is why the OCR
gate exists and why the gate ratio was expected to decide A1. Measured at a 52% gate
ratio: **embedding is 84% of per-asset cost and OCR is 6%.** Per asset actually OCR'd,
OCR costs 0.1× an embedding.

This is stated as *in doubt*, not *refuted*, and the distinction matters:
`VNGenerateImageFeaturePrintRequest` is exactly the stage that runs on the Neural
Engine on a device and on the CPU in a Simulator, so the embedding cost above is
inflated by an unknown factor that Vision's text recognition does not pay in the same
proportion. Refuting C-1 needs a device. What follows either way is that the next
optimisation belongs on the embedding rather than on the OCR gate — the gate can at
best remove a stage that costs a fraction of the one nothing gates.

**2 · Index size is 2× over its budget, and all of the overage is one field.**
*(Identical in both runs, to the byte.)*
4,219 B/asset against a §8 budget of 2,048. The feature-print blob alone is 3,072 B;
everything else comes to 1,147 B, which is inside the budget on its own. At 100k that
is 0.42 GB. This is a design choice to make — store the embedding, quantise it, or
recompute it on demand — not a bug to fix. The budget was written before anyone knew
what a feature print weighed.

**3 · Cost is linear within a run.** 127.7 → 110.8 → 104.7 ms/asset from n=200 to
n=3000 in run 1; the trend is *downward* as fixed costs amortise. Nothing in the pipeline is superlinear, which is
what makes the extrapolation above legitimate. Zero failed assets across 4,200
indexings.

## What this run still cannot answer

- **A2 thermal** — the Simulator has no thermal state. Untested.
- **A3 survivability** — no jetsam, no `BGProcessingTask` expiry. Untested, **and A3 is
  the fatal one.**
- **A4 incrementality** — needs a real `PHPhotoLibraryChangeObserver`. Untested.
- **iCloud** — no optimised-storage library exists here, so §6 is untouched.
- **Video** — images only (MNI-2 / FC-2). A mixed library is worse than this.
- **FC-1** — the dHash is computed and never read, so every duplicate pays full price.
  The number above is the naive pipeline and is pessimistic by the duplicate rate.
- **The stage mix** — the least transferable row in the report, per finding 1.

## Full analyzer output

Reproduced verbatim from the run's job summary. Generated by
`20_TIER0/harness/analyze_scale.py`, whose budgets are imported from
`analyze_benchmark.py` so the two analyzers cannot drift.

```
| n    | wall    | ms/asset | assets/s | decode | L1  | OCR/ocr'd | OCR/asset | embed | store | gate | peak MB | idx B/asset |
|------|---------|----------|----------|--------|-----|-----------|-----------|-------|-------|------|---------|-------------|
| 200  | 26 s    | 127.7    | 7.8      | 10.2   | 0.5 | 37.8      | 20.4      | 96.4  | 0.16  | 54%  | 1769    | 5025        |
| 1000 | 1.8 min | 110.8    | 9.0      | 10.0   | 0.5 | 14.5      | 7.6       | 92.4  | 0.19  | 52%  | 1904    | 4314        |
| 3000 | 5.2 min | 104.7    | 9.6      |  9.9   | 0.5 | 12.1      | 6.3       | 87.8  | 0.18  | 52%  | 2309    | 4219        |

PVM_SCALE_RESULT {"n":3000,"indexed":3000,"failed":0,"wall_s":314.151,"ms_per_asset":104.717,
"assets_per_s":9.550,"decode_ms_per_asset":9.893,"l1_ms_per_asset":0.507,"gate_ms_per_asset":0.001,
"ocr_ms_per_ocr_asset":12.085,"ocr_ms_per_asset":6.340,"embed_ms_per_asset":87.782,
"store_ms_per_asset":0.183,"ocr_attempted":1574,"ocr_gated_out":1426,"ocr_gate_ratio":0.525,
"embed_attempted":3000,"start_footprint_mb":1904.292,"peak_footprint_mb":2308.714,
"index_bytes_total":12658000,"index_bytes_per_asset":4219.333,"embedding_bytes_per_asset":3072.000}
```

Memory: read the **+404 MB of growth**, not the 2,309 MB absolute. The absolute
includes the whole test host inside a Simulator and is not a phone number; growth that
tracks n would be a leak wherever it ran. Neither is an A3 result.

## Note on the first attempt

Run 34021927268 came back **green having measured nothing**. The sweep was gated on an
environment variable that never arrived, and the diagnostic that should have said so
was a `print` — and stdout from a process inside the Simulator does not reach
xcodebuild's log. The only reason this was not read as a result is that the collection
step was written to fail when no measurements existed. Both defects are fixed in
`c01d9a6`; the guard is why there is a real number here instead of a confident empty one.
