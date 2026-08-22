# PROJECT STATE
**Read this file first, every session.** Canonical runtime state (Playbook E-03).
Last updated: 2026-08-22 · Session 001 (3 deliverables complete; HG-3 approved in principle)

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

⚠️ **Awaiting Owner approval of spend: EUR 2.64 (Scaleway 24h M1 block) + 99 USD (Apple Developer Program).** Nothing purchased. See `20_TIER0/T0A_MAC_ENVIRONMENT_AND_DEVICE_PLAN.md`. Work continues on everything that does not depend on it.

## Work queue

### ACTIVE
1. ~~**T0-C1** Competitor pricing matrix~~ — ✅ **DONE** → `20_TIER0/evidence/COMPETITOR_PRICING_MATRIX.md`
2. ~~**T0-A-PREP** Device benchmark harness spec~~ — ✅ **DONE** → `20_TIER0/T0A_DEVICE_BENCHMARK_HARNESS_SPEC.md`
3. ~~**T0-A-MAC-PLAN** Cloud Mac environment + device gradient plan~~ — ✅ **DONE** → `20_TIER0/T0A_MAC_ENVIRONMENT_AND_DEVICE_PLAN.md` (pre-payment report, awaiting approval)
4. **T0-B-PREP** Retrieval-entry study protocol: task set, standard test-library definition, script, scoring sheet, anti-bias rules. — **NEXT**
5. **T0-A-HARNESS** Write the Swift benchmark harness source on Windows (cannot compile here, can be written here) so the cloud-Mac block is spent compiling, not authoring.
6. **T0-C2-PREP** Landing-page value-ladder copy + measurement plan, derived from C1. Owner launches it.

### RESEARCH
- Apple-native on-device capability survey (Vision, Core ML, Live Text/OCR, PhotoKit limits) — FACT/INTERPRETATION separated, feeds the T0-A compute budget and the P-04 route decision. **No model dependency may be added without benchmark evidence.**

### EXPERIMENT
- (empty — Tier 0 experiments are all device- or user-blocked)

### HUMAN_GATE
| Gate | Blocker | Wake condition | First action on wake |
|---|---|---|---|
| **HG-3** (T0-A) | ✅ **APPROVED IN PRINCIPLE 2026-08-22** — cloud Mac only, existing 6-iPhone fleet. Reduced to the spend gate below | — | — |
| **HG-2a** (blocking T0-A) | **Spend approval: EUR 2.64 Scaleway + 99 USD Apple Developer.** Nothing purchased | Owner approves both amounts | Provision Scaleway M1, build, upload to TestFlight |
| **HG-1** (blocking T0-A) | Apple Developer enrollment — legal name, own credit card, 2FA, possibly photo ID. **Owner must do this personally** | Owner completes enrollment | Create App Store Connect record + TestFlight internal testers |
| **HG-4** (blocking T0-B) | No recruited external test users. Tooling half is now solved by the same Mac environment — this is **purely a recruitment problem** | Users recruited **and** prototype built | Run the study per T0-B-PREP |
| **HG-2b** (blocking T0-C2) | Needs domain, payment path and real spend | Owner approves the landing page and funds it | Launch page, collect reach-checkout / deposit data |

### CAPABILITY
- Web search/fetch: available. If it drops, fall back to the search-free queue (T0-A-PREP, T0-B-PREP) — do not idle (S-03, F-05).

### MAINTENANCE
- Create a git remote so E-06 (local absence ≠ remote absence) is actually enforceable. Currently local-only, which is a real single-point-of-failure for cross-machine recovery.

## Blockers
Tier 0 **cannot be closed** on Windows alone. After HG-3 approval the remaining gates are: **spend approval + Apple Developer enrollment** (T0-A, and by extension the T0-B tooling), **external user recruitment** (T0-B), and **landing page + payment path** (T0-C2). This blocks the *gate*, not the *mission* — all PREP and harness-authoring work proceeds.

## Risks
| Risk | Note |
|---|---|
| Tier 0 gate stalls indefinitely | If HG-2/3/4 stay unresolved, C1 + PREP work will be exhausted and the mission genuinely idles. That would be the S-04 condition for escalating HG-9. |
| PF-01 simulated device numbers | Guarded by P-02. Watch for it. |
| Cleaner-rung commoditisation | The likely C1 finding is that the Cleaner rung is already free. That is expected, and is why the Constitution anchors paid value at Continuous Management and above. |

## Next action for a recovering session
Write `20_TIER0/T0B_RETRIEVAL_ENTRY_STUDY_PROTOCOL.md` (task set, standard test library, script, scoring sheet, anti-bias rules). Then author the Swift benchmark harness source, then `T0C2_LANDING_PAGE_PLAN.md`.

## Key findings so far (do not re-derive)
- Cleaner rung is commoditised: 10 cleaners all free-to-install, top app 701k ratings, one competitor giving cleaning away free. Do **not** test a Cleaner-rung price.
- Category monetises via weekly subs $4-12/wk ($207-623/yr) with documented predatory patterns. Credible non-predatory price point is a **$29.99-49.99 lifetime/one-off**.
- Search rung is thin: Queryable $4.99 one-off, 88 US ratings despite HN #1.
- **Lucent Pro** (id 6749473261) occupies this project's exact positioning — on-device AI photo manager, NL search, 200+ smart collections — and has **0 ratings**. Recorded as **UNKNOWN-1**: demand verdict vs distribution verdict, unresolved. Do not cite either way.
- On-device semantic search ships in 206-262MB binaries → no 2GB+ model dependency is implied (supports P-04).

### T0-A environment (DEC-008, do not re-derive)
- **A cloud Mac cannot have an iPhone plugged into it.** Delivery must go via TestFlight, which is why the 99 USD Apple Developer Program is on the critical path.
- **TestFlight requires iOS 16+; iPhone 7 maxes at iOS 15.8.x; A10 has no Neural Engine.** iPhone 7 is therefore excluded from the campaign — verified fact, not preference.
- Scaleway Mac mini M1 EUR 0.11/hr, 24h minimum lease → ~EUR 2.64 per block. M2 EUR 0.17/hr if 8GB proves cramped.
- 30k/100k libraries are reached by **on-device synthetic asset insertion**, not by transferring images. Real vs synthetic counts reported separately (DEC-009).
