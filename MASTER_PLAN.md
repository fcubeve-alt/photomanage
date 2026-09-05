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
| **T0-A** device & thermal | ✅ compiles green **and runs green on the iOS Simulator** (17 tests); analyzer self-tested | **HG-1** — blocked on a payment instrument, not willingness (DEC-027) | `DEVICE_BENCHMARK_TIER0.csv` + `.md` |
| **T0-B** retrieval entry | ✅ protocol, clickable prototype, test library, facilitator script, scoring sheet, analyzer | **136 foreground images**, then **HG-4** — 15 participants. Kept by Owner ruling, DEC-027 | `RETRIEVAL_ENTRY_USABILITY_TIER0.md` |
| **T0-C1** competitor pricing | — | — | ✅ **COMPLETE** 2026-08-22 |
| ~~**T0-C2** real payment signal~~ | pages built and kept unpublished | — | **CANCELLED by the Owner, DEC-026.** HG-2 closed; no domain, no ad spend |
| ~~**T0-D** autonomous mgmt~~ | materials kept | — | **CANCELLED by the Owner, DEC-026.** The Constitution §7 automation-tolerance bet is now an accepted risk carried into M4, not a validated finding |

**Every measurement chain is closed and every analyzer is self-tested** — none will
meet real data for the first time. What is missing is the data, not the tooling.

**Acceptance:** `20_TIER0/TIER0_GO_NO_GO.md` completed from named artifacts.
`NO DATA` is never a soft PASS; a workstream not run leaves the gate INCOMPLETE.

**Gate — rewritten 2026-09-06 for DEC-026.** The four-workstream gate no longer
describes a programme that will run. C and D are cancelled by the Owner and B is
frozen pending **OPEN-2**, so the gate now rests on **A alone**:
- **A3 (survivability) failure is fatal** — an index that cannot survive being killed
  and resumed is not a product, regardless of the build decision.
- An **A1-only failure degrades scope** to "recent N months" rather than killing it.
- **A1 is currently pessimistic** — `FC-1` means the harness measures the naive
  baseline, not the intended architecture. Fix or explicitly accept before reading a
  verdict from it.
- **NO DATA is still never a soft PASS.** A cancelled workstream is recorded as
  cancelled with its reason; it is never quietly counted as passed.
- The Constitution §7 automation-tolerance bet is no longer validated in Tier 0. It is
  carried into M4 as a **named accepted risk** (DEC-026).

`20_TIER0/TIER0_GO_NO_GO.md` still contains the old four-workstream template. It is
deliberately **not** rewritten yet — OPEN-2 decides its shape, and guessing would
produce a confident document that has to be redone.

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
| Study tasks stay answerable | `build_sourcing_worksheet.py` verifies the 8 constraint counts against the manifest and aborts on any mismatch |
| CSV schema ↔ writer agree | `analyze_benchmark.py` aborts on header mismatch |
| Landing arms differ only as intended | `build_landing.py` aborts on drift |
| Analyzers still run (incl. non-UTF-8 console) | `.github/workflows/tools-check.yml` on every `.py` change — PF-10 |
| Generators still deterministic; manifest reproduces from its seed | same workflow, verified by negative control |
