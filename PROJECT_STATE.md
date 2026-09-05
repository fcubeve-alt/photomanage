# PROJECT STATE
**Read this file first, every session.** Canonical runtime state (Playbook E-03).
Last updated: 2026-09-06 · Session 002 — machine migration; tooling repaired and guarded (DEC-025)

## Coordinates
- Project: Personal Visual Memory Engine (智能照片管理系统)
- Repo: `D:\Documents\GitHub\photomanage` · branch `main` · remote: **`github.com/fcubeve-alt/photomanage` (PRIVATE)**
- Stage: **M1 / Tier 0 — 生死开关**
- Environment: **new machine since 2026-09-06** — Windows 10 Pro 19045, user `claudetest`, Python **3.14.3**, git **2.50.0** on `PATH` and working unprefixed. No Mac, no Xcode. Owner has ~6 iPhones (7 → 17).
- ⚠️ **Console locale is cp936 (Chinese Windows).** Every Python entry point now pins its own stdout to UTF-8, so the tools run unprefixed — but **anything new that prints `⚠️`/`✅` must do the same**, or it dies on `print` after doing all its work. See **PF-10 / DEC-025**.
- ⚠️ **`gh` is NOT installed on this machine.** HG-1 (adding signing secrets) and dispatching either CI workflow both run through it. Install GitHub CLI and `gh auth login` as `fcubeve-alt` (scopes `repo` + `workflow`) before touching Actions.
- The previous machine's git trap (system git 2.9.0 unable to reach GitHub, `C:\Users\admin\tools` PATH prefix) **does not apply here** — historical only, DEC-018.

## Architecture methodology (L1-B, 2026-08-24)
**Information-Change-First / Minimum Necessary Inference** is now a binding long-term
engineering constraint → **`ARCHITECTURE_METHODOLOGY.md`** (digest + conflict review +
the FC-1…FC-7 register).
> *Do not understand everything. Understand what changed, and spend intelligence only
> where it creates new memory.*
It changed **no** product goal, taxonomy, risk grade, lifecycle, retrieval path or the
Tier 0 execution order. Two violations are **marked, not fixed**: **MNI-1** the harness
computes `dHash` and never uses it to skip work (**FC-1, Owner decision, recommended
before the device campaign**); **MNI-2** the corpus is photos-only, so A1 is an
optimistic bound for mixed libraries (**FC-2, state as a limitation**).

## Authority (never re-derive this)
L1 Product Constitution **v1.3** → **L1-B Architecture Methodology v1.0** → L2 P0 Execution Index v1.0 + Tier 0/1/2 **v1.1** → L3 Engineering Playbook **v1.1** → L4 Skills/Tools.
**→ Read `CONSTITUTION_UNDERSTANDING.md` before acting on anything product-related.** It is the section-by-section digest of L1, created after a real misreading on 2026-08-22 (PF-08). It never overrides the source — re-read the cited section before deciding.
Full map: `DOCUMENTATION_MAP.md`. Decisions: `DECISIONS.md`. Rules: `OPERATING_RULES.md`.

## Done
- **M0 Bootstrap complete.** 11 source documents audited, authority levels assigned, 4 superseded/duplicate files archived, 5 conflicts resolved (C-1…C-5), Money OS package sealed out of scope.
- Persistent state established: MISSION_SPEC, MASTER_PLAN, PROJECT_STATE, OPERATING_RULES, DECISIONS, FAILURE_PATTERNS, SESSION_HANDOFF, DOCUMENTATION_MAP, VALIDATION_MATRIX. No pre-existing equivalents were duplicated — the folder contained zero markdown files.
- Validation matrix built for all three tiers with measurable pass criteria.
- Plain-text mirror of every source .docx committed for grep-able reuse.

## Recovery guarantee (DEC-022)
`python recovery_check.py --strict` verifies that a session with no conversation history can reach the next action unaided. It runs in CI on every `.md` change and **must stay green** — a FAIL means a fresh session would have to ask the Owner, or would re-solve something already solved.
Last run: **29 checks, 0 FAIL, RECOVERY VIABLE.**

## Tier 0 gate
`20_TIER0/TIER0_GO_NO_GO.md` — template in place, gate logic fixed in advance:
**A or B FAIL → NO-GO/PIVOT · A+B PASS but C FAIL → COMMERCIAL PIVOT (the product survives, DEC-002) · D FAIL → escalate to Owner as a potential Kill (DEC-014, PF-08).**
Within A: **A3 survivability failure is fatal**; an A1-only failure degrades scope to "recent N months" rather than killing the product.
**`NO DATA` is never a soft PASS** — a workstream not run leaves the gate INCOMPLETE, and Tier 1 may not begin on partial evidence.

## Doing now
> ### Nothing of the product is built. Zero lines. (PF-11)
> ~1,650 lines of Swift = a stopwatch that times photo reads. 82 prototype pages = hand-authored, no engine. ~3,100 lines of Python = generators and analyzers that never ship. **The classifier, taxonomy engine, entity resolver, lifecycle engine and risk policy engine are at zero lines and still LOCKED.** Green test results are evidence about tools, never about the product.

**Owner decisions 2026-09-06:**
- **T0-C and T0-D cancelled; the product is a GO** (DEC-026).
- **T0-B stays** — OPEN-2 closed (DEC-027). No longer a kill test, still wanted work. Its materials are out of freeze.
- **HG-1 is blocked on a payment instrument, not on willingness** (DEC-027). The Owner will pay the $99; Apple's enrolment does not accept the payment method available to them. Duration unknown. Per S-03 this blocks **T0-A's device measurement only.**

**T0-A — everything possible at $0 is done:**
1. ~~Compiles green~~ ✅ (DEC-018)
2. ~~**Runs** on the iOS Simulator~~ — ✅ **17 tests, 0 failures** (run 33984153562). Covers CSV column parity and the `iPhone14,5` comma, the C-1 OCR gate decisions, `dHash` stability, index cursor persistence across restarts, and the DEC-009 rule that cleanup can only reach assets the harness created.
3. **FC-1 + FC-1a — the one substantive engineering item left, and it is unblocked.** See `ARCHITECTURE_METHODOLOGY.md`. In plain terms: the harness computes a cheap fingerprint for every photo, stores it, and **never looks at it again**, so an identical re-downloaded image is fully re-analysed every time. **A1 is therefore measuring a naive baseline, and a real library full of duplicates would look worse than the intended design actually is.** The FC-1a precondition found on 2026-09-06: `dHash` returns 0 both for a whole class of ordinary images *and* for every hash failure, so a hash match alone must never authorise a skip.
4. **HG-1 → device campaign.** Blocked as above. Everything downstream of it is written and green.

**T0-B — unblocked work available now:**
- Source the 136 foreground images per `20_TIER0/study_assets/FOREGROUND_SOURCING_WORKSHEET.md`. Two Owner questions at the top of it are still unanswered: the route for the 49 `people_family` assets, and confirmation of the specimen-document line.
- Then **HG-4** — n ≥ 15 external participants. Needs no Mac, no TestFlight and no spend.

⚠️ **Spend status.** Nothing purchased.
- **$99 Apple Developer** — approved by the Owner, blocked on payment method.
- ~~$500–700 ad spend + domain~~ — cancelled with T0-C2 (DEC-026).
- ~~$29.99 Lucent~~ (DEC-013) · ~~Scaleway EUR 2.64~~ (DEC-016) — both gone.

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
8. ~~**T0-C2-PREP** Landing-page plan + copy~~ — DONE → `20_TIER0/T0C2_LANDING_PAGE_PLAN.md`
9. ~~**T0-B/D-SOURCING** Foreground image sourcing worksheet~~ — ✅ **DONE 2026-09-06** → `20_TIER0/study_assets/FOREGROUND_SOURCING_WORKSHEET.md`. Generated from the manifest, and it **verifies the 8 section-3 constraints against the library** rather than transcribing them — a second white-top Ben now makes the generator refuse to write. Two Owner decisions are flagged at the top of it.

### RESEARCH
- Apple-native on-device capability survey (Vision, Core ML, Live Text/OCR, PhotoKit limits) — FACT/INTERPRETATION separated, feeds the T0-A compute budget and the P-04 route decision. **No model dependency may be added without benchmark evidence.**

### EXPERIMENT
- (empty — Tier 0 experiments are all device- or user-blocked)

### HUMAN_GATE
| Gate | Blocker | Wake condition | First action on wake |
|---|---|---|---|
| **HG-3** (T0-A) | ✅ **APPROVED IN PRINCIPLE 2026-08-22** — cloud Mac only, existing 6-iPhone fleet. Reduced to the spend gate below | — | — |
| ~~Scaleway rental~~ | ~~EUR 2.64~~ — **WITHDRAWN (DEC-016).** GitHub Actions replaced it at $0 | — | — |
| ~~**HG-5**~~ | ~~No GitHub remote~~ — ✅ **DONE 2026-08-22.** `fcubeve-alt/photomanage`, private, 170 files, CI green | — | — |
| **HG-1** ← **NOW THE CRITICAL PATH** | Apple Developer enrolment + **$99**. Precondition (green build) is **satisfied** — DEC-018. Owner must enrol personally: legal name, own credit card, 2FA, possibly photo ID. Then add 8 repo secrets | Owner enrols, pays, adds secrets | Dispatch `ios-testflight.yml`: archive, sign, upload, release to TestFlight, then run A1–A4 on the fleet |
| **HG-4** (blocking T0-B **and T0-D**) | **No recruited external test users (n>=10).** Corrected 2026-08-22: these two studies need **no Mac, no TestFlight and no $99** — the prototype is HTML. Prototype is built. This is now **purely a recruitment + test-library-prep problem** | ≥10 external users recruited, test library loaded on a loaner iPhone | Run T0-B, then T0-D with the same participants on separate instruments |
| **HG-2** (blocking T0-C2) | Domain (~$12) + **ad spend ~$500-700** + Owner approval of positioning, $39 price and the disclosure wording | Owner approves and funds | Build and publish 3 arms, run traffic, collect E1-E8 |

### CAPABILITY
- Web search/fetch: available. If it drops, fall back to the search-free queue (T0-A-PREP, T0-B-PREP) — do not idle (S-03, F-05).

### MAINTENANCE
- ~~Create a git remote~~ — ✅ done. E-06 cross-machine recovery gap closed, and **proven in the real event** on 2026-09-06: the project moved machines and a cold session recovered from the repo alone (DEC-025).
- ~~Persist the git tools on `PATH`~~ — moot. The new machine's git 2.50.0 is already on `PATH` and works unprefixed.
- **Install GitHub CLI on this machine** and `gh auth login` as `fcubeve-alt` with scopes `repo` + `workflow`. Not needed for local work; needed the moment HG-1 opens or a workflow must be dispatched.

## Blockers
Tier 0 **cannot be closed** on Windows alone. After HG-3 approval the remaining gates are: **spend approval + Apple Developer enrollment** (T0-A, and by extension the T0-B tooling), **external user recruitment** (T0-B), and **landing page + payment path** (T0-C2). This blocks the *gate*, not the *mission* — all PREP and harness-authoring work proceeds.

## Risks
| Risk | Note |
|---|---|
| Tier 0 gate stalls indefinitely | If HG-2/3/4 stay unresolved, C1 + PREP work will be exhausted and the mission genuinely idles. That would be the S-04 condition for escalating HG-9. |
| PF-01 simulated device numbers | Guarded by P-02. Watch for it. |
| Cleaner-rung commoditisation | The likely C1 finding is that the Cleaner rung is already free. That is expected, and is why the Constitution anchors paid value at Continuous Management and above. |

## Idle justification (S-04) — re-checked 2026-09-06
Every Tier-0 workstream is prepared to the boundary of an Owner gate, and every measurement chain is closed:
- **T0-A** — spec + harness (compiles green on CI) + XcodeGen spec + both CI workflows + self-tested analyzer. Needs **HG-1** ($99, condition already satisfied by the green build).
- **T0-B** — protocol + clickable prototype + test-library manifest + facilitator script + scoring sheet + self-tested analyzer. Needs **HG-4** (n ≥ 15 participants) and the 136 real foreground images.
- **T0-C1** — COMPLETE. **T0-C2** — three instrumented landing pages built and smoke-tested. Needs **HG-2** (~$520–720).
- **T0-D** — protocol + 4 ledger variants + scoring sheet + self-tested analyzer. Needs **HG-4**, same cohort as T0-B.

Two items of build-ahead work remain that need no approval (the 136 foreground images, and the FC-1 recommendation), so the mission is **not** blocked (S-03). Do not enter WAITING. When those two are exhausted, the S-04 condition for escalating **HG-9** is genuinely reached and should be escalated rather than filled with invented work.

## Next action for a recovering session
**FC-1 + FC-1a.** It is the only substantive engineering item that is both unblocked and on the critical path — HG-1 is stuck on a payment instrument for an unknown time (DEC-027), and until it clears, FC-1 is the only thing that improves the T0-A result rather than just waiting for it. Read `ARCHITECTURE_METHODOLOGY.md` FC-1 and FC-1a first; the precondition is mandatory and is locked into `Layer1SignalsTests.testAWholeClassOfImagesHashesToZero`.

In parallel, T0-B is live again (DEC-027): the 136 foreground images can be sourced from `FOREGROUND_SOURCING_WORKSHEET.md` as soon as the Owner answers its two questions.

**Do not** report any of this as product progress. See PF-11.

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

### Build/CI facts (DEC-016 + **DEC-018 measured**, do not re-research)
- **UNKNOWN-6 RESOLVED at zero cost.** Timing API reports `billable.MACOS.total_ms = 0` on a **private** repo — included allowance covers it. The case for making the repo public to get free minutes is closed **on evidence**. Strategy stays unpublished.
- Measured build: **48 seconds** end to end, far under the 4–8 min estimate.
- Two environment traps, both fixed, both silent-failure modes worth remembering: (a) `credential.helper = manager` configured while GCM was never installed → git exit 128 with empty stderr; (b) git 2.9.0 cannot negotiate TLS with GitHub at all, and neither `http.sslVersion=tlsv1.2` nor disabling `sslVerify` helps. `gh` kept working throughout, which is what isolated the fault to git.
- `macos-latest` = macOS 26 arm64; `macos-15` arm64 GA; `macos-14` deprecated. Xcode 16.0-16.4 (16.4 default) + 26.x preinstalled.
- Standard macOS runner = $0.062/min, free and unmetered on public repos; Free plan gives 2,000 included min/mo, 5 concurrent macOS jobs, 500 MB artifacts, 6 h job cap.
- **UNKNOWN-6**: 10x vs 1x multiplier on private-repo included minutes post-Jan-2026 repricing. Costed both ways; irrelevant to the decision. Resolve from the account billing page once the repo exists.
- `.xcodeproj` is **generated by XcodeGen** from `20_TIER0/harness/project.yml` — never hand-written, never committed.

### T0-C2 design (do not re-derive)
- **Positioning is the manipulation, price is held constant** — the Tier 0 question is *which rung is paid for*, not *what is the optimal price*. 3 arms at $39 one-off: L1 Organised Library, L2 Continuous Manager, L3 Cleaner **control**.
- L3 exists to make L1/L2 interpretable, not as a candidate positioning (§24 Gate 4 forbids shipping as a Cleaner).
- $39 from C1: every credible non-predatory competitor sits at $29.99-49.99 one-off. Weekly subscription excluded on trust grounds.
- **No money is ever taken.** Fake-door with a mandatory full-screen disclosure the instant someone commits. No dark patterns. Deposit variant held in reserve for an ambiguous result only.
- **No third-party ad pixel on the landing page** — running a privacy-first product test on surveillance infrastructure would be the first broken promise (§26).
- **Run T0-D first where possible**: it tells us whether the rung is wanted before ~$600 is spent advertising it, and its verbatims should rewrite the copy.

### T0-B/D study materials (built 2026-08-22, do not rebuild)
- `20_TIER0/study_assets/` — generator, ledger variants, facilitator script, two scoring sheets.
- Test library: **deterministic** (SEED 20260822), composition verified within **0.3pp** of §5 at 10k assets.
- **Foreground/background split is the key design**: 136 assets carry every task target and hard negative and need REAL imagery; 9,864 are synthetic filler for scale and noise. Placeholders are stamped so they cannot be used in a real session by accident.
- **The home is the Visual Library entry point, NOT an AI work-report dashboard** (DEC-017). First-run result compresses into a 3-line header; the library takes the prime real estate; the work report sits below it.
- **ORGANIZED is a taxonomy with drill-down, not flat count tiles.** 11 top-level entries (§23), 3 levels deep where it matters: `Documents › Identity › Passports`. Flat tiles are structurally the same as Lucent smart collections — the PF-06 failure.
- Cross-listing is **shown**, not hidden: Receipts carries "also in Purchases › Receipts", making §3 (one asset, many entries, no copies) visible as a differentiator.
- Prototype: `study_assets/prototype/`, 82 pages, generated by `build_prototype.py`. The 4 T0-D variants are variants of this same home; the library section is byte-identical across all four (verified each build). Never hand-edit the HTML.
- **V1 vs V4 is the sharpest comparison**: V4 puts "23 need you" *above the library*. Same facts, opposite order — service vs homework.
- What is built is a **navigational skeleton**, hand-authored. It is NOT the Tier 1-A taxonomy (no classifier, no confusion matrix, no risk defaults). Do not let it drift into Tier 1.
- **OPEN-1 awaiting Owner ruling:** whether `Documents › Medical` may exist at all (§16 forbids unrequested health inference). Rendered as "pending decision", excluded from every task.

### T0-A harness (authored 2026-08-22, do not rewrite)
- `20_TIER0/harness/` — 13 Swift files. **Written on Windows, never compiled.** Expect first-build errors; fixing them on the Mac is minutes, authoring there would have been hours.
- No `.xcodeproj` — hand-written pbxproj is fragile. README has the ~10-minute Xcode setup: new SwiftUI App, drag sources, Background Modes capability, 3 Info.plist keys, deployment target iOS 16.
- Key choices not to undo: `isNetworkAccessAllowed=false` everywhere (C-2); Apple-native `VNGenerateImageFeaturePrintRequest` for L2 (zero bundled model, P-04); raw SQLite3 with no SPM dependency; synthetic assets at realistic 4032×3024 pixels with heavy compression; thermal as **dwell time**; memory as **footprint** not resident size.
- Most likely to need fixing first: the mach/`task_info` bridging in `Telemetry.swift`.
- Known unfinished: `PHPhotoLibraryChangeObserver` change-set handling for **edits to old assets** — the incremental path currently stops at the first known asset, which is correct for new captures but not for modifications. Finish before treating the A4 verdict as final.

### T0-A environment (DEC-008 + **DEC-016**, do not re-derive)
- **Build environment is GitHub Actions**, `macos-15` (arm64 Apple Silicon, standard runner, Xcode 16.4). Scaleway is a **fallback only**, for interactive bring-up if CI stalls. The EUR 2.64 ask is withdrawn.
- **Do NOT switch to `macos-15-xlarge` / `-large`** — those are *larger* runners and are billed even on public repos.
- **Repo must be PRIVATE.** Free minutes are not a reason to go public: ~150 bring-up minutes fit inside the 2,000/mo Free allowance either way, so private is free for our volume. Publishing would expose the Constitution, pricing strategy, the $39 test and the unlaunched landing copy.
- **Neither a cloud Mac nor a CI runner can have an iPhone plugged into it.** Delivery is TestFlight, which is why the 99 USD Apple Developer Program stays on the critical path.
- **TestFlight requires iOS 16+; iPhone 7 maxes at iOS 15.8.x; A10 has no Neural Engine.** iPhone 7 is therefore excluded from the campaign — verified fact, not preference.
- *(Fallback only)* Scaleway Mac mini M1 EUR 0.11/hr, 24h minimum lease → ~EUR 2.64/block; **stopping does not stop billing, deletion is impossible for 24h** — enable auto-delete if ever used.
- 30k/100k libraries are reached by **on-device synthetic asset insertion**, not by transferring images. Real vs synthetic counts reported separately (DEC-009).
