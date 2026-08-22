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
**Status.** ACTIVE. Revisit at the Tier 0 gate and again at Tier 2-A/C.
