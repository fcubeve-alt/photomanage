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

---

### DEC-018 · 2026-08-22 · Repository live on GitHub; first CI build GREEN; UNKNOWN-6 resolved at zero cost
**Outcome.** `github.com/fcubeve-alt/photomanage` — **PRIVATE**, 170 files, 14 commits, both workflows registered. First `ios-build.yml` run **succeeded**.

**The build result.** ~1,400 lines of Swift, written blind on Windows with no Mac and no Xcode, produced **exactly one compile error**: a no-op self-assignment in `BackgroundIndexing.swift`. Fixed in one round. Second run green in **48 seconds**.

**UNKNOWN-6 resolved.** The Actions timing API reports `billable.MACOS.total_ms = 0` for the run — **on a PRIVATE repository**. The macOS minutes are covered by the included allowance. This settles the question DEC-016 costed both ways: **private costs nothing at our volume**, so the argument for making the repo public to obtain free minutes is now closed on evidence, not estimate. Strategy stays unpublished.

**Two blockers were discovered and fixed en route — both are environment facts worth keeping.**
1. **`credential.helper = manager` was configured but Git Credential Manager was never installed.** Git failed with exit 128 and *completely empty stderr*, which is close to undiagnosable if you are not looking for it. Overridden locally to `!gh auth git-credential`.
2. **git 2.9.0 (2016) cannot negotiate TLS with GitHub at all.** `ls-remote` failed with exit 128 and no message; forcing `http.sslVersion=tlsv1.2` and disabling `sslVerify` both changed nothing. `gh` worked throughout because it carries its own modern HTTP stack — which is what isolated the fault to git. Fixed by installing **MinGit 2.55.0.5** (official git-for-windows zip, no installer) to `C:\Users\admin\tools\git`.

**Tooling installed** (both official releases, extracted locally, no admin, no system changes):
- `C:\Users\admin\tools\bin\gh.exe` — GitHub CLI 2.98.0
- `C:\Users\admin\tools\git\cmd\git.exe` — MinGit 2.55.0.5

⚠️ **The system default `git` is still the broken 2.9.0.** Any session that runs `git` without prefixing the new path will hit the same silent exit-128. See `SESSION_HANDOFF.md`.

**DEC-015 condition is now MET.** The rule was: pay the $99 only after a successful compile. The compile is green, at $0, with no Mac and no Apple account. **HG-1 is now the Owner's move.**

**Status.** ACTIVE. Evidence: run 32579093228, and `20_TIER0/T0A_CI_ENVIRONMENT_EVALUATION.md`.

---

### DEC-019 · 2026-08-22 · One canonical taxonomy; prototype driven by the real manifest
**Decision.** `20_TIER0/study_assets/taxonomy.py` becomes the single source of truth for the browse tree. Both `generate_test_library.py` (which assigns every asset its index entries) and `build_prototype.py` (which builds the tree and rolls up counts) import it. The prototype now renders **real assets from `library/manifest.json`** — nothing on screen is hand-written.

**Why this mattered more than it looked.** The prototype had invented counts and coloured rectangles at the leaves. A facilitator **could not have completed a single task inside it**, and we would have discovered that with a participant sitting in the room. The build now **fails loudly** if any task answer is unreachable, and prints the reachability table on every run. All 8 targets verified clickable.

**Three fidelity bugs surfaced the moment real counts replaced invented ones** — each would have damaged the study:
1. **Clothing = 0, Work = 0.** Two of the eleven §23 entries were empty. A participant tapping an empty top-level category discredits the whole prototype.
2. **Travel = 22.** §11 says trips form automatically from time + place and the user never builds a travel album. They were not being derived.
3. **Timeline = 9,864, not 10,000.** Foreground assets had no time index at all.

**Fixed by multi-indexing, not by adding content.** A clothing photo *is* a person/photography asset that is **also** indexed under Clothing; a work screenshot *is* a screenshot also indexed under Work; Tokyo photos inside the trip window join the derived Travel view. This is exactly what §3 describes — one stored asset, many entries — and it leaves the §5 composition untouched: re-verified **within 0.3pp on all eight content classes**.

**Result:** 10,000 assets, **21,790 index entries (2.18 per asset)**, all 11 top-level entries populated, Timeline complete at 10,000. Cross-listing verified genuinely shared rather than duplicated: `Documents > Receipts` and `Purchases > Receipts` resolve to the **same 6 asset ids**.

**Guard added.** The generator now validates every emitted path against `taxonomy.py` and aborts on any path the browse tree does not contain. Taxonomy and library cannot silently drift apart again.

**Also noted:** Constitution §23 has **no generic "Photography" bucket**. Ordinary photos are not a category — they are reached through Places and Timeline. That is the taxonomy being faithful, not an omission, and the generator now reflects it.

**Status.** ACTIVE.

---

### DEC-020 · 2026-08-23 · `Documents > Medical` approved — explicit medical DOCUMENTS only, never health-state inference
**Decision (Owner ruling on OPEN-1).** The category is approved, bounded:

| | |
|---|---|
| **ALLOWED** | Classifying an explicit medical **document** the user photographed — a prescription, a test result, an appointment letter |
| **FORBIDDEN** | Inferring health **state** from it: conditions, diagnoses, medications, treatment, severity, or any derived signal about the person |

**The category describes the piece of paper. It never characterises the human.**

**Why this needed teeth rather than a note.** Those two things are one careless model call apart. A classifier that can read "prescription" off a photo is already most of the way to storing what the prescription is for, and nothing about the architecture would stop that from happening quietly. So the boundary is written as a rule with an enforcement hook, not as a comment: **`OPERATING_RULES.md` P-08** requires any future classifier touching this category to be explicitly reviewed against it. Also recorded at the definition site in `taxonomy.py` and in the §16 row of `CONSTITUTION_UNDERSTANDING.md`.

**Risk default.** Medical documents are R5-class (§6) and default to **Protect** — no auto-delete, ever.

**Study impact.** T0-B limitation **L-5 retired**. The category is populated (130 assets) and browsable like any other. It is deliberately **not** made a task target: there is no question the existing seven tasks do not already answer, and asking a stranger to hunt for medical paperwork buys nothing.

**Caught while implementing:** `Documents > Warranty` displayed 0 while carrying an "also in Purchases > Warranty" tag — a cross-listed node whose twin is empty reads as broken. The warranty asset was only indexed on the Purchases side. Fixed; both cross-listed pairs now verified to resolve to the **same asset ids**, not copies.

**Status.** ACTIVE. OPEN-1 CLOSED.

---

### DEC-021 · 2026-08-23 · Sample size raised to n=15 — the thresholds and n=10 were mutually inconsistent
**Found while self-testing the study analyzer, before a single participant was recruited.**

Wilson 95% confidence intervals at **n = 10**, against the pre-registered 70% threshold:

| Observed | Rate | 95% CI | Clears 70%? |
|---|---|---|---|
| 8/10 | 80% | 49–94% | **no** |
| 9/10 | 90% | 60–98% | **no** |
| 10/10 | 100% | 72–100% | yes |

**At n = 10 the only result that can statistically clear a 70% threshold is a unanimous one.** We had pre-registered a threshold the pre-registered sample size could not reach except by a perfect score. Both numbers were set in good faith and neither was checked against the other.

Smallest n that resolves P-1, by the effect size that actually appears:

| Observed rate | n required |
|---|---|
| 100% | 10 |
| 90% | **15** |
| 80% | **77** |

**Decision: n ≥ 15**, with the reporting rule fixed in advance so it cannot be negotiated afterwards:
- **≥ 90%** → resolved at n=15. Report PASS.
- **70–89%** → **directionally positive but NOT statistically resolved.** Report the estimate with its CI and say so. **Do not report PASS.** Resolving it needs ~75 participants, which is a separate decision about whether that certainty is worth the recruiting cost.
- **< 70%** → FAIL. A clearly low result is informative even at n=15.

**Why this is worth five extra participants.** Discovering *after* fifteen sessions that no attainable result could have supported the claim would have wasted the entire study and the recruiting effort behind it. Five more people is cheap by comparison.

**This does not weaken the study — it states what it is.** A small-sample usability test detects **large** effects reliably and cannot adjudicate **small** ones. Tier 0 is looking for a large effect: if the organised-library entry point only wins by a few points, that is not the differentiation the Constitution claims anyway.

**Propagated to:** both protocols (§8.1 with the power table), both scoring sheets, the facilitator rota (extended to P15, balance checked: 8/7 arm order, V1×4 V2×4 V3×4 V4×3), and `analyze_studies.py` (`MIN_N = 15`, which now stamps any smaller sample UNDERPOWERED and forbids a PASS).

**Status.** ACTIVE.

---

### DEC-022 · 2026-08-23 · Cold-Start Recovery Test implemented and wired into CI
**Closes the last unchecked item on the Playbook §5 Bootstrap Checklist:** *做一次 Cold-Start Recovery Test：假设换了新模型/新 Session，验证能否不靠 Owner 解释继续。*

**Asserting that recovery works is worth nothing**, so it is checked mechanically by `recovery_check.py` and re-run automatically in CI whenever any `.md` changes. Recovery rots silently — documents drift, a file keeps claiming something that stopped being true, a referenced path gets renamed — and none of that is visible until a fresh session actually needs to recover and cannot.

**What it verifies:** all 11 canonical state files exist · handoff coordinates match *reality* (live git remote, branch, working-tree state) rather than what someone wrote down days ago · every backtick file reference in the handoff chain resolves · the **seven questions** a session with no conversation history must answer are actually answerable from the documented reading order · no stale claims (the classic being "no remote" after one exists) · the gate document still states plainly that it is unfilled.

**Result: 29 checks, 0 FAIL, 2 WARN — RECOVERY VIABLE.** All 25 file references resolve.

**Two flaws found in the checker itself, both worth recording because they are the failure mode of checkers generally:**

1. **It cried wolf.** Two files were reported missing that plainly existed; the resolver guessed at candidate directories instead of indexing the tree. A checker that produces false alarms gets ignored, which is worse than not having one. Replaced with a real filename index.
2. **It reported a vacuous check as green.** "All 0 internal links resolve" looked like a pass but there are *zero* markdown links in the state files — they reference files with backticks instead. An empty check reporting OK is actively misleading, so it now reports N/A and names the backtick check as the one that matters.

Both were bugs in the instrument, not the project. That distinction is the point of running the instrument before trusting it.

**Standing rule:** `recovery_check.py --strict` must stay green. A FAIL means a fresh session would have to ask the Owner something, or would rediscover something already solved — which is precisely the cost E-04/E-05 exist to prevent.

**Status.** ACTIVE.

---

### DEC-023 · 2026-08-23 · MASTER_PLAN and MISSION_SPEC recalibrated; two governance defects fixed
Both files were written on the first morning and had not been revisited across DEC-008 … DEC-022. `recovery_check.py` verifies that references *resolve*; it could not see a document that resolves perfectly while saying something untrue. Reading them found two real defects.

**Defect 1 — `MASTER_PLAN` contradicted itself.** The header said *"M1 complete → M2 in progress"* while the M1 section said IN PROGRESS. **A cold session reading the top line would have concluded Tier 0 was finished and Tier 1 had started** — the single most damaging thing that file could get wrong. Rewritten: `M0 complete · M1 (Tier 0) IN PROGRESS · zero measurements taken`, with the workstream table rebuilt around the real gates, T0-D added, and the stale "Windows-side preparation" list replaced by what actually exists.

**Defect 2 — `HG-5` was defined twice**, as *"irreversible or high-risk operations"* and as *"create a private GitHub repository"*. I introduced the collision myself when adding the repo gate. **"HG-5 is blocking" was ambiguous**, which is worse than having no identifier. The repo gate is done and removed; HG-5 keeps only its original meaning. The gate table was also corrected for DEC-016 (the cloud-Mac spend was withdrawn) and DEC-021 (n ≥ 15), and `HG-2a`/`HG-2b` in `PROJECT_STATE` were collapsed to `HG-2` so the two files use one vocabulary.

**Three new semantic-staleness checks** added to `recovery_check.py`, because both defects survived a 0-FAIL run: milestone agreement between the two files, Human Gate id uniqueness, and every gate referenced in `PROJECT_STATE` being defined in `MISSION_SPEC`.

**The checks themselves then failed their own negative control** — see `FAILURE_PATTERNS.md` **PF-09**. The milestone check used a substring test that matched both "M1 in progress" and "M1 complete", so it reported agreement while the contradiction was live. Now verified by deliberately breaking the file and confirming it goes red.

**Standing rule added:** every new check gets a negative control before it is trusted. If it cannot be made to fail on demand, it is decoration.

**Status.** ACTIVE.

---

### DEC-024 · 2026-08-24 · Information-Change-First / Minimum Necessary Inference incorporated as L1-B
**Owner supplied** `PVME_Information_Change_First_Methodology_Update_v1.0.docx` with the instruction: incorporate as long-term architectural methodology, **do not restart, rewrite or interrupt the current P0 / Tier 0 execution**, review current work for conflicts, record required future changes, continue the existing order.

**Registered at authority level L1-B** — binds all architecture and model decisions, sits below Constitution v1.3 on product truth. The source states explicitly that it changes no product goal, no taxonomy, no risk grading, no lifecycle, no retrieval path, and not the Tier 0 execution order. Where it appeared to conflict with L1, L1 would win; no such conflict was found.

**Two principles, now `OPERATING_RULES.md` P-09 and P-10:**
- **MNI** — `Cheap Signals → Candidate Reduction → Selective Intelligence → Structured Memory`. Handing every asset to a heavy model is wrong *by construction*, not merely slow. The architecture never bends to accommodate a model.
- **ICF** — *what changed / what is actually new / does it deserve deeper inference* before any expensive inference. Video may never default to frame-sampling with a full model per frame; it produces a **Video Memory Record** into the same Unified Visual Memory Graph.

**P-04 restated:** the question is the *minimum* capability required for the task, not the *maximum* available. Rules/metadata → no AI; light model → no large model; Apple Native → no added model. LocateAnything, Mage and Gemma stay Candidate/Benchmark and are not product dependencies.

**Conflict review — checked against the code, not from memory.** Much of the existing work was already compliant before the methodology arrived: the Tier 0 scope lock to Layers 1–2, **C-1 gated OCR**, C-2 thumbnails-only, the Apple-native zero-model embedding, and `LibraryChangeTracker` — which is Information-Change-First implemented at the index layer in everything but name.

**Two violations marked, neither fixed** (§7: review and mark; do not refactor working results without reason):
- **MNI-1** — `dHash` is computed, stored *and indexed*, and never queried. We pay for the cheap signal that would authorise skipping, then discard it and run gated OCR plus an embedding on every asset including exact re-downloads. **This matters for the kill test:** §5 says the harness must measure the intended design rather than a naive baseline, and as written it measures the naive one, so **A1 is pessimistic and could fail a budget the intended architecture meets.** Recorded as **FC-1** and recommended before the device campaign — no data exists yet to invalidate — but left as an **Owner decision** rather than done unilaterally.
- **MNI-2** — the harness and test corpus are **photos only**. Real 100k libraries contain substantial video, and video is precisely where naive per-frame processing explodes. **An A1 PASS is therefore an optimistic bound for a mixed library.** Building video handling now would be Tier 1/2 work and is forbidden, so this is **FC-2**: stated as an explicit limitation in the T0-A spec and carried into `TIER0_GO_NO_GO.md`.

**Seven required future changes registered (FC-1 … FC-7)**, scoped to the tier that owns each — including the Video Memory Record pipeline (Tier 2), video in the Tier 1 corpus, re-scoping T1-A/T2-E around candidate reduction rather than whole-library classification, and making Candidate Reduction an explicit stage alongside Constitution §25.

**Nothing was stopped, reversed or redone. No Tier 1/Tier 2 development was started. The T0-A/B/C/D order is unchanged.**

**Status.** ACTIVE.

---

### DEC-025 · 2026-09-06 · Machine migration: environment pinned in code, not in the handoff
**Context.** The project moved from `D:\photomanage` on the previous computer to
`D:\Documents\GitHub\photomanage` on a new one. Session 002 opened cold, with the repo
and the state files as the only inputs. `recovery_check.py` reported **33 checks,
0 FAIL, RECOVERY VIABLE** — the E-06 / M0 acceptance criterion held in the real event
it was written for, not in rehearsal.

**What the recovery test could not see.** It verifies that documents agree and that
referenced files exist. It does not execute anything. So it passed while **both Tier 0
analyzers were broken on this machine** — see `FAILURE_PATTERNS.md` **PF-10**. The new
machine has a Chinese locale, `sys.stdout` defaults to cp936, and the report glyphs
(`⚠️`, `✅`) cannot be encoded in it. Each analyzer ran the full analysis and then died
on `print`. These are the tools that will meet the T0-A CSV and the T0-B/T0-D session
data exactly once.

**Decided.**
1. **The console locale is not an input.** All seven Python entry points pin
   `sys.stdout`/`sys.stderr` to UTF-8 at start-up. Rejected alternative: stripping the
   glyphs from the reports — that lets the environment dictate the deliverable, and
   `⚠️ Projected, not measured` is load-bearing (PF-01).
2. **New standing check — `.github/workflows/tools-check.yml`**, on every `.py` change:
   the analyzer self-tests, the same self-tests under `PYTHONIOENCODING=gbk`, generator
   determinism, and test-library manifest reproducibility. Both new checks were given a
   negative control per DEC-023/PF-09 — the pre-fix code exits 1 under the gbk step,
   and a manifest with one altered field is rejected.
3. **Two claims re-verified rather than inherited.** Generator determinism now proves
   itself: `build_prototype.py` and `build_landing.py` rebuild byte-identical output,
   and the test-library manifest reproduces from SEED 20260822 in every field except
   its wall-clock stamp (10,000 assets, 136 foreground). The `--manifest-only` path
   still validates every asset path against `taxonomy.py`.
4. **`PROJECT_STATE` coordinates rewritten for this machine.** The DEC-018 git trap —
   system git 2.9.0 unable to reach GitHub, requiring a `C:\Users\admin\tools` PATH
   prefix — **does not exist here**: git is 2.50.0 and works unprefixed. That warning
   was the loudest text in `SESSION_HANDOFF.md` and it now describes a machine that is
   gone; leaving it would send the next session chasing a fault that is not there. It
   is demoted to a historical note under DEC-018. **`gh` is not installed on this
   machine** — a real new gap, since HG-1 and the CI workflows are driven through it.
5. **`PROJECT_STATE`'s "Doing now" list was stale and is corrected.** It listed the
   landing pages, the manifest-wired prototype and the analyzers as build-ahead work
   still to do. All three were finished in commits `9502cbc`, `5af1e4a` and `32382ea`,
   and `MASTER_PLAN` already said so. A cold session would have rebuilt finished work —
   the F-06 failure, reached through a stale file rather than a missing one.

**Not done, deliberately.** No Tier 1/Tier 2 work, no scope change, no re-derivation of
any finding, and **FC-1 (MNI-1) remains an open Owner decision** — it is still the one
substantive engineering change recommended before the device campaign.

**Status.** ACTIVE.

---

### DEC-026 · 2026-09-06 · Owner cancels T0-C and T0-D; the product is a GO
**Owner instruction, verbatim in substance:** *"C、D 测试不用做了，我们有结论了。这个 app 一定要做。"*

**Recorded as an Owner WHAT decision (E-02).** The Owner defines what gets built and
what evidence is worth buying. This is not a technical finding and is not presented as
one.

**What is cancelled.**
- **T0-C2** — the three landing pages, the traffic buy and the fake-door payment test.
  **HG-2 is closed**: the domain (~$12) and the ~$500–700 ad spend will not happen.
  The built pages stay in the repo unpublished; they cost nothing to keep and would
  cost real time to rebuild.
- **T0-D** — the Autonomous Management Value Proposition study. The protocol, the four
  ledger variants, the scoring sheet and the analyzer stay in the repo.
- Neither deliverable will be written. The gate cannot be completed as originally
  specified, and that is a consequence of the decision, not a defect to paper over.

**Concern registered once, then the decision stands.**
- **Cancelling C costs little.** The gate logic already said a C failure triggers a
  commercial-model pivot, never a kill (DEC-002). T0-C1 is complete and gives the
  market picture; C2 would only have priced it. Skipping it defers a pricing question,
  not a survival one.
- **Cancelling D is the one with a real cost.** Constitution §7 requires the
  automation-tolerance bet — *will users let the system act on their library, not just
  search it* — to be validated by real users rather than assumed by the people building
  it. DEC-014 added D precisely because Tier 0 contained no such test. Cancelling does
  not answer that question; it moves it to beta, where the same finding costs a rebuild
  instead of a protocol. **Recorded as an accepted, named risk carried into M4, not as
  a closed question.**
- The Owner was told this and reaffirmed. Proceeding.

**What does NOT change: T0-A.**
A is not a market question, it is a physics question — whether an iPhone can index a
100k-asset library without thermal death, memory kill or an unrecoverable background
loss. Deciding to build the product does not decide that, and if A fails the product
has to change shape regardless of how much anyone wants it. **A is now the only
remaining Tier 0 kill test** and moves to the top of the queue.

**OPEN-2 — awaiting Owner ruling: does T0-B survive?**
B asks whether users prefer this over Apple Photos as the place they go to find things.
With the build decision made, B stops being a kill test and becomes design research; it
could run against a beta instead of a prototype. Not decided unilaterally. Until the
Owner rules, T0-B materials are frozen, not deleted, and no further sourcing effort is
spent on the 136 foreground images.

**Consequences to carry.** `MASTER_PLAN` M1, `MISSION_SPEC` success criteria and
`20_TIER0/TIER0_GO_NO_GO.md` were all written around a four-workstream gate and now
describe a programme that will not run. They are corrected here for A/C/D; the B-shaped
hole is left explicitly marked as OPEN-2 rather than guessed at, so the next session
finds a stated gap instead of a confident fiction.

**Status.** ACTIVE.

---

### DEC-027 · 2026-09-06 · OPEN-2 closed — T0-B stays. HG-1 blocked on a payment instrument, not on willingness
**Owner ruling on OPEN-2:** *"B 不用撤了，没有意义，还要做的就不撤了。"* — **T0-B survives.**
It is no longer a kill test (the build decision is made, DEC-026) but it remains work
the Owner wants done. Its materials come out of freeze. The 136 foreground images go
back onto the ungated work queue.

**HG-1 — the blocker is a payment instrument, not the $99.** The Owner has confirmed
the fee will be paid and cannot pay it today: the Apple Developer Program enrolment
does not accept the payment method available to them. Apple Pay works for their iCloud
subscription; it is not accepted for the enrolment fee. The Owner is arranging this
themselves.

**Consequence, stated plainly so no later session misreads the queue:** T0-A's device
measurement is blocked for an unknown duration. Per S-03 that blocks **T0-A only**. It
does not block T0-B, FC-1, or anything else. It also means **the $0 simulator work done
on 2026-09-06 is worth more than it looked** — it is currently the only thing
advancing T0-A at all.

**A correction the Owner was right to demand.** The Owner asked whether the project was
"finished", having read a run of green results. It is not, and the state files were
letting that impression form: they describe instrumentation in detail and say
comparatively little about how much of the *product* does not exist. **Nothing of the
product is built. The classifier, the taxonomy engine, the entity resolver, the
lifecycle engine and the risk policy engine are all Tier 1/Tier 2, all still LOCKED,
and all at zero lines of code.** `README.md` now says this on its first screen rather
than implying it. Recorded as **PF-11**.

**Status.** ACTIVE.

---

### DEC-028 · 2026-09-06 · Owner directs the classification engine to be built now, whatever T0-A says
**Owner instruction, verbatim in substance:** run T0-A once so we have a number, ignore
what the documents have locked, and then build the real classification program —
*"无论这个测试过不过，我都要做"*. B, C and D are not to be touched. Highest authority.

**What was locked, and is now overridden.** `MISSION_SPEC` OUT OF SCOPE listed the
Visual Asset Taxonomy, Multi-Signal Classification and the Risk Policy Engine as Tier 1
/ Tier 2. `MASTER_PLAN` M2/M3/M4 are marked LOCKED, and the Execution Index rule is one
tier at a time. The Owner has lifted that sequencing for the classifier specifically.
Recorded here rather than silently — a rule that gets ignored without a record stops
being a rule for everything else too.

**The Owner's reasoning, which is sound.** The Tier 0 gate exists to stop the project
building something physics forbids. The Owner has already decided to build (DEC-026),
HG-1 blocks the device measurement for an unknown duration (DEC-027), and T0-A's own
kill question is about *library size*, not about whether classification works. A1
failing degrades scope to "recent N months" — it does not make a classifier pointless.
So the classifier is not downstream of A in the way the tier ordering assumed.

**A stated by the Owner and confirmed by measurement:** 100k assets is far above what
most libraries hold. The measured ceiling (`20_TIER0/evidence/T0A_SCALE_SIMULATOR_2026-09-06.md`)
puts ~50k inside both budgets on the optimistic ceiling and ~10k–26k inside the
90-minute foreground budget on the predicted device band. Designing for 10k–50k rather
than for 100k is consistent with the data.

**What was built.** `30_ENGINE/` — signal contract, escalating classifier, R0–R6 risk
policy, duplicate and same-entity handling, SQLite catalogue with checkpoint/resume and
incremental update, CLI, 55 behavioural tests, and an evaluation harness run against
the 10,000-asset labelled library. Root-level macro F1 **0.998**, leaf exact **99.8%**
where the label is derivable, **0** wrong roots, all four safety red lines audited
against the written catalogue rather than asserted from the code.

**Three things kept honest rather than flattered:**

1. **4,155 of the 10,000 labels are coin flips.** `generate_test_library.py` assigns
   filler assets a leaf with `random.choice`, and no signal on the asset records which
   one it picked. Those are counted and **not scored**; scoring them would report the
   generator's randomness as classifier error permanently, however good the classifier
   became. The corpus was built for T0-B retrieval navigation, not for classifier
   evaluation, and it is used only for what it can actually answer.
2. **The corpus carries no provenance and no scene labels**, so `Downloads`, `Objects`
   and `Clothing` are unreachable in evaluation. Their rules exist and are unit-tested
   from explicit signals. Faking either from the label would have measured the adapter.
3. **The adapter refuses to read ground truth.** `_Row` raises on `category`,
   `category_path`, `paths`, `same_entity_group`, `source_query` and the rest. A leak
   crashes the run instead of producing a perfect score.

**A real defect the work exposed, worth more than the score.** With the location rule
running before the text tier, a GPS fix filed every photographed document as
`Places > … > London` at 0.91 confidence; the escalation policy saw a settled answer and
the OCR pass that would have recognised the passport never ran. **Nine of nine identity
documents lost, silently, each with a plausible wrong answer in its place.** Location is
context, not identity. Locked into `LocationIsContextNotIdentity` in the test suite.

**A corpus defect found on the way.** Assets A00126–A00132 carry `place: "home"` — which
the manifest's own table resolves to London, 51.5074/-0.1278 — while their labelled path
is `Places > United Kingdom > Brighton`. The coordinates and the label disagree. That
matters to **T0-B**, not just here: a facilitator task that asks a participant to find
those beach photos by location is not answerable from the asset's own data. Left as a
finding for whoever next touches the test library; not silently patched.

**Status.** ACTIVE.

---

### DEC-029 · 2026-09-06 · Paced ingestion and change-driven processing — A1 becomes a scheduling constraint, A3 becomes the whole kill test
**Two Owner rulings, both accepted, both built. One correction to each.**

---

**Ruling 1 — a large library is paced, not raced.** A new user with 100k photos does
not have to wait for one long run. Do a coarse pass first, then a set amount per day,
tell them what is happening, offer choices, and stand down when they pick the phone up.
*"没有必要就是你装系统…这半个小时…我一定把你搞完，没有的，这是一个很人性化的"*.

**The data supports it and offers something better than the version proposed.** Breadth
is nearly free; depth is what costs. A breadth pass reads PhotoKit metadata only — date,
GPS, media subtype — and decodes **no pixels**: 0.18–0.28 ms/asset measured, and 0.17
ms/asset in a real run of the engine over the 10,000-asset library. **A 100k library
gets Timeline, Places, Travel and Screenshots in under 30 seconds**, not in a day. Depth
(OCR, embedding, faces) is 105–154 ms/asset — three orders of magnitude more — and that
is the part worth pacing. So the user is never told "wait N days for your library". They
are told "your library is here in a minute, and it gets deeper while you use the phone".
Built as `30_ENGINE/pvm/schedule.py` and `pvm plan`.

**THE CORRECTION, and it must not be lost in the agreement: pacing makes A3 MORE
critical, not less.** A3 is not "indexing is slow"; it is *the system kills the task and
the index cannot resume — progress is lost*. A ninety-minute run that loses its place
costs ninety minutes. **A twenty-two-day plan that loses its place is a product that
never finishes.** And `BGProcessingTask` is granted at the system's discretion and
withdrawn from apps that misbehave — "2,000 a day" is a request, not a schedule. A4
(incrementality) rises with it, because a paced first run overlaps with new photos
arriving, so the engine must ingest new assets while still working through old ones.

**Recorded consequence for the Tier 0 gate.** By this ruling **A1 is no longer a kill
question** — it is a scheduling constraint with a known cost per asset, and a library
too large for one run is paced rather than refused. **A3 is now the entire kill test**,
and A4 is promoted alongside it. This does not lower the bar; it moves all of it onto
the two claims that were always the ones a device has to answer.

---

**Ruling 2 — do not analyse every frame; analyse what changed.** *"第一帧和第二帧…如果
基本上没什么变化…我们只对那种有变化的地方进行处理"*. This is L1-B applied to time, and
it is FC-1 generalised from duplicate stills to sequences. Accepted.

**THE CORRECTION, because the rule as stated silently destroys content.** "Compare each
frame with the one before it, skip if similar" fails on a slow pan: every adjacent pair
is similar, so nothing is ever processed, while the start and end of the sequence are
different scenes. Measured on a 600-frame synthetic pan: the pairwise rule processes
**1 frame of 600**, and frames 0 and 599 differ by **41 of 64 hash bits** — an entire
scene never looked at, with no error and no symptom.

Every comparison is therefore against the **last frame actually processed** — the
current keyframe — never against the immediately preceding frame. Drift then accumulates
until it crosses a threshold and opens a new keyframe. On the same 600-frame pan that
processes 76 frames and still saves **80%** of the work.

**Measured savings** (cost model built from the measured per-stage numbers, so the
arithmetic is real even though the sequences are synthetic): static shot **88%**, slow
pan **80%**, cuts every 60 frames **79%**, handheld motion **61%**. Every frame still
pays decode and hash — the gate's own cost is counted, not hidden.

**Three guards, each one a way this loses data if left off**, all tested:
1. **FC-1a** — `dHash` returns 0 both for a class of ordinary images and for every hash
   failure, so a failure is indistinguishable from a perfect match, and a perfect match
   is exactly what licenses a skip. An unusable hash always processes.
2. **Documents** — contract page 1 and page 2 are visually near-identical and
   semantically unrelated. Visual similarity may never skip text extraction.
3. **First and last frame** always processed; plus a hard cap of 30 consecutive skips,
   for drift slower than the threshold forever.

Built as `30_ENGINE/pvm/deltas.py`, 15 tests including the pairwise-failure demonstration.

**OPEN-3, stated rather than assumed:** these decisions are measured on synthetic hash
sequences. Whether `dHash` separates scenes as cleanly on **real video frames** — motion
blur, exposure shifts, compression artefacts — is unverified, and it is the assumption
the whole saving rests on. It needs real footage, not a device, so it is not blocked by
HG-1.

**Status.** ACTIVE.

---

### DEC-030 · 2026-09-06 · Constraint audit after PF-12 — the specification becomes a CI check
**Owner challenge:** *"这些设计思想，都已经在文档中体现了，为何还要我这么碎片化的"* — why is the Owner having to feed back, piecemeal, requirements that the documents already contain?

**They were right.** Both design instructions given during DEC-029 were already binding: L1 §24 Gate 3 mandates Progressive Indexing and names TTFUV a P0 metric; L1 §24 Gate 1 mandates 分块/分时 + checkpoint + 增量处理 + 后台机会执行; L1-B §4 forbids the naive every-N-frames video pipeline. I had not read L1 or L1-B while building the engine, and reported their requirements back as findings. **PF-12.**

**The audit found more than the two clauses the Owner named.** Full result in `30_ENGINE/CONSTRAINTS.md`: **34 binding clauses — 21 DONE, 6 PARTIAL, 4 MISSING, 2 out of scope.**

The four MISSING, now named rather than absent:
- **B4-RECORD** — L1-B §4 requires a **Video Memory Record** (Date / Place / Person / Object / Event / relevant segment / representative frames) into the Unified Visual Memory Graph. `deltas.py` selects frames; it does not produce the record. Frame selection was the easy half.
- **S14-PERSONAL** — §14 Personal Policy from the user's Keep/Delete/Protect/Restore corrections. Not built (Tier 2).
- **K-PERSONAL** — Personalization Gain, which depends on the above.
- **Select Best** — §25 Layer 6 lists it among the policy actions; `risk.py::Action` has no such member.

The six PARTIAL are mostly one shape: **Category-Specific Entity Resolution** (§24 Gate 2 / §25 Layer 4 — 证件用 OCR/版式/字段, 合同用文本指纹/页码, 普通照片用时间/地点/视觉相似) and **Lifecycle/importance** (§25 Layer 5), both Tier 1-A.

**The most consequential single finding: the engine was being measured against the wrong things.** §18 names eight KPIs. The evaluation reported F1 and precision — measures I chose. Now fixed: `pvm/kpi.py` computes Automation Ratio, Human Review Burden, Weighted Error Cost, Catastrophic Error Rate, Classification Coverage, Continuous Hygiene Rate and TTFUV, and `eval/evaluate.py` prints them with the statement that **where they disagree with F1, they win**. First measurement on the 10k library: Automation Ratio **94.0%**, Human Review Burden **60 per 1,000**, Catastrophic Error Rate **0**, Coverage **94.0%**, TTFUV **2.8 s** (28 s at 100k).

`kpi.py` also separates **outcome** (priced against labels, evaluation only) from **exposure** (what it would cost if every acting proposal were wrong, the only honest field metric). Reporting exposure as outcome is how a dashboard starts lying.

**The guard, and why it is not a promise.** `check_constraints.py` runs in CI and fails when a quoted clause no longer appears verbatim in the source document it cites, when a clause marked DONE names code that does not exist, or when a PARTIAL/MISSING carries no explanation. Its own self-test proves it catches a paraphrase, a DONE with nothing behind it, a DONE citing a missing symbol, and a silent gap. **A constraint cannot be softened by rewording it into the register, and cannot claim completion on an intention.**

**Also corrected:** `SESSION_HANDOFF.md` listed L1 as optional reading — *"only if you need product-level detail"*. That framing is what let the engine be built without it. Engine work now requires `CONSTRAINTS.md`, which points at the source.

**Status.** ACTIVE.

---

### DEC-031 · 2026-09-06 · Full audit against every authority document, and two defects it found in shipped code
**Owner instruction:** *"一一对照项目内容，看你开发的程序是不是按要求来做。先自主审计一下。到时我再要求外部对你审计。"*

**First, the framing that has to lead.** There is no app. There is a Python engine and
a Swift stopwatch. Every DONE below means a clause is satisfied by code that does not
ship (PF-11).

**Second, an admission about the previous audit.** DEC-030's register covered only the
sections I had happened to read — §12, §13, §14, §18, §24, §25 and L1-B. It missed
twenty sections of the Constitution and all of L2 Tier 1 and Tier 2. That is PF-12
repeated one level up: an audit of the parts I already knew about is not an audit.

**This audit covers L1 §1–26, L1-B, and L2 Tier 0/1/2 in full. 90 clauses:**

| status | count | share |
|---|--:|--:|
| DONE | 36 | 40% |
| PARTIAL | 34 | 38% |
| MISSING | 11 | 12% |
| OUT-OF-SCOPE (tier named) | 6 | 7% |
| NOT-CODE (principle, explained) | 3 | 3% |

**Two defects found in code that was already written and already passing its tests.**

**1 · The risk scale was not the Constitution's.** §6 and Tier 2-A both define
R0 Disposable / R1 Low Value / R2 Normal / R3 Personal / R4 Important / R5 Critical /
R6 Irreplaceable. The engine used the same seven identifiers with meanings I had
invented: **R6 meant "not understood" where the Constitution means "irreplaceable,
highest protection"**, receipts sat one level below their §6 placement and people one
level above. Every row of the catalogue read wrong against the document that defines
it, and no test caught it because the tests asserted my scale.

Rewritten to §6 verbatim, with §5's actual formula — Category × Importance × Lifecycle
× Confidence × Recoverability × Personal Preference — as a generated Policy Table
(a Tier 2-A deliverable). Confidence is no longer a rung on the risk scale: conflating
"we do not know what this is" with a level of consequence is what let an unidentified
asset outrank a passport. Pinned by
`tests/test_engine.py::TheRiskScaleIsTheConstitutionsNotMine`, which compares the enum
to §6 clause by clause.

**2 · Byte identity was gated behind classification confidence.** An exact duplicate
the classifier could not identify went to Review. §6 makes 完全重复下载 the R0 case and
激进自动处理 its default; the evidence for byte identity is a content hash and is
certain whether or not we worked out what the picture shows. So the one action the
system can genuinely automate was the one it refused to take — precisely the trade §7
exists to forbid. Fixed; auto-clean now fires for exact duplicates and for nothing else.

**The eleven MISSING, worst first.** The largest is **S2-REMEMBER / B4-RECORD — the
Visual Memory Graph.** §2 makes "Remember" one of the ten steps the product *is*, and
§15 builds every later service on it. The catalogue files photos; it does not turn them
into evidence about people, objects and events. That is the difference between a filing
system and a memory, and it is architectural rather than a feature. Then:
**Intent Search** and **Relations** — two of the four retrieval paths §10 and §19 define,
both absent; **per-category Entity Resolution** (§24 Gate 2, the Tier 1 make-or-break);
**Select Best**, an action the engine can name and cannot perform; **Personal Policy**
and its KPI; and **risk-grading evaluation**, never measured against labels.

**On the 38% PARTIAL.** That column matters more than the MISSING one. A partial clause
passes its tests and still does not do what the document asks — Time is indexed by year
but not by month, day or moment; Places reaches city but not place; Object and Event
are relation rows rather than indexes. Those read as done in a demo.

**Status.** ACTIVE. `check_constraints.py` verifies all 90 clauses in CI.

## DEC-032 · 2026-09-07 · Money OS 包从工作树移除；历史清除待批准

`90_ARCHIVE/OTHER_PROJECT_MONEY_OS/Project_M_Master_Development_Package_v1.3.1_COMPLETE.zip`
（422 KB）是另一个项目的开发包，M0 引导时随文档一并提交，此后无任何代码或文档读过它。
DEC-005 早已把它封存在范围之外。**仓库现在是公开的**，而它不属于这个项目，所以 Owner
批准移除。

已做：`git rm`，并在原位置留下 README 说明。

**未做，需要 Owner 明确同意才能执行**：它仍在 commit `e62e073` 中，任何人知道该 SHA
仍可从 GitHub 下载。真正清除必须重写历史：

```bash
# 在一个全新的克隆里做，不要在有未推送工作的仓库里做
pip install git-filter-repo
git clone --mirror https://github.com/fcubeve-alt/photomanage.git
cd photomanage.git
git filter-repo --invert-paths   --path '90_ARCHIVE/OTHER_PROJECT_MONEY_OS/Project_M_Master_Development_Package_v1.3.1_COMPLETE.zip'
git push --force --mirror
```

**代价，说清楚再决定**：所有 commit SHA 全部改变；任何已有克隆（包括正在进行的分支）
都必须重新克隆，否则下一次 push 会把旧历史推回去；GitHub 上已有的 PR 引用会失效。
另外 GitHub 会在自己的服务器上缓存旧对象一段时间，彻底消失需要联系 GitHub Support
或等待其垃圾回收。**如果那个包里有任何敏感内容，正确的做法是当作已经泄露处理
（该轮换的轮换），而不是只依赖删除。**

## DEC-033 · 2026-09-11 · 仓库是 PUBLIC，与既有决定冲突；等待 Owner 裁决

**事实**（2026-09-11 通过 GitHub API 核实，非推断）：

```
GET /repos/fcubeve-alt/photomanage → "private": false, "visibility": "public"
forks 0 · stars 0 · watchers 0 · open PRs 0
```

`PROJECT_STATE.md` 的 Constraints 一节写着「**Repo must be PRIVATE**」，理由是公开会暴露
产品宪法、定价策略、$39 测试和未发布的落地页文案。**这四样现在全部是公开的。**

**最可能的成因**：2026-09-06 的 handoff 在「CI 分钟数耗尽」条目下列过三个选项，其中
(c) 是「把仓库公开，Actions 就免费——这会公开一切，所以是个决定不是权宜之计」。看起来
这个选项被采纳了，但从未写回决策记录，于是文档继续声称 PRIVATE。**这不是事故，更像是
一个做过但没记录的决定**；只是没有证据能确认，所以这里两种可能都列出。

**本次未执行任何设置更改。**改变可见性是 Owner 的决定，且如果公开是有意的，改回去反而
会再次弄坏 CI。

**需要 Owner 二选一：**

- **A. 公开是有意的** → 撤销「Repo must be PRIVATE」这条约束，把理由写进决策记录，
  并复核 `10_SOURCE_DOCS/`、`20_TIER0/evidence/`、定价矩阵这些内容是否都接受公开。
- **B. 公开是意外** → 按事故处理：改为私有；检查 fork/clone/Actions artifact；
  轮换任何曾进入历史的凭证；清理文档里的本机路径和用户名。

**无论选哪个**，`check_repo_reality.py` 现在会在 `verify.sh` 里核对文档声明与 GitHub
实际状态，不一致就失败。这个漂移之所以能存在几周，是因为**没有任何检查在看真实世界**——
`recovery_check.py` 检查的是文档自洽，不是文档为真。

**已知残留**：Money OS 的 zip（DEC-032）和 11.8 MB 的 `eval_catalog.sqlite.ablation`
都仍在 git 历史中，任何人知道 commit SHA 就能取到。后者确认为合成数据（资产 ID
A00001…，生成器产物），不是保密问题，只是体积。前者是另一个项目的包，清除方案和代价见
DEC-032。

---

## DEC-034 · 2026-09-11 · 不做账号体系

**Decision.** 产品不设账号：不注册、不收邮箱、不接 Sign in with Apple。购买权益绑定在
Apple ID 上，换设备用 `AppStore.sync()` 恢复。

**Rationale.** 本产品不联网、不在任何服务器上保存任何东西。加一个账号意味着为了卖一件
根本不需要邮箱的东西而去收集一个邮箱地址——它会把《隐私政策》第一条从真话变成假话。
StoreKit 2 在设备上验证交易签名（`VerificationResult`），这是 Apple 自己推荐的路径，
也是唯一与"不联网"相容的路径。

**Evidence.** `40_APP/PVM/Store/Purchases.swift`；`50_LAUNCH/PRIVACY_POLICY.md` 第 6、7 节。

**Impact.** 「账号体系」这一项从待办变成已决定。代价：无法跨 Apple ID 迁移权益，
无法做基于账号的客服查询——两者都不需要。

**Status.** ACTIVE。若将来出现必须有服务器的功能，这条要先被推翻，而不是绕过。

---

## DEC-035 · 2026-09-11 · 崩溃上报不接任何第三方 SDK

**Decision.** 崩溃记录写在设备本地文件，下次启动时**把全文展示给用户**，由用户自行决定
是否用自己的邮件 App 发送。不接 Crashlytics / Sentry / Bugsnag / 任何同类服务。

**Rationale.** 这类 SDK 的工作方式就是把报告发到别人的服务器。竞品拆解
（`20_TIER0/evidence/COMPETITOR_PRICING_MATRIX.md`，2025-01-13 第三方技术分析）记录：
用户付费 $7.99/周**之后**元数据仍经 6 个以上追踪 SDK 外传，隐私标签声称"未关联到你"
而实际负载携带用户 ID。装一个那样的 SDK 再写"不收集任何数据"的隐私政策，是同一个谎言
换了名字。

**Cost, stated plainly.** 我们会漏掉绝大多数崩溃——只有愿意手动发邮件的用户会报告。
这是为了那句承诺是真的所付的价，不是一个可以两全的设计。

**Evidence.** `40_APP/PVM/Support/CrashReporter.swift`（signal-safe，写本地文件，
自动重新抛出信号让系统照常记录）；`40_APP/check_no_network.py` 在 `verify.sh` 中
强制"App 内不存在任何联网 API 与分析 SDK"。

**Impact.** App Store 隐私问卷可以诚实地回答 **Data Not Collected**。

**Status.** ACTIVE。

---

## DEC-036 · 2026-09-11 · 迁移策略：重建派生数据，保留用户写下的东西

**Decision.** 目录数据库升级时清空并重算全部派生表，保留 `decisions`、`entity_review`
与 `meta` 中 `pref.` 前缀的键；不复制文件、不做逐列迁移。更新版本戳与清空工作放在
同一个事务里，且在工作**之后**。降级（文件版本高于当前构建）不做任何猜测，把文件连同
`-wal`/`-shm` 改名挪走。

**Rationale.** 这个产品的目录几乎全是派生数据，可以从照片库免费重算；而 `decisions` 是
§14 Personal Policy 的证据来源，`entity_review` 是 §24 Gate 2 已经决定要问的问题——
这两样丢了会悄悄改写系统对用户的认识。在装着 10 万张照片目录的手机上复制数据库，
是用用户可能没有的存储空间去保护可以免费重算的数据。

**Bug this fixed.** 原 `Catalog.init` 无条件写入当前版本戳。旧文件打开后立刻被标成
"当前"，若迁移执行前进程被杀，下次启动会认为一切正常而表结构仍是旧的——**判断所需的
证据被自己覆盖掉了**。

**Evidence.** `40_APP/PVMCore/Sources/PVMCore/Migration.swift`；
`40_APP/PVMCore/Tests/PVMCoreTests/MigrationTests.swift`（含
`testOpeningAnOldFileDoesNotClaimItIsCurrent`）；`50_LAUNCH/DATA_MIGRATION.md`。

**Impact.** 「数据迁移方案」从待办变成已实现。不做 iCloud 同步、不做目录导出——
目录含 OCR 出的证件与银行文字，一个可以被导出的目录文件就是一个可以被误发的文件。

**Status.** ACTIVE。

---

## OPEN-4 · 2026-09-11 · 定价待裁决（阻塞 App Store 商品）

`Commerce.paywall` 当前是空集：全部功能免费，所有购买入口隐藏。这是一个**记录在案的
状态，不是疏漏**——DEC-026 取消了 T0-C2（假门支付测试），本项目从未测量过任何人的付费
意愿，现在定价等于凭空发明那次测试本该买到的证据。

三个选项与建议见 `50_LAUNCH/PRICING_PROPOSAL.md`。裁决后改一行代码
（`40_APP/PVM/Store/Commerce.swift`）并记 DEC-037。
