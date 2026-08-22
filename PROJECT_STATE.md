# PROJECT STATE
**Read this file first, every session.** Canonical runtime state (Playbook E-03).
Last updated: 2026-08-22 · Session 001 (9 deliverables; T0-B/D study materials complete)

## Coordinates
- Project: Personal Visual Memory Engine (智能照片管理系统)
- Repo: `D:\photomanage` · branch `main` · remote: **none yet** (local-only — see MAINTENANCE queue)
- Stage: **M1 / Tier 0 — 生死开关**
- Environment: Windows 10, Python 3.12.10, git 2.9. No Mac, no Xcode. Owner has an iPhone.

## Authority (never re-derive this)
L1 Product Constitution **v1.3** → L2 P0 Execution Index v1.0 + Tier 0/1/2 **v1.1** → L3 Engineering Playbook **v1.1** → L4 Skills/Tools.
**→ Read `CONSTITUTION_UNDERSTANDING.md` before acting on anything product-related.** It is the section-by-section digest of L1, created after a real misreading on 2026-08-22 (PF-08). It never overrides the source — re-read the cited section before deciding.
Full map: `DOCUMENTATION_MAP.md`. Decisions: `DECISIONS.md`. Rules: `OPERATING_RULES.md`.

## Done
- **M0 Bootstrap complete.** 11 source documents audited, authority levels assigned, 4 superseded/duplicate files archived, 5 conflicts resolved (C-1…C-5), Money OS package sealed out of scope.
- Persistent state established: MISSION_SPEC, MASTER_PLAN, PROJECT_STATE, OPERATING_RULES, DECISIONS, FAILURE_PATTERNS, SESSION_HANDOFF, DOCUMENTATION_MAP, VALIDATION_MATRIX. No pre-existing equivalents were duplicated — the folder contained zero markdown files.
- Validation matrix built for all three tiers with measurable pass criteria.
- Plain-text mirror of every source .docx committed for grep-able reuse.

## Doing now
**T0-C2-PREP** — landing-page value-ladder copy + measurement plan, derived from the pricing matrix. (`WINDOWS_OK`)

This is the **last fully unblocked Tier-0 item**. After it, everything remaining needs Owner action (HG-1/2a/4). See S-04: entering WAITING requires proving nothing authorised is executable.

⚠️ **Awaiting Owner approval of EUR 2.64 only** (Scaleway one 24h M1 block). Nothing purchased.
- **$99 Apple Developer: approved in principle, paid only AFTER a successful cloud-Mac compile** (DEC-015).
- **$29.99 Lucent: cancelled** — Owner decided not to download or buy it (DEC-013).

## Work queue

### ACTIVE
1. ~~**T0-C1** Competitor pricing matrix~~ — ✅ **DONE** → `20_TIER0/evidence/COMPETITOR_PRICING_MATRIX.md`
2. ~~**T0-A-PREP** Device benchmark harness spec~~ — ✅ **DONE** → `20_TIER0/T0A_DEVICE_BENCHMARK_HARNESS_SPEC.md`
3. ~~**T0-A-MAC-PLAN** Cloud Mac environment + device gradient plan~~ — ✅ **DONE** → `20_TIER0/T0A_MAC_ENVIRONMENT_AND_DEVICE_PLAN.md` (pre-payment report, awaiting approval)
4. ~~**T0-B-PREP** Retrieval-entry study protocol~~ — ✅ **DONE** (revised to two arms per DEC-013)
4b. ~~**T0-D-PREP** Autonomous Management Value Prop protocol~~ — ✅ **DONE** → `20_TIER0/T0D_AUTONOMOUS_MANAGEMENT_VALUE_PROP_PROTOCOL.md`
4c. ~~**CONSTITUTION digest**~~ — ✅ **DONE** → `CONSTITUTION_UNDERSTANDING.md`
5. ~~**LUCENT-ANALYSIS** Benchmark Competitor No.1 deep analysis~~ — ✅ **DONE** → `20_TIER0/evidence/LUCENT_PRO_BENCHMARK_COMPETITOR.md`
6. ~~**T0-A-HARNESS** Swift benchmark harness~~ — ✅ **DONE** → `20_TIER0/harness/` (13 files, ~1,400 lines, **NEVER COMPILED** — see README known gaps)
7. ~~**T0-B/D-ASSETS** Study materials~~ — ✅ **DONE** → `20_TIER0/study_assets/` (generator + 4 ledger variants + facilitator script + 2 scoring sheets)
8. **T0-C2-PREP** Landing-page value-ladder copy + measurement plan, derived from C1. Owner launches it. — **NEXT**

### RESEARCH
- Apple-native on-device capability survey (Vision, Core ML, Live Text/OCR, PhotoKit limits) — FACT/INTERPRETATION separated, feeds the T0-A compute budget and the P-04 route decision. **No model dependency may be added without benchmark evidence.**

### EXPERIMENT
- (empty — Tier 0 experiments are all device- or user-blocked)

### HUMAN_GATE
| Gate | Blocker | Wake condition | First action on wake |
|---|---|---|---|
| **HG-3** (T0-A) | ✅ **APPROVED IN PRINCIPLE 2026-08-22** — cloud Mac only, existing 6-iPhone fleet. Reduced to the spend gate below | — | — |
| **HG-2a** (blocking T0-A) | **Spend approval: EUR 2.64 Scaleway only.** Nothing purchased | Owner approves EUR 2.64 | Provision Scaleway M1, install Xcode, compile, run in Simulator, then STOP and report |
| **HG-1** (blocking T0-A delivery) | Apple Developer enrollment + $99. **Deferred until after a successful compile** (DEC-015). Owner must enroll personally — legal name, own credit card, 2FA, possibly photo ID | Build compiles → Owner enrolls and pays | Archive, sign, upload to App Store Connect, release to TestFlight |
| **HG-4** (blocking T0-B **and T0-D**) | No recruited external test users (n>=10). Tooling half solved by the same Mac environment — **purely a recruitment problem** | Users recruited **and** prototype built | Run T0-B, then T0-D with the same participants on separate instruments |
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
Write `20_TIER0/T0C2_LANDING_PAGE_PLAN.md` (value-ladder copy at the Continuous Management rung, price test design, measurement plan). Then the queue is exhausted of unblocked work — do NOT idle without first re-checking S-04.

## Key findings so far (do not re-derive)
- Cleaner rung is commoditised: 10 cleaners all free-to-install, top app 701k ratings, one competitor giving cleaning away free. Do **not** test a Cleaner-rung price.
- Category monetises via weekly subs $4-12/wk ($207-623/yr) with documented predatory patterns. Credible non-predatory price point is a **$29.99-49.99 lifetime/one-off**.
- Search rung is thin: Queryable $4.99 one-off, 88 US ratings despite HN #1.
- **Lucent Pro** (id 6749473261) = **Benchmark Competitor No.1**. Read `20_TIER0/evidence/LUCENT_PRO_BENCHMARK_COMPETITOR.md` before citing anything about it. Corrections on record: rating volume is **below Apple's display threshold**, NOT "0 ratings"; development was **dense v1.5→v2.0 (Dec 2025 → 2026-02-04)**, quiet since — not abandoned after launch. **UNKNOWN-1 stands**: weak demand vs weak distribution is unresolved; do not cite either way. **UNKNOWN-5**: the $29.99 SKU period is not stated — do not call it lifetime.
- **Lucent is not purchased or installed** (DEC-013). Its free tier caps at 1,000 analysed photos, which is why any study that *did* include it would have to buy Premium — the fair-configuration rule (PF-07) now binds **Apple Photos** instead: full authorisation, People indexed, indexing complete, verified per session.
- **Our differentiator is visible on first open — do not re-derive this wrongly (DEC-012, PF-08).** The product has TWO organisation layers: **基础整理** = first-run full-library cataloguing (Constitution §12, **immediate**) and **持续整理** = continuous hygiene (§13, gradual). Plus the entry point changes (§22/§23): the user stops opening Apple Photos to look at their own photos. Lucent analyses a library so you can *search* it; we hand it back *organised*. An earlier session wrongly merged these two layers and concluded we were "harder to sell" — corrected by Owner challenge.
- **PF-06 reframed:** the risk is not that our value is invisible, it is drifting into shipping a search tool instead of an organised library.
- On-device semantic search ships in 206-262MB binaries → no 2GB+ model dependency is implied (supports P-04).

### T0-B / T0-D study design (DEC-011/012/013/014, do not re-derive)
- **Two arms only: Apple Photos vs our prototype.** Lucent is NOT installed or purchased (DEC-013) — it stays a documentary reference. Two parts: standardised loaner library (both arms) + participant's own library (Apple Photos only, where the real complaint list comes from).
- **T0-D runs after T0-B with the same participants, on separate instruments, into a separate deliverable. Neither study may substitute for the other** (Owner instruction, DEC-014). T0-D is mandated by Constitution §7, which requires the automation-tolerance bet be validated by real users rather than engineer assumption.
- **The prototype leads with the already-catalogued library, not a search box.**
- Sharpest single measurement: *"without tapping, where would you expect your passport to be?"* — tests predictability, which is what separates a destination from a tool.
- PASS thresholds pre-registered (P-1..P-6, n≥10). B FAIL = NO-GO/PIVOT, not a prompt to add features.
- Known limitation L-1: arm C's catalogue is hand-prepared — proves the concept, not the engine. Must be stated in the summary, not a footnote.

### T0-B/D study materials (built 2026-08-22, do not rebuild)
- `20_TIER0/study_assets/` — generator, ledger variants, facilitator script, two scoring sheets.
- Test library: **deterministic** (SEED 20260822), composition verified within **0.3pp** of §5 at 10k assets.
- **Foreground/background split is the key design**: 136 assets carry every task target and hard negative and need REAL imagery; 9,864 are synthetic filler for scale and noise. Placeholders are stamped so they cannot be used in a real session by accident.
- The 4 ledger variants are **generated from one template** — a between-subjects manipulation is only valid if variants differ solely in the manipulated dimension. Never hand-edit the HTML; change `LIBRARY` in the script and regenerate.
- **V1 vs V4 is the sharpest comparison**: identical facts, opposite order. If V4 reads as homework and V1 as a service, presentation is carrying the value proposition.

### T0-A harness (authored 2026-08-22, do not rewrite)
- `20_TIER0/harness/` — 13 Swift files. **Written on Windows, never compiled.** Expect first-build errors; fixing them on the Mac is minutes, authoring there would have been hours.
- No `.xcodeproj` — hand-written pbxproj is fragile. README has the ~10-minute Xcode setup: new SwiftUI App, drag sources, Background Modes capability, 3 Info.plist keys, deployment target iOS 16.
- Key choices not to undo: `isNetworkAccessAllowed=false` everywhere (C-2); Apple-native `VNGenerateImageFeaturePrintRequest` for L2 (zero bundled model, P-04); raw SQLite3 with no SPM dependency; synthetic assets at realistic 4032×3024 pixels with heavy compression; thermal as **dwell time**; memory as **footprint** not resident size.
- Most likely to need fixing first: the mach/`task_info` bridging in `Telemetry.swift`.
- Known unfinished: `PHPhotoLibraryChangeObserver` change-set handling for **edits to old assets** — the incremental path currently stops at the first known asset, which is correct for new captures but not for modifications. Finish before treating the A4 verdict as final.

### T0-A environment (DEC-008, do not re-derive)
- **A cloud Mac cannot have an iPhone plugged into it.** Delivery must go via TestFlight, which is why the 99 USD Apple Developer Program is on the critical path.
- **TestFlight requires iOS 16+; iPhone 7 maxes at iOS 15.8.x; A10 has no Neural Engine.** iPhone 7 is therefore excluded from the campaign — verified fact, not preference.
- Scaleway Mac mini M1 EUR 0.11/hr, 24h minimum lease → ~EUR 2.64 per block. M2 EUR 0.17/hr if 8GB proves cramped.
- 30k/100k libraries are reached by **on-device synthetic asset insertion**, not by transferring images. Real vs synthetic counts reported separately (DEC-009).
