# MASTER PLAN
Milestones and acceptance gates. Not a daily task list (Playbook §5).
Current position: **M1 complete → M2 in progress.**

## M0 · Bootstrap — ✅ COMPLETE (2026-08-22)
Documentation audit, authority map, conflict resolution, persistent state, validation matrix, git repository.
**Acceptance:** a new session on a new machine can recover the project from `PROJECT_STATE.md` + git alone, without the Owner explaining anything. Verified by cold-start recovery test.

## M1 · Tier 0 — 生死开关 — 🔵 IN PROGRESS
Answer three kill questions with real evidence.

| Workstream | Executable now? | Deliverable |
|---|---|---|
| T0-A Device & thermal limit | ❌ `REQUIRES_MAC` `REQUIRES_DEVICE` → HG-3 | `DEVICE_BENCHMARK_TIER0.csv/.md` |
| T0-B Retrieval Entry study | ❌ `REQUIRES_MAC` `REQUIRES_USERS` → HG-4 | `RETRIEVAL_ENTRY_USABILITY_TIER0.md` |
| T0-C1 Competitor pricing matrix | ✅ **WINDOWS_OK — active** | `COMPETITOR_PRICING_MATRIX.md` |
| T0-C2 Real payment signal | ❌ `REQUIRES_OWNER` → HG-2 | `REAL_PAYMENT_SIGNAL_TIER0.md` |

Windows-side preparation that removes future blocked time (does not substitute for the real tests):
- Device benchmark harness spec + exact metric list + per-asset compute budget the phone must hit.
- Retrieval-entry study protocol: task set, standard test library, script, scoring sheet, anti-bias rules.
- Landing-page value-ladder copy and measurement plan, derived from C1 findings, ready for Owner launch.

**Acceptance:** `TIER0_GO_NO_GO.md` with A/B/C verdicts backed by real runs and real users.
**Gate:** A or B FAIL → NO-GO/PIVOT. C FAIL → Commercial Model Pivot, product survives. All PASS → M2.

## M2 · Tier 1 — 核心能力可行性 — 🔒 LOCKED
Taxonomy, Category-Specific Entity Resolver, Lifecycle Engine, multi-dimensional index skeleton, four retrieval paths (lite).
Mostly Windows-executable once unlocked — blocked by sequence, not hardware.
**Acceptance:** `TIER1_GO_NO_GO.md`. Document-class False Merge rate is the make-or-break number.

## M3 · Tier 2 — 完整体验与规模化 — 🔒 LOCKED
Risk Policy Engine, Equivalence Margin, first-run cataloguing + continuous ingestion, full Structure-First home, Multi-Signal Classification, unit economics, Personal Policy learning.
**Acceptance:** `FINAL_P0_GO_NO_GO_DECISION.md`.

## M4 · Product development — 🔒 LOCKED
Only after a GO or GO WITH CONSTRAINTS at M3. Nothing before this milestone is a product.

---

## Sequencing rules
1. One tier at a time. A gate file must exist before the next tier opens (Execution Index v1.0).
2. Validation code is written until it answers the kill question, then stops. Not until it feels complete.
3. A blocked workstream never blocks an unblocked one.
4. Every milestone persists evidence to `20_TIER0/evidence/` (and the equivalent per tier) before advancing.
