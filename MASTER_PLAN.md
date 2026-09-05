# MASTER PLAN
Milestones and acceptance gates. Not a daily task list (Playbook §5).
**Current position: M0 complete · M1 (Tier 0) IN PROGRESS · zero measurements taken.**
Recalibrated 2026-08-23 against DEC-008 … DEC-022.

## M0 · Bootstrap — ✅ COMPLETE (2026-08-22)
Documentation audit, authority map, conflict resolution, persistent state, validation
matrix, git repository, GitHub remote.
**Acceptance:** a new session on a new machine can recover from `PROJECT_STATE.md` +
git alone, without the Owner explaining anything.
**Verified** — not asserted: `recovery_check.py --strict`, 33 checks, 0 FAIL, and it
now runs in CI on every `.md` change (DEC-022). **Proven in the real event on
2026-09-06**: the project moved to a different computer and a cold session recovered
from the repo alone. What the recovery test could not see — that the analyzers
themselves were broken on the new machine — is DEC-025 / PF-10.

## M1 · Tier 0 — 生死开关 — 🔵 IN PROGRESS
Answer the kill questions with real evidence. **Four workstreams** — D was added by
Owner instruction (DEC-014) because Constitution §7 requires the automation-tolerance
bet be validated by real users, and the Tier 0 document contained no such test.

| Workstream | Instrumentation | Blocked on | Deliverable |
|---|---|---|---|
| **T0-A** device & thermal | ✅ harness compiles green on CI; analyzer self-tested | **HG-1** — $99 Apple Developer + signing secrets | `DEVICE_BENCHMARK_TIER0.csv` + `.md` |
| **T0-B** retrieval entry | ✅ protocol, clickable prototype, test library, facilitator script, scoring sheet, analyzer | **HG-4** — 15 external participants | `RETRIEVAL_ENTRY_USABILITY_TIER0.md` |
| **T0-C1** competitor pricing | — | — | ✅ **COMPLETE** 2026-08-22 |
| **T0-C2** real payment signal | ✅ three landing pages, instrumented, smoke-tested | **HG-2** — domain + ~$500–700 ad spend | `REAL_PAYMENT_SIGNAL_TIER0.md` |
| **T0-D** autonomous mgmt | ✅ protocol, 4 ledger variants, scoring sheet, analyzer | **HG-4** — same cohort as T0-B | `AUTONOMOUS_MGMT_VALUE_PROP_TIER0.md` |

**Every measurement chain is closed and every analyzer is self-tested** — none will
meet real data for the first time. What is missing is the data, not the tooling.

**Acceptance:** `20_TIER0/TIER0_GO_NO_GO.md` completed from named artifacts.
`NO DATA` is never a soft PASS; a workstream not run leaves the gate INCOMPLETE.

**Gate (Tier 0 v1.1 §6, DEC-002 / DEC-014):**
- A **or** B FAIL → **NO-GO / PIVOT**, stop.
- A+B PASS, C PASS → **GO → M2**.
- A+B PASS, C FAIL → **TECHNICAL/PRODUCT GO + COMMERCIAL MODEL PIVOT.** The product
  survives; heavy investment waits until the commercial model is fixed.
- D is reported alongside, never inside, the A/B/C arithmetic. **D FAIL → escalate to
  Owner as a potential Kill result** (PF-08) — it contradicts Constitution §5–§7/§17.
- Within A: **A3 (survivability) failure is fatal**; an A1-only failure degrades scope
  to "recent N months" rather than killing the product.

## M2 · Tier 1 — 核心能力可行性 — 🔒 LOCKED
Taxonomy, Category-Specific Entity Resolver, Lifecycle Engine, multi-dimensional index
skeleton, four retrieval paths (lite).
Largely Windows-executable once unlocked — blocked by **sequence, not hardware**.
**Acceptance:** `TIER1_GO_NO_GO.md`. The Document-class False Merge rate is the
make-or-break number.

## M3 · Tier 2 — 完整体验与规模化 — 🔒 LOCKED
Risk Policy Engine, Equivalence Margin, first-run cataloguing + continuous ingestion,
full Structure-First home, Multi-Signal Classification, unit economics, Personal Policy
learning.
**Acceptance:** `FINAL_P0_GO_NO_GO_DECISION.md`.

## M4 · Product development — 🔒 LOCKED
Only after GO or GO WITH CONSTRAINTS at M3. **Nothing built before this milestone is a
product** — everything to date is validation instrumentation.

---

## Sequencing rules
1. One tier at a time. A gate file must exist with a conclusion before the next tier
   opens (Execution Index v1.0).
2. Validation code is written until it answers the kill question, then stops — not
   until it feels complete.
3. A blocked workstream never blocks an unblocked one (S-03).
4. Evidence is persisted to `20_TIER0/evidence/` before a milestone advances.
5. Every analyzer is self-tested before it sees real data. Two real bugs have already
   been caught this way — a comma in device identifiers silently shifting every CSV
   column, and a sample size that could not reach its own threshold (DEC-021).

## Standing checks
| Check | Enforced by |
|---|---|
| Harness compiles | `.github/workflows/ios-build.yml` on every harness change |
| Recovery still viable | `.github/workflows/recovery-check.yml` on every `.md` change |
| Taxonomy ↔ test library agree | `generate_test_library.py` aborts on any path not in `taxonomy.py` |
| CSV schema ↔ writer agree | `analyze_benchmark.py` aborts on header mismatch |
| Landing arms differ only as intended | `build_landing.py` aborts on drift |
| Analyzers still run (incl. non-UTF-8 console) | `.github/workflows/tools-check.yml` on every `.py` change — PF-10 |
| Generators still deterministic; manifest reproduces from its seed | same workflow, verified by negative control |
