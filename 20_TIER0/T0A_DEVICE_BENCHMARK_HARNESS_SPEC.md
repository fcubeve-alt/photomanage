# T0-A · DEVICE BENCHMARK HARNESS SPEC
**Windows-side preparation for Tier 0-A.** Status of Tier 0-A itself: `REQUIRES_MAC` `REQUIRES_DEVICE` — **NOT TESTED.**
Purpose: make the on-device run a single working session once hardware exists, and state in advance what counts as PASS so the result cannot be argued after the fact.
Created 2026-08-22 · Session 001

> **This document contains zero measured device data.** Every number below is either a **TARGET** (a criterion set in advance) or a **PREDICTION** (a modelled estimate with stated assumptions). Neither may ever be written into `DEVICE_BENCHMARK_TIER0.csv`, which accepts measured values only. See `FAILURE_PATTERNS.md` PF-01.

---

## 1. What Tier 0-A must answer

Verbatim from Tier 0 v1.1 §2 — the PASS bar:

> 100k 图库首次索引可在合理时间内完成（不发烫降频、不被系统杀后台到无法恢复），且可增量更新，不需要每次全量重扫。

Decomposed into four independently falsifiable claims:

| Claim | Falsified if |
|---|---|
| **A1 Throughput** | A 100k first index cannot finish in the agreed time budget on the lowest device tier |
| **A2 Thermal** | Sustained indexing drives `ProcessInfo.thermalState` to `.serious`/`.critical` and stays there |
| **A3 Survivability** | The system kills the task and the index cannot resume — progress is lost |
| **A4 Incrementality** | New/changed assets require a full rescan rather than a delta update |

**A1 failing alone is survivable** (fall back to "recent N months" scope, per Tier 0 §2 FAIL clause). **A3 failing is fatal** — an index that cannot survive interruption cannot exist on a phone.

## 2. Scope lock

Layer 1 + Layer 2 **only** (Constitution §25). Explicitly **not** in this harness: taxonomy, entity resolution, risk scoring, policy, UI.

| Layer | Included |
|---|---|
| L1 cheap signals | PHAsset metadata, creation/modification time, GPS, media subtype, source (screenshot / camera / downloaded), pixel dimensions, file size, perceptual + exact hash |
| L1 OCR | Basic text recognition — **gated**, see §5 |
| L2 visual | One lightweight image embedding per asset |

## 3. Test grid  *(revised 2026-08-22 after Owner confirmed a ~6-device fleet)*

Superseded design: "3 device tiers". Actual design: **a performance gradient across every TestFlight-capable device the Owner owns**, with the minimum supported model derived from the measured curve rather than assumed. Full rationale, fleet handling, corpus strategy and run order: `T0A_MAC_ENVIRONMENT_AND_DEVICE_PLAN.md` Part 5.

| Axis | Values |
|---|---|
| Device | Every fleet device running iOS 16+ (iPhone 7 excluded — no TestFlight, no Neural Engine; see plan Part 2). Record exact model, chip, iOS version, RAM, free storage |
| Library | Real library as-is, then padded to 30k / 100k with synthetic assets where storage allows |
| Storage state | **all-local** and **iCloud-optimised** — both; see §6, still the highest-risk variable |
| Thermal start | begin each run at `.nominal`, battery ≥ 80%, not charging |
| Run type | cold first index → deliberate interrupt → resume → incremental |

**Run order is cheapest-information-first, not oldest-first or newest-first:** the Owner's daily-driver device runs first (proves the harness, answers the fatal A3/A4), then the oldest TestFlight-capable device (where A1/A2 will break if anywhere), then the rest of the curve. A flagship-first run proves the least.

**Minimum supported model rule, fixed in advance:** a device is supported if it meets the A1 time budget, the A2 thermal budget and A4 at its realistic library size. The minimum supported model is the **oldest device that passes**. Failures are reported with the specific budget missed and the margin. Choosing a minimum model first and then testing it is explicitly rejected.

## 4. Metrics — the exact columns of `DEVICE_BENCHMARK_TIER0.csv`

```
device_model, chip, ram_gb, ios_version, library_size, storage_state, run_type,
wall_time_s, assets_indexed, assets_failed, throughput_assets_per_s,
peak_mem_mb, mem_footprint_at_kill, avg_cpu_pct,
thermal_nominal_s, thermal_fair_s, thermal_serious_s, thermal_critical_s,
battery_start_pct, battery_end_pct, battery_drain_pct_per_10k,
index_bytes_total, index_bytes_per_asset,
interrupted_count, resumed_ok, assets_reprocessed_after_resume,
ocr_attempted, ocr_gated_out, embed_attempted,
icloud_fetch_required_count, icloud_fetch_skipped_count,
notes
```

Instrumentation notes:
- `thermal_*_s` — sample `ProcessInfo.processInfo.thermalState` every 5s and integrate. A single spot reading is worthless; the question is *dwell time*.
- `peak_mem_mb` — use `os_proc_available_memory()` / footprint, not Xcode's gauge alone. Jetsam kills are footprint-driven.
- `assets_reprocessed_after_resume` — this is the checkpoint-quality metric. Anything above one batch means checkpointing is too coarse (Playbook E-07).

## 5. Design constraints to build in before measuring

These are engineering decisions the harness must embody, so the benchmark measures the intended design rather than a naive baseline.

**C-1 · OCR must be gated, not universal.**
Running text recognition across all 100k assets is the single most likely cause of an A1 failure. Gate it on cheap L1 signals first — screenshot subtype, aspect ratio, source, low colour variance, high edge density. Record `ocr_attempted` vs `ocr_gated_out` so the ablation is available later.
*PREDICTION (unverified): OCR dominates per-asset cost by roughly an order of magnitude over embedding. If true, the gate ratio — not raw OCR speed — determines whether A1 passes.* This prediction is itself a benchmark output: report measured OCR cost per asset separately.

**C-2 · Index from thumbnails, never originals.**
Request a fixed small target size through `PHImageManager` with `isNetworkAccessAllowed = false` for the indexing pass. Originals are unnecessary for L1/L2 and catastrophic for iCloud-optimised libraries (§6).

**C-3 · Checkpoint per small batch.**
Persist after every N assets (suggest N = 200, tune from measurement). On resume, reprocessing must be bounded by N. Playbook E-07.

**C-4 · Two execution contexts, measured separately.**
Foreground (user watching, TTFUV matters) and `BGProcessingTask` (bulk overnight). They have different limits and must not be conflated in one number.
> **FACT (Apple platform behaviour, confidence MEDIUM — must be confirmed on device):** `BGProcessingTask` is intended for long, non-time-sensitive, CPU/IO-heavy work, is scheduled by the system when the device is idle and preferentially while charging, must set an `expirationHandler`, and must call `setTaskCompleted(success:)`. Overrunning without handling expiration risks termination *and throttled future scheduling*.
> **INTERPRETATION:** background scheduling is a privilege the system withdraws from apps that misbehave. A1 and A3 are therefore coupled — sloppy expiration handling degrades throughput permanently, not just once. The harness must log every expiration event.

**C-5 · Change observation, not rescanning.**
Use `PHPhotoLibraryChangeObserver` + persisted local identifiers for the incremental run. A4 is falsified the moment a full enumeration is required to find deltas.

## 6. The iCloud variable — highest risk, test first

**FACT (documented API behaviour, confidence HIGH; on-device confirmation still required):** with "Optimise iPhone Storage" enabled, full-resolution originals may not be present locally; requesting them triggers a network download, and `PHImageRequestOptions.isNetworkAccessAllowed` controls whether that is permitted.

**INTERPRETATION:** if the harness ever requests originals on an iCloud-optimised 100k library, the benchmark measures the user's Wi-Fi, not the phone. This would produce a spuriously catastrophic A1 result and could falsely NO-GO the project. Conversely, if usable local thumbnails are *not* available for a large fraction of assets, that is a genuine and severe product constraint that must surface in Tier 0, not Tier 2.

**Required output:** `icloud_fetch_required_count` vs `icloud_fetch_skipped_count`, plus the quality of what came back when network access was denied. This single measurement may matter more to the product than raw throughput.

## 7. PhotoKit behaviours to verify in the same session

Tier 0 §2 requires these; they are cheap to check once the harness exists and expensive to discover later.

| # | To verify | Why it can change the product |
|---|---|---|
| V-1 | Full vs **limited** photo authorisation — what is enumerable, and what the re-prompt flow looks like | A user on limited access may make the whole Visual Library premise unworkable; the product needs a stance |
| V-2 | Deletion boundary — `performChanges` deletion always requires user confirmation; behaviour on batch deletes | Directly constrains the automation philosophy (Constitution §5–§7). If every delete needs a tap, "autonomous management" needs redefining |
| V-3 | `PHPhotoLibraryChangeObserver` fidelity and delivery while backgrounded | Underpins Continuous Hygiene (§13) |
| V-4 | iCloud-only asset original vs thumbnail request behaviour | §6 |
| V-5 | Whether app-deleted assets land in "Recently Deleted" and remain recoverable for 30 days | **Safety red line.** The Constitution's entire risk philosophy depends on deletions being recoverable. If they are not, R0–R2 automation must be rethought |

**V-5 is the most important item in this section.** The Constitution's automation argument (§7: tolerate low-cost recoverable errors) is only valid if errors *are* recoverable. Verify it, do not assume it.

## 8. Time budget — TARGETS set in advance

Set now, before data exists, so the result cannot be rationalised afterwards.

| Scenario | TARGET | Rationale |
|---|---|---|
| 100k cold index, background, charging overnight | **≤ 8 h**, resumable | Must complete in one idle night |
| 100k cold index, foreground, lowest tier | **≤ 90 min** | Upper bound of a motivated user leaving the app open |
| First useful view (TTFUV) | **≤ 30 s** | Constitution §24 Gate 3 / Tier 2-C. Measured here only as a sanity floor |
| Incremental, 100 new assets | **≤ 60 s** | Continuous Hygiene must feel immediate |
| Thermal | **0 s** in `.critical`; `.serious` dwell **< 5%** of run | Sustained `.serious` means throttling and user-visible heat |
| Battery | **≤ 8%** per 10k assets | 100k overnight must not flatten the device |
| Index size | **≤ 2 KB/asset** → ≤ 200 MB at 100k | Above this the index competes with the storage the product claims to free |

**PREDICTION for planning only (assumptions: A16-class ANE, gated OCR at ~25% of assets, thumbnail-only decode, 4 concurrent workers):** per-asset cost is dominated by thumbnail decode and gated OCR rather than by embedding, putting a 100k foreground index in the tens-of-minutes range on a flagship and plausibly 2–3× that on entry tier. **Confidence LOW.** This exists to size the experiment, not to predict its verdict. It is not evidence and must not be cited as such.

## 9. Deliverables when hardware is available
1. `DEVICE_BENCHMARK_TIER0.csv` — measured rows only, schema per §4
2. `DEVICE_BENCHMARK_TIER0.md` — analysis, A1–A4 verdicts, PhotoKit V-1…V-5 findings
3. Harness source, committed
4. Raw thermal/memory traces, archived

## 10. Environment status

**HG-3 approved in principle by Owner on 2026-08-22**: cloud Mac only, no Mac purchase, existing iPhone fleet, explicit approval required before any actual payment.

Environment plan, verified costs, delivery path and step-by-step execution now live in **`T0A_MAC_ENVIRONMENT_AND_DEVICE_PLAN.md`**. Summary: Scaleway Mac mini M1 at €0.11/hr (one 24h block ≈ €2.64) builds and signs; delivery to the fleet is via TestFlight, which requires the $99/yr Apple Developer Program. Nothing purchased yet — awaiting Owner approval of €2.64 + $99.

Note the constraint that drove that design: **a cloud Mac cannot have an iPhone plugged into it**, so the plan must solve delivery to device, not just build.
