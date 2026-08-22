# DECISIONS
Append-only. Never edit a past entry — supersede it with a new one.
Format: ID · date · decision · rationale · evidence · impact · status

---

### DEC-001 · 2026-08-22 · "P0 / P1 / P2" maps to P0 Tier 0 / Tier 1 / Tier 2
**Decision.** The launch instruction refers to "P0、P1、P2 验证文档". No documents named P1 or P2 exist. The folder contains a single **P0 Kill Test programme** split into **Tier 0 / Tier 1 / Tier 2**, governed by `P0 KILL TEST | MASTER EXECUTION INDEX v1.0`. These are treated as the same thing.
**Rationale.** The Execution Index explicitly sequences `Tier 0 → decision → Tier 1 → decision → Tier 2 → final GO/NO-GO → full app development`, which is precisely the P0→P1→P2 dependency chain the Owner described. Inventing separate P1/P2 documents would create the duplicate-canonical-file problem the bootstrap is meant to prevent.
**Evidence.** Full directory listing; `P020Test20EXECUTION%20INDEX_v1.0.docx`.
**Impact.** Everything downstream sequences on Tier 0/1/2.
**Status.** ACTIVE. Owner may override with one sentence if P1/P2 were meant to be separate later-stage documents that have not been written yet.

---

### DEC-002 · 2026-08-22 · Tier documents v1.1 supersede the unversioned Kill Test files
**Decision.** `P020Test20*_v1.1.docx` are authoritative. The three unversioned `P0 Kill Test Tier*.docx` are archived to `90_ARCHIVE/SUPERSEDED/`.
**Rationale.** They conflict on a decision rule that matters. The old Tier 0 says *any* of A/B/C failing stops the project. v1.1 says **A or B** failing stops it, while **C failing triggers a Commercial Model Pivot and explicitly does not kill the product**. Executing both would be incoherent. Tier 1 differs by version stamp only; Tier 2 differs by an updated prerequisite clause that permits entry after a completed commercial pivot.
**Evidence.** Text diff of both sets — recorded in `DOCUMENTATION_MAP.md` §3.
**Impact.** A Tier 0-C failure will be reported as COMMERCIAL MODEL PIVOT, not NO-GO.
**Status.** ACTIVE.

---

### DEC-003 · 2026-08-22 · Constitution §19 does not authorise Tier-0 scope expansion
**Decision.** The nine additional validation items listed in Constitution §19 ("对 P0 Engineering Validation 的直接影响") are assigned to Tier 1 and Tier 2. They are **not** built during Tier 0.
**Rationale.** §19 declares scope for the whole P0 programme; the Execution Index allocates that scope across tiers and forbids pre-building later tiers. Reading §19 as a Tier-0 mandate would collapse the entire kill-test structure into one enormous first step — the exact failure the Index was written to prevent (and Playbook F-01: the first viable route hijacking the mission).
**Evidence.** Constitution §19; Execution Index "唯一执行规则".
**Impact.** Taxonomy, Entity Resolver, Risk Engine, Equivalence Margin and Personal Policy stay unbuilt until their tier unlocks.
**Status.** ACTIVE.

---

### DEC-004 · 2026-08-22 · Windows-only environment splits Tier 0, it does not stop it
**Decision.** Tier 0-A (device benchmark) and Tier 0-B (retrieval-entry user study) are tagged `REQUIRES_MAC` / `REQUIRES_DEVICE` / `REQUIRES_USERS` and marked **BLOCKED — NOT TESTED**. Work proceeds on Tier 0-C1 (competitor pricing matrix), which is fully executable on Windows, plus the Windows-side preparation that makes A and B one-session jobs once hardware and users exist.
**Rationale.** Owner instruction: do not pretend macOS-dependent validation is done, and do not stop the project for lack of a Mac. Playbook S-03: a blocked branch blocks only itself.
**Evidence.** Environment: Windows 10, no Mac, no Xcode. Owner has an iPhone but no local Mac.
**Impact.** `TIER0_GO_NO_GO.md` cannot be completed until HG-2, HG-3 and HG-4 are resolved. Tier 0 will reach a partial state with C1 evidence and prepared protocols for A/B.
**Status.** ACTIVE.

---

### DEC-005 · 2026-08-22 · Project M / Money OS package is out of scope and stays sealed
**Decision.** `Project_M_Master_Development_Package_v1.3.1_COMPLETE.zip` is moved to `90_ARCHIVE/OTHER_PROJECT_MONEY_OS/` and deliberately left unextracted.
**Rationale.** It is a different product (Money OS kernel + autonomous business brains M1/M2-A/M2-B/M2-C). Both the Owner instruction and Playbook §6 forbid importing its business content. Its engineering lessons already arrived here distilled as Playbook v1.1 — extracting the raw package would only risk contamination and burn context.
**Evidence.** Zip manifest and README read during audit; 90_REFERENCE_DOCS are all Project M business specs.
**Impact.** No Money OS concepts enter this codebase. One method-level artifact (the pre-install capability preflight discipline) is retained as reference text only.
**Status.** ACTIVE.

---

### DEC-006 · 2026-08-22 · Governance files at repository root; source docs sorted, nothing deleted
**Decision.** The seven Playbook-mandated state files plus `DOCUMENTATION_MAP.md` and `VALIDATION_MATRIX.md` live at repo root. Authoritative source documents move to `10_SOURCE_DOCS/`, superseded ones to `90_ARCHIVE/SUPERSEDED/`, Tier-0 work to `20_TIER0/`.
**Rationale.** A recovering session must find state without being told where to look, so state goes where it will be found first. Superseded documents sitting beside authoritative ones is the conflict risk the audit exists to remove. Archiving is reversible; deleting is not.
**Evidence.** Playbook §5 Bootstrap Checklist; Launch Instruction Phase B.
**Impact.** No equivalent canonical files pre-existed — the folder contained zero markdown — so none were duplicated.
**Status.** ACTIVE.

---

### DEC-007 · 2026-08-22 · Plain-text mirror of every source document is committed
**Decision.** `10_SOURCE_DOCS/_extracted_text/*.txt` holds a grep-able extraction of every authoritative .docx, with the extractor script alongside.
**Rationale.** The source material is Word-only. Without a text mirror, every future session re-parses binaries to answer one question — precisely the repeated-read waste T-01/T-02/T-07 forbid. Cost: one extraction. Benefit: permanent.
**Impact.** `OPERATING_RULES.md` P-06 makes the text mirror the required read surface. Regenerate if a .docx is updated.
**Status.** ACTIVE.

---

### DEC-008 · 2026-08-22 · HG-3 resolved via cloud Mac + TestFlight; iPhone 7 excluded; minimum supported model decided by benchmark
**Decision.** Owner approved HG-3 in principle: cloud Mac only, no Mac purchase, existing iPhone fleet (~6 devices, iPhone 7 through iPhone 17), Owner approval required before any actual payment. Consequent design decisions:
1. Build environment = **Scaleway Mac mini M1, hourly** (EUR 0.11/hr, one 24h block ~= EUR 2.64). Delivery to devices = **TestFlight**, which requires the **99 USD/yr Apple Developer Program**. Neither purchased; approval requested.
2. **iPhone 7 is excluded from the Tier 0-A campaign.**
3. Tier 0-A is redesigned from "3 device tiers" to a **cross-device performance gradient**, with the **minimum supported model derived from the measured curve**, never assumed in advance.
4. 30k/100k library sizes are reached by **on-device synthetic asset insertion** layered on top of each device's real library, with real and synthetic counts reported separately.

**Rationale.**
- A cloud Mac cannot have an iPhone physically attached, so the plan had to solve *delivery*, not just *build*. TestFlight is the only path that scales to five devices and repeated runs.
- iPhone 7 exclusion rests on three independently verified facts, not preference: TestFlight requires **iOS 16+**; iPhone 7 maxes at **iOS 15.8.x**; and A10 Fusion has **no Neural Engine** (ANE debuted with A11). Including it would cost a separate delivery path, a deployment target that forfeits every Vision/Core ML API added since iOS 15, and ANE-less execution — three compromises for one boundary datapoint. Owner had already ruled that core capability must not be sacrificed for old-device compatibility.
- Synthetic padding avoids transferring ~50-200 GB of imagery to a phone, which no available path supports. Tier 0-A is a performance/thermal test, not an accuracy test, so a synthetic corpus is valid for A1-A4 provided the screenshot/photo ratio approximates the real library and the composition is disclosed per row.

**Evidence.** scaleway.com/en/pricing/apple-silicon/ ; developer.apple.com/support/enrollment/ ; testflight.apple.com ("iPhone or iPad running iOS 16 or iPadOS 16 or later") ; Apple device support tables ; ANE device generation table. All retrieved 2026-08-22, recorded with confidence levels in `20_TIER0/T0A_MAC_ENVIRONMENT_AND_DEVICE_PLAN.md` Part 2.

**Impact.** HG-3 becomes a spend-approval gate rather than a hardware gate. Approving it also unblocks the **tooling** half of Tier 0-B, since the same environment builds the retrieval-entry prototype — leaving HG-4 as purely a user-recruitment problem. HG-1 (Apple Developer identity/KYC) is newly activated and must be performed by the Owner personally.

**Status.** ACTIVE. Blocked on Owner approval of EUR 2.64 + 99 USD.

---

### DEC-009 · 2026-08-22 · The benchmark harness may write to a real photo library, under strict conditions
**Decision.** The Tier 0-A harness inserts synthetic assets into the iOS photo library via `PHAssetCreationRequest` and deletes them afterwards. Conditions: insertion and cleanup are proven on a **secondary device with a disposable library first**; cleanup deletes **only assets the harness itself created**, tracked by local identifier; nothing pre-existing is ever touched; the Owner confirms before any primary device is used.
**Rationale.** There is no other way to reach 30k/100k on-device. But this project's own safety red line is "no silent permanent deletion" (Constitution, `OPERATING_RULES.md` P-03) — that rule has to bind the tooling too, not only the product, or it is not a real rule.
**Impact.** Adds a mandatory pre-flight step before the main campaign. Open question 3 to Owner.
**Status.** ACTIVE, pending Owner confirmation.

---

### DEC-010 · 2026-08-22 · Lucent Pro becomes Benchmark Competitor No.1; Tier 0-B becomes a 3-way study under a fair-configuration rule
**Decision.**
1. Lucent Pro is promoted from a matrix row to **Benchmark Competitor No.1**, with its own analysis file.
2. Tier 0-B changes from **Apple Photos vs us** to **Apple Photos vs Lucent Pro vs our prototype**.
3. A **fair-configuration rule** binds every comparative study: competitors are tested **fully paid, fully permissioned and fully finished analysing**, or the comparison is not run and the limitation is reported. Task order is counterbalanced; the facilitator follows a fixed script or is not the prototype's author.
4. The Tier 0-B prototype must include a **first-run quantified receipt** of work already done, including how little is left for the user.
5. Three earlier claims of mine are corrected on the record: "0 ratings" (→ below Apple's display threshold), "no update in six months" (→ dense v1.5→v2.0 run, quiet since February), and a weekly price string wrongly readable as Lucent's (→ it belongs to a recommended app on the same page).

**Rationale.**
- Lucent occupies the *search + collections* half of our target rung with a real shipped product. Testing only against Apple Photos would measure us against the wrong baseline and produce an easy win that tells us nothing about the competitor we would actually face.
- **The fair-configuration rule is not politeness, it is validity.** Lucent's free tier analyses only 1,000 photos. A 3-way study on a 20,000-photo library with free Lucent would measure Lucent's paywall and report it as our advantage — a result that collapses under the first challenge, after decisions have been made on it. Requires purchasing Lucent Premium ($29.99).
- The first-run receipt addresses the sharpest finding of the analysis: our differentiators accrue over weeks, Lucent's was instant and still did not convert. Being "more differentiated" may mean "harder to sell" unless autonomy is made visible in session one.

**Evidence.** `20_TIER0/evidence/LUCENT_PRO_BENCHMARK_COMPETITOR.md`, verified against the archived App Store page retrieved 2026-08-22.

**Impact.** T0-B protocol is written against this design. Adds a **$29.99** spend item. Adds `FAILURE_PATTERNS.md` PF-06 and PF-07. Tightens `OPERATING_RULES.md` P-04.

**Status.** ACTIVE.

---

### DEC-011 · 2026-08-22 · Recorded: our primary differentiator is unfalsifiable until Tier 2
**Decision.** Log explicitly that a Tier 0-B PASS proves users prefer our **structure and retrieval**, and proves nothing about whether they want, or will pay for, **autonomous management**. `TIER0_GO_NO_GO.md` must carry this limitation in its own words.
**Rationale.** The Tier 0-B prototype will not contain risk, lifecycle or same-entity capability, because building those now would violate the Execution Index (see DEC-003, P-01). So the differentiator we consider decisive cannot be tested in the tier that decides whether to continue. Naming that gap is the honest move; discovering it later while reading a B PASS as validation of the whole thesis is the failure mode.
**Consequence for study design.** The Owner's proposed sixth task — cleaning 8 near-identical burst photos — is an Equivalence Margin task (Tier 2-B). It is **kept but inverted**: the user performs it **manually in each app** and the effort is measured. That captures the pain our differentiator would remove, produces a baseline to beat later, and builds nothing that belongs to a later tier.
**Status.** **SUPERSEDED by DEC-012** — the claim was too broad. First-run cataloguing *is* testable in Tier 0-B; only the engine accuracy and the continuous/risk layers are not.

---

### DEC-012 · 2026-08-22 · CORRECTION: the first-run organised library is the headline differentiator, and it is visible immediately
**Supersedes the reasoning in DEC-011 and in Part 3 of the Lucent analysis.**

**What I got wrong.** I claimed our differentiators "accrue over weeks and months" and therefore that being more differentiated than Lucent might mean being harder to sell. To reach that I merged two distinct layers of the product and then reasoned from a competitor's unexplained failure over the top of a Level 1 document.

**What is actually true — the product has two organisation layers:**
1. **基础整理 — first-run full-library cataloguing (Constitution §12).** On first open the whole library is already catalogued into a library-style hierarchy, expired temporary content cleared, duplicates cleared, only a very small Review Queue left. §12 names the value moment itself: 『原来我的照片可以这么整齐，而且我不用自己整理。』 **This is immediate, not slow-burn.**
2. **持续整理 — continuous hygiene (§13).** Every subsequent photo auto-filed. This one does accrue over time.

**And the entry point changes (§22/§23).** After install the user stops opening Apple Photos to look at their own photos. That behavioural switch is the north star, it is what Tier 0-B measures as Retrieval Entry Share, and it is also felt immediately.

**Corrected position.** The headline differentiator is visible on first open by design. Lucent analyses a library so you can *search* it; we hand the library back *organised*. Genuinely slow-burn items are a short list and are not what we lead with: Personal Policy learning (§14), long-span Same-Entity (§9), derived services (§15).

**Correction to DEC-011.** DEC-011 said our primary differentiator is unfalsifiable until Tier 2. Too broad. Correct scope:
- **Tier 0-B CAN test:** whether the already-organised library beats Apple Photos and Lucent as the place users go to find things, and whether the "it is already organised and I did nothing" moment lands. The Tier 0 doc only requires a Structure First skeleton, so the test library catalogue may be prepared for the study — no engine required.
- **Tier 0-B CANNOT prove:** that our engine produces that catalogue reliably at scale (Tier 1), or that risk-aware automation is safe and wanted (Tier 2).
The burst-cleanup task stays inverted per DEC-011 — measure the manual effort, build nothing from a later tier.

**Rationale for recording this at all.** Level 1 may be overridden only by demonstrated technical infeasibility or documented material conflict — never by inference from a competitor whose failure cause is explicitly UNKNOWN (UNKNOWN-1). Logged as `FAILURE_PATTERNS.md` **PF-08**.

**Impact.** Lucent analysis Part 3 rewritten; PF-06 reframed from "our value is invisible" to "do not drift into shipping a search tool"; T0-B protocol will lead with the catalogued library rather than a search box.
**Status.** ACTIVE.

---

### DEC-013 · 2026-08-22 · Lucent Pro is NOT purchased or installed; Tier 0-B returns to a two-arm study
**Decision (Owner).** Do not download or buy Lucent Pro. It is removed as a study arm. Tier 0-B is **Apple Photos vs our prototype**, exactly as Tier 0 v1.1 §3 specifies. Lucent stays as a **documentary reference only** (`20_TIER0/evidence/LUCENT_PRO_BENCHMARK_COMPETITOR.md`).
**Rationale.** Owner assessment: its functionality is unremarkable, and Tier 0-B’s PASS bar is written against **Apple native**, not against a low-traction third party. Adding an arm we do not need lengthens an already long session, adds order effects, and spends money for a comparison the kill-question does not ask for.
**Supersedes.** The three-way design in DEC-010 point 2. Everything else in DEC-010 stands — Lucent is still Benchmark Competitor No.1 as an intelligence source, and the fair-configuration rule (PF-07) survives and now binds **Apple Photos**: an instance that has not finished indexing People, or lacks full authorisation, would hand us a rigged win.
**Impact.** Removes the **$29.99** spend and the pre-session analysis wall-time. Total pre-payment ask returns to **€2.64 + $99**. P-4 (beat Lucent) retired; P-1/P-2/P-3/P-5/P-6 unchanged. AB-1 counterbalancing simplifies to two sequences.
**Status.** ACTIVE.

---

### DEC-014 · 2026-08-22 · T0-D Autonomous Management Value Proposition added to Tier 0
**Decision (Owner).** Add a concept validation to Tier 0 testing whether users clearly prefer *「AI 替我持续管理，只把少数问题交给我决定」*, and whether a first-screen **Work-Done Ledger / Human Review Burden** conveys the core value immediately. Results recorded **separately** from Retrieval Entry; neither may substitute for the other.

**Why this is not scope creep.** Constitution §7 ends with an explicit instruction: *「用户获得巨大持续便利时，对少量、低代价、可恢复的判断错误可能具有容忍度；这必须通过真实用户测试验证，而不能只凭工程师假设。」* The Constitution mandates this test; the Tier 0 document does not contain one. **T0-D closes a gap between L1 and L2.** It is also a genuine kill-question: §17 makes the Risk-Aware Decision Engine the basis of autonomy, so if users reject the model, that fails *before* Tier 1 spends anything on taxonomy and entity resolution.

**Execution Index compliance.** Nothing from Tier 1 or Tier 2 is built. No classifier, no entity resolver, no lifecycle engine, no R0–R6 policy engine, no equivalence selection, no personal policy learning. What is built is **one screen and a structured interview**; the ledger numbers are hand-prepared for the test library, exactly as the T0-B catalogue is. The question is not *does our AI work* but *do users want an AI that does this at all* — answerable before any classifier exists. Limitation **L-4** must be stated in the report summary.

**Separation rule (Owner, binding).** T0-B answers *will they come here to find things* (§22/§23). T0-D answers *will they let it manage for them* (§5/§7/§12/§13). They can dissociate in both directions and are recorded in separate deliverables. Run D after B in the same session, never interleaved.

**Notable design points.** Four ledger variants isolate what carries the value — V1 Full vs **V4 Review-first** is the sharpest, since identical facts in the opposite order test whether the product reads as a service or as homework. Step 4 validates the §6 R0–R6 ladder **as measured user preference** rather than assumption. Step 5 quantifies §7’s recoverability argument for the first time. Step 6 produces the first empirical **Human Review Burden** target for §18, replacing an engineering guess.

**Failure handling.** D-P1 failure (users reject autonomous management) **contradicts Constitution §5–§7 and §17** and is therefore escalated to the Owner as a potential Kill result — never quietly redesigned around (PF-08).

**Impact.** New workstream **T0-D** in `VALIDATION_MATRIX.md`; new deliverable `AUTONOMOUS_MGMT_VALUE_PROP_TIER0.md`; `TIER0_GO_NO_GO.md` now carries four workstreams (A/B/C/D). No new spend — same participants, same prototype, same device.
**Status.** ACTIVE.

---

### DEC-015 · 2026-08-22 · Apple Developer $99 paid only after the first successful cloud-Mac compile
**Decision (Owner).** The $99 Apple Developer Program fee is approved in principle but is paid **only after the cloud Mac has successfully compiled the project**, not before.
**Rationale.** It sequences the risk correctly: the cheap, reversible €2.64 Mac block proves the toolchain works and the project builds; only then is the annual, non-refundable fee committed. If the build fails for reasons we have not anticipated, we have spent €2.64 instead of $102.
**Consequence for the plan.** Phase 2 of `T0A_MAC_ENVIRONMENT_AND_DEVICE_PLAN.md` splits: **2.1–2.3 build and verify → STOP → report success to Owner → Owner enrolls and pays $99 → 2.4–2.5 archive, sign, upload to TestFlight.** Enrollment is HG-1 and must be done by the Owner personally (legal name, own credit card, 2FA, possibly photo ID).
**Note.** A signing identity is not needed to compile and run in the Simulator, so the pre-payment build check is genuinely possible. Whether the 24-hour block can be paused or must be re-leased after the approval round-trip is a practical detail to confirm at provisioning; if it cannot, budget a second €2.64 block.
**Status.** ACTIVE.

---

### DEC-016 · 2026-08-22 · GitHub Actions macOS runners become the primary build environment; Scaleway demoted to fallback
**Decision (Owner-initiated, evidence confirms).** Tier 0-A builds, archives, signs and uploads to TestFlight via **GitHub Actions standard macOS runners**. Scaleway is kept as a documented fallback for interactive bring-up only. **The EUR 2.64 Scaleway ask is withdrawn.** Repository is to be **PRIVATE**.

**Verified facts (2026-08-22).**
- "GitHub Actions usage is free for standard GitHub-hosted runners in public repositories" (docs.github.com, verbatim).
- `macos-latest` = macOS 26 **arm64 Apple Silicon**, GA; `macos-15` also arm64 GA; `macos-14` deprecated.
- Standard macOS SKU = "macOS 3-core or 4-core (M1 or Intel)" at **$0.062/min**. The `-xlarge`/`-large` variants are *larger* runners and are billed even on public repos.
- `macos-15-arm64` ships Xcode **16.0-16.4 (16.4 default)** and 26.x; iOS SDKs 18.0-26.2.
- Job limit 6 h; Free plan 2,000 included minutes/month, 5 concurrent macOS jobs, 500 MB artifacts.
- **UNKNOWN-6**: whether macOS still consumes included private-repo minutes at 10x or 1x after the Jan 2026 repricing. Costed both ways; does not change the decision.

**Rationale.**
1. **It does the whole chain.** Build, test, archive, sign, TestFlight upload — an ordinary iOS CI pipeline, not an experiment.
2. **Cost.** Our bring-up is ~150 macOS minutes. That fits inside the 2,000-minute Free allowance under **either** multiplier reading, so a **private** repo is free for our volume. Worst case (allowance exhausted) is ~$9.30. Scaleway is ~EUR 5.28 and carries a standing billing liability.
3. **No card required to start**, and **no persistent resource to forget**. Scaleway bills while the Mac is *assigned*, stopping does not help, and deletion is impossible for the first 24 h.
4. **It improves DEC-015 rather than replacing its intent.** Build-and-test needs no signing at all, so the project can be proven to compile **for $0 before any $99 is committed** — better than the original plan, which still needed a EUR 2.64 block for that check.

**PRIVATE, not public — and the cost argument is why.** Publishing would expose the Product Constitution, the competitor and pricing analysis, the $39 price and the three positioning arms, the landing-page copy before it launches, and every decision and open unknown. The free-minutes argument for going public **evaporates** once you notice 150 minutes fits inside the free private allowance anyway. If minutes ever run out, pay the few dollars — do not pay in strategy for a discount we already have. (If the harness itself should later be open-sourced for credibility, split it into its own repo; it contains no strategy.)

**What this does NOT change.**
- **The $99 Apple Developer Program is still required** for signing and TestFlight. No CI avoids it.
- **A CI runner cannot have an iPhone attached** either. Delivery to the 5-device fleet is still TestFlight.
- iPhone 7 remains excluded (DEC-008).

**Where Scaleway is genuinely better, stated fairly.** Interactive debugging of never-compiled code: a VNC desktop shows every error at once and rebuilds in seconds, where CI costs a ~5-minute round trip per iteration. Estimated cost of that difference for our ~1,400-line harness: **6-10 iterations, 45-80 minutes of mostly waiting**, mitigated by batching fixes from a full diagnostic log. That is a smaller cost than a paid account, a card, a 24-hour minimum lease and a standing "did I delete it?" liability — and every build after the first is where CI wins permanently.

**Delivered with this decision.** `.github/workflows/ios-build.yml` (unsigned build+test, **no secrets, no Apple account**), `.github/workflows/ios-testflight.yml` (manual dispatch, archive/sign/upload), and `20_TIER0/harness/project.yml` (XcodeGen spec, replacing the hand-built-in-Xcode step).

**New Owner action required.** Create a **private** GitHub repository and push. This also closes the standing MAINTENANCE item — the repo is currently local-only, which is a real single-point-of-failure for E-06 cross-machine recovery.

**Status.** ACTIVE. Evidence: `20_TIER0/T0A_CI_ENVIRONMENT_EVALUATION.md`.

---

### DEC-017 · 2026-08-22 · The home is the Visual Library entry point, not an AI work-report dashboard
**Decision (Owner directive).**
> 这版方向基本正确，但请不要把首页理解成"AI 工作报告 Dashboard"。它首先必须是用户以后替代 Apple Photos 的 Visual Library 主入口，其次才显示 AI 替用户完成了多少工作。ORGANIZED 区域不是几个 Smart Collections，而是稳定、可预测、可以继续下钻到二级/三级目录的 Library Taxonomy。首次全库整理完成后，用户应当同时获得两个即时价值：① 一个已经整理好的、可以直接浏览的视觉图书馆；② 一份系统已经替他完成大量管理工作的结果。

**What was wrong with the previous mock.** The Work-Done Ledger gave the AI work report the whole screen and reduced ORGANIZED to six flat count tiles — which is structurally the same thing as Lucent's smart collections, the exact failure PF-06 exists to prevent. Flat counts do not let a user form a spatial memory, and a user who cannot predict where a thing lives has a tool, not a destination.

**What changed.**
1. **The first-run result compresses into a three-line header** — *N analysed · N organised or handled · Only 23 need your attention* — and the **library takes the prime real estate** below it. Work report moves below the library.
2. **ORGANIZED becomes a real taxonomy with drill-down**, 11 top-level entries per Constitution §23, three levels deep where it matters: `Documents › Identity › Passports`, `Screenshots › Temporary › Pickup Codes`, `Places › Japan › Tokyo`.
3. **Cross-listing is shown, not hidden.** Receipts carries an "also in Purchases › Receipts" tag. This makes Constitution §3 visible — one asset, many entries, no duplicated originals — and it is a differentiator, not an inconsistency to paper over.
4. The T0-D ledger variants are now variants of **this same home**, not of a standalone dashboard. V4 (review-first) becomes sharper: it puts "23 need you" *above the library* rather than below, which is precisely the service-versus-homework manipulation.

**Scope boundary, stated so this does not drift into Tier 1.** What is built is a **navigational skeleton**, hand-authored for the test library. It is **not** the Tier 1-A Visual Asset Taxonomy — no classification rules, no confusion matrix, no risk/lifecycle defaults. Same principle as limitation L-1: T0-B tests whether the STRUCTURE works for users, not whether a classifier can produce it. Building the classifier now would violate the Execution Index (DEC-003, P-01).

**Open question raised by the tree — OPEN-1: a `Documents › Medical` category.** Constitution §16 forbids unrequested inference about health. Filing a photo the user deliberately took of a medical document is arguably categorisation of explicit content rather than inference — but it is sensitive enough to need an explicit ruling rather than a silent default. **Rendered in the prototype as "pending decision" and excluded from any task.** Owner decision required before the study runs.

**Superseded.** `build_ledger_variants.py` and its `ledger/` output are removed — `build_prototype.py` generates the ledger variants as part of the home. Two competing generators sitting side by side is exactly the duplicate-canonical-artifact hazard the documentation audit exists to prevent.

**Impact.** 82-page clickable prototype at `20_TIER0/study_assets/prototype/`. T0-B protocol §3/§7 updated: the predictability question now tests **path depth**, not just top-level placement.
**Status.** ACTIVE.
