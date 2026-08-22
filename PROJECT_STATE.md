# PROJECT STATE
**Read this file first, every session.** Canonical runtime state (Playbook E-03).
Last updated: 2026-08-22 · Session 001 (2 deliverables complete)

## Coordinates
- Project: Personal Visual Memory Engine (智能照片管理系统)
- Repo: `D:\photomanage` · branch `main` · remote: **none yet** (local-only — see MAINTENANCE queue)
- Stage: **M1 / Tier 0 — 生死开关**
- Environment: Windows 10, Python 3.12.10, git 2.9. No Mac, no Xcode. Owner has an iPhone.

## Authority (never re-derive this)
L1 Product Constitution **v1.3** → L2 P0 Execution Index v1.0 + Tier 0/1/2 **v1.1** → L3 Engineering Playbook **v1.1** → L4 Skills/Tools.
Full map: `DOCUMENTATION_MAP.md`. Decisions: `DECISIONS.md`. Rules: `OPERATING_RULES.md`.

## Done
- **M0 Bootstrap complete.** 11 source documents audited, authority levels assigned, 4 superseded/duplicate files archived, 5 conflicts resolved (C-1…C-5), Money OS package sealed out of scope.
- Persistent state established: MISSION_SPEC, MASTER_PLAN, PROJECT_STATE, OPERATING_RULES, DECISIONS, FAILURE_PATTERNS, SESSION_HANDOFF, DOCUMENTATION_MAP, VALIDATION_MATRIX. No pre-existing equivalents were duplicated — the folder contained zero markdown files.
- Validation matrix built for all three tiers with measurable pass criteria.
- Plain-text mirror of every source .docx committed for grep-able reuse.

## Doing now
**T0-B-PREP · Retrieval Entry study protocol** (`WINDOWS_OK`).
Target: `20_TIER0/T0B_RETRIEVAL_ENTRY_STUDY_PROTOCOL.md`.

## Work queue

### ACTIVE
1. ~~**T0-C1** Competitor pricing matrix~~ — ✅ **DONE** → `20_TIER0/evidence/COMPETITOR_PRICING_MATRIX.md`
2. ~~**T0-A-PREP** Device benchmark harness spec~~ — ✅ **DONE** → `20_TIER0/T0A_DEVICE_BENCHMARK_HARNESS_SPEC.md`
3. **T0-B-PREP** Retrieval-entry study protocol: task set, standard test-library definition, script, scoring sheet, anti-bias rules. — **NEXT**
4. **T0-C2-PREP** Landing-page value-ladder copy + measurement plan, derived from C1. Owner launches it.

### RESEARCH
- Apple-native on-device capability survey (Vision, Core ML, Live Text/OCR, PhotoKit limits) — FACT/INTERPRETATION separated, feeds the T0-A compute budget and the P-04 route decision. **No model dependency may be added without benchmark evidence.**

### EXPERIMENT
- (empty — Tier 0 experiments are all device- or user-blocked)

### HUMAN_GATE
| Gate | Blocker | Wake condition | First action on wake |
|---|---|---|---|
| **HG-3** (blocking T0-A) | No Mac / Xcode / instrumented iPhones | Owner provides a Mac, a cloud-Mac subscription, or an alternative device-test route | Build the Layer-1+2 indexing harness per T0-A-PREP and run 10k/30k/100k on 3 device tiers |
| **HG-4** (blocking T0-B) | No recruited external test users; prototype needs iOS | Users recruited **and** a runnable prototype exists (depends on HG-3) | Run the study per T0-B-PREP |
| **HG-2** (blocking T0-C2) | Needs domain, payment path and real spend | Owner approves the landing page and funds it | Launch page, collect reach-checkout / deposit data |

### CAPABILITY
- Web search/fetch: available. If it drops, fall back to the search-free queue (T0-A-PREP, T0-B-PREP) — do not idle (S-03, F-05).

### MAINTENANCE
- Create a git remote so E-06 (local absence ≠ remote absence) is actually enforceable. Currently local-only, which is a real single-point-of-failure for cross-machine recovery.

## Blockers
Tier 0 **cannot be closed** on Windows alone. T0-A, T0-B and T0-C2 all need Owner-side resources (HG-2/3/4). This blocks the *gate*, not the *mission* — C1 and all three PREP items proceed.

## Risks
| Risk | Note |
|---|---|
| Tier 0 gate stalls indefinitely | If HG-2/3/4 stay unresolved, C1 + PREP work will be exhausted and the mission genuinely idles. That would be the S-04 condition for escalating HG-9. |
| PF-01 simulated device numbers | Guarded by P-02. Watch for it. |
| Cleaner-rung commoditisation | The likely C1 finding is that the Cleaner rung is already free. That is expected, and is why the Constitution anchors paid value at Continuous Management and above. |

## Next action for a recovering session
Write `20_TIER0/T0B_RETRIEVAL_ENTRY_STUDY_PROTOCOL.md` (task set, standard test library, script, scoring sheet, anti-bias rules). Then `T0C2_LANDING_PAGE_PLAN.md` derived from the pricing matrix.

## Key findings so far (do not re-derive)
- Cleaner rung is commoditised: 10 cleaners all free-to-install, top app 701k ratings, one competitor giving cleaning away free. Do **not** test a Cleaner-rung price.
- Category monetises via weekly subs $4-12/wk ($207-623/yr) with documented predatory patterns. Credible non-predatory price point is a **$29.99-49.99 lifetime/one-off**.
- Search rung is thin: Queryable $4.99 one-off, 88 US ratings despite HN #1.
- **Lucent Pro** (id 6749473261) occupies this project's exact positioning — on-device AI photo manager, NL search, 200+ smart collections — and has **0 ratings**. Recorded as **UNKNOWN-1**: demand verdict vs distribution verdict, unresolved. Do not cite either way.
- On-device semantic search ships in 206-262MB binaries → no 2GB+ model dependency is implied (supports P-04).
