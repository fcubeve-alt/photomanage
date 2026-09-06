# FAILURE PATTERNS
Part 1 is inherited (Playbook v1.1 §4) — already paid for by earlier projects.
Part 2 is this project. Append a new entry every time a real failure happens here (E-15 Learn Once).

## Part 1 — Inherited, active guards

| ID | Pattern | Guard in this project |
|---|---|---|
| F-01 | First viable route hijacks the mission — deep-dive before covering the search space | Tier ordering is fixed by the Execution Index. No deep build before the breadth question is answered. |
| F-02 | Scope drift — HOW-autonomy mistaken for WHAT-autonomy | `MISSION_SPEC.md` IN/OUT SCOPE + HG-6. |
| F-03 | Sunk cost — continue because code already exists | Gate question at every tier: *starting from zero today, would I spend the next unit here?* |
| F-04 | Chat completion = project completion | S-01/S-04. Finishing a deliverable triggers requeue, not a stop. |
| F-05 | Tool outage = brain outage | Web search unavailable → switch to the search-free queue. |
| F-06 | Local not found = never existed | Check authoritative remote before rebuilding anything. |
| F-07 | Big-bang research lost to a quota wall | Competitor research checkpoints per competitor, not at the end. |
| F-08 | Busy = progress | Progress counts only as reduced decision uncertainty, a verified/falsified hypothesis, reusable evidence, or economic value. File count and token spend count for nothing. |
| F-09 | UNKNOWN treated as negative | UNKNOWN is its own state and carries a resolution plan. |
| F-10 | Reviewer = boss | Challenges get re-verified, then accepted/partially accepted/rejected with a reason. |
| F-11 | Token saving = underthinking | Optimize Waste, Not Thinking. Skipping a Kill Test to save tokens is forbidden. |
| F-12 | One model = project identity | Mission, state, decisions, evidence and queue all live on disk. |

## Part 2 — This project

### PF-01 · Simulation presented as device validation
**Risk.** Windows-only environment plus pressure to show progress makes it tempting to model iPhone indexing throughput and then let the number drift into the record as if it were measured on hardware. Tier 0-A would then read PASS while nothing was ever run on a phone.
**Guard.** `OPERATING_RULES.md` P-02. Every device-dependent row in `VALIDATION_MATRIX.md` carries `REQUIRES_DEVICE` and an explicit **NOT TESTED** status. Predicted numbers must be labelled PREDICTION with their assumptions and are never written into a benchmark deliverable.
**Status.** Guard active. No occurrence yet.

### PF-02 · Constitution richness pulling work into later tiers
**Risk.** The Constitution is detailed and inviting — taxonomy tables, R0–R6 ladder, 8-layer pipeline. It reads like a build spec. Starting it now would burn the entire kill-test budget before a single kill question is answered.
**Guard.** DEC-003 and P-01. Constitution sections describing Tier 1/2 capability are reference-only during Tier 0.
**Status.** Guard active. No occurrence yet.

### PF-03 · Survey evidence smuggled in as payment signal
**Risk.** Real conversion data needs a domain, a payment path and Owner spend. Interest surveys and friendly opinions are free. Tier 0-C explicitly rejects them, and the substitution would look like progress while proving nothing.
**Guard.** T0-C2 accepts only reach-checkout / deposit / paid-beta data. Anything else is recorded as UNKNOWN with a resolution plan, never as PASS.
**Status.** Guard active. No occurrence yet.

### PF-04 · Word-source re-parsing every session
**Risk.** All source material is .docx. A fresh session with no guidance re-extracts binaries to answer a one-line question, repeatedly.
**Guard.** DEC-007 + P-06: read `10_SOURCE_DOCS/_extracted_text/*.txt`.
**Status.** Guard active — this session already paid the extraction cost once.

### PF-05 · Shell heredoc corrupted by apostrophes in prose content
**Risk.** Writing long English prose into files through a quoted shell heredoc failed with an EOF parse error when the content contained an odd number of apostrophes, because the command is wrapped in single quotes by the harness. Silent truncation or a lost file is possible.
**Guard.** Use the Write tool for prose documents. For edit scripts containing prose, **write the script to a file with Write and run it by path** — do not inline it in a heredoc. Reserve inline heredocs for short content with no apostrophes.
**Status.** Occurred three times on 2026-08-22 (VALIDATION_MATRIX write, then two edit scripts, then a git commit message). Each time recovered with no data lost, but it cost round-trips. Guard upgraded after the third occurrence: **commit messages also go via `git commit -F <file>`.**

### PF-06 · Becoming another Lucent — shipping a search tool instead of an organised library
**Risk.** Lucent Pro shipped NL search, OCR, object/face recognition, 200+ smart collections and duplicate detection on-device in 262 MB, and got rating volume too low for Apple to display. The trap is drifting into the same product: analysing the library so the user can *search* it, rather than handing the library back **already organised and already cleaned** and becoming the place the user goes to look at their photos.
**What this project does instead — both visible on first open:** (a) Constitution §12, first-run full-library cataloguing — the user opens the app and their library is already sorted into a predictable hierarchy, expired temporary content cleared, duplicates cleared, with only a very small Review Queue left; (b) Constitution §22/§23, the entry point changes — the user stops opening Apple Photos to look at their own photos.
**Guard.** (a) The Tier 0-B prototype leads with the **already-catalogued library**, not with a search box. (b) A feature earns its place by making the catalogue more complete, more predictable or more trustworthy — not by extending the capability list. (c) Any comparison against Lucent runs under the fair-configuration rule (PF-07) — beating a paywalled competitor proves nothing.
**Status.** Guard active. Full analysis: `20_TIER0/evidence/LUCENT_PRO_BENCHMARK_COMPETITOR.md`.

### PF-08 · Over-applying a competitor lesson until it contradicts the Constitution
**Risk.** Lucent's weak traction is a real signal, and it is tempting to reason outward from it until the conclusion overrides Level 1 product truth. That is exactly what happened on 2026-08-22: I merged first-run cataloguing (§12, immediate) with continuous hygiene (§13, gradual), concluded "our differentiators only pay off over weeks, so we may be harder to sell than Lucent", and recommended a first-run "receipt" as a *new* idea — when §12 already specifies the first-run experience and names its value moment. A competitor with unknown causes of failure was allowed to outrank an authoritative product document.
**Why it matters.** The Constitution is Level 1. It may only be overridden by demonstrated technical infeasibility or a documented material conflict — never by inference from a third party's market performance, especially when UNKNOWN-1 says we cannot even tell why they failed.
**Guard.** Before any competitor-derived conclusion is allowed to change product direction: (1) name the Constitution section it touches and re-read it; (2) if the conclusion contradicts that section, it is a **finding to escalate**, not a change to apply; (3) competitor evidence whose causal mechanism is UNKNOWN can inform *how we test*, never *what we build*.
**Status.** **Occurred 2026-08-22.** Caught by Owner challenge, not by me. Corrected in DEC-012; Part 3 of the Lucent analysis rewritten; PF-06 reframed.

### PF-07 · Rigging a comparative study through competitor configuration
**Risk.** Lucent's free tier analyses only 1,000 photos. A 3-way study run against free Lucent on a 20,000-photo library would measure Lucent's paywall and report it as our advantage — a result that collapses the first time anyone checks, after we have already made decisions on it.
**Guard.** Fair-configuration rule, fixed before data collection: every competitor is tested **fully paid, fully permissioned and fully finished analysing**. If that state cannot be reached, the comparison is not run and the limitation is reported. Task order counterbalanced across participants. Session facilitator follows a fixed script or is not the prototype's author.
**Status.** Guard active. Caught during study design, before any data was collected.

### PF-09 · A check that cannot fail is worse than no check
**Risk.** A green result creates confidence. If the check could not have gone red, that confidence is manufactured, and it is *more* dangerous than having no check — because nobody looks again at something already verified.

**Three instances in one sitting, all in `recovery_check.py`:**
1. **Vacuous pass.** `all 0 internal links resolve` reported OK. There are zero markdown links in the state files — they use backticks. The check ran, matched nothing, and reported success.
2. **Cry wolf.** Two files that plainly existed were reported missing, because the resolver guessed candidate directories instead of indexing the tree. False alarms train people to ignore the tool, which disables every *true* alarm alongside them.
3. **Undetectable contradiction.** The milestone-agreement check used `"M1" in pos`, which matches both *"M1 in progress"* and *"M1 complete"*. It reported agreement while `MASTER_PLAN` said M2 was current and `PROJECT_STATE` said M1.

Case 3 is the worst of the three: the check existed **specifically** to catch that contradiction, and the contradiction was live in the repo while it reported green.

**Guard.** Every check gets a **negative control** before it is trusted: deliberately break the thing it is meant to catch and confirm it goes red, then restore. If it cannot be made to fail on demand, it is not a check — it is decoration. Applied to the milestone check, which now demonstrably reports `FAIL` when `MASTER_PLAN` and `PROJECT_STATE` disagree, and `ok` when they do not.

**Also:** an empty check must report **N/A**, never OK. Zero things verified is not zero things wrong.

**Status.** Occurred 2026-08-23, three times. All three fixed. Negative control is now the standard before relying on any new check — the same discipline already applied to the four analyzers (self-test before real data).

### PF-10 · Tooling that works only on the machine that wrote it
**Risk.** Validation instrumentation is written on one machine and run — for the only time that matters — on another, months later, with real data on the table. Anything that silently depended on the first machine's environment surfaces at exactly the wrong moment.

**Occurred 2026-09-06**, on the first session after the project moved to a new computer. Both Tier 0 analyzers crashed with `UnicodeEncodeError` — `analyze_benchmark.py --selftest` and `analyze_studies.py selftest`. The new machine is a Chinese-locale Windows install, so `sys.stdout` defaults to **cp936**, which cannot encode the `⚠️`/`✅` glyphs the reports are built from. Both died **after** completing the whole analysis and printed nothing usable.

Why this one is worse than an ordinary bug:
- These tools each meet real data **once**. The device campaign ends, the participants go home, the CSV exists — and that is the moment the tool would have failed.
- Nothing was wrong with the analysis logic. `MASTER_PLAN` correctly claimed *"every analyzer is self-tested"* — the self-tests had genuinely passed. They passed **on the old machine**, and the claim carried no environment with it.
- The failure was invisible to every existing check. `recovery_check.py` verifies that documents are consistent and that files resolve. It does not run anything.

**Guard.** Three parts, all landed:
1. Every Python entry point pins `sys.stdout`/`sys.stderr` to UTF-8 at start-up, rather than removing the characters from the reports. Console locale is now an input the tools ignore.
2. `.github/workflows/tools-check.yml` runs every self-test on each `.py` change, **and runs them again under `PYTHONIOENCODING=gbk`** — the exact condition that broke them.
3. Negative control verified per PF-09: the pre-fix code exits 1 under `PYTHONIOENCODING=gbk`, the fixed code exits 0. The check can go red.

**Generalisation.** A green self-test proves the logic, never the environment. Any claim of the form *"the tooling is ready"* must name the machine it was verified on, or be re-verified where it will actually run.

**Status.** Fixed and guarded (DEC-025).

### PF-11 · A wall of green results reading as "the product is built"
**Risk.** This project's output so far is almost entirely *instrumentation*: harnesses, generators, analyzers, protocols, CI checks. Each one finishes with a visible success — a green run, a passing test, a written report. Stack enough of them together and the honest sentence *"the validation tooling is ready"* is received as *"the app is ready"*. Nobody has to lie for it to happen; the shape of the reporting does it.

**Occurred 2026-09-06.** After a session that ended with "17 tests, 0 failures", the Owner asked directly: *"你难道就做完做好了吗？我觉得没那么快吧… 整个系统要按照各种分类，应该不是那么容易就编好吧？编好了吗？项目已经做好了？"* They were right to push back, and the doubt was correct.

The true accounting on that date:
- **~1,650 lines of Swift** — a stopwatch. It reads photos, times itself, records temperature, memory and battery, writes a CSV. **It does not classify, recognise, organise or understand anything.**
- **82 prototype HTML pages** — hand-authored, fixed content, no engine behind them. They exist to ask users whether a structure makes sense.
- **~3,100 lines of Python** — generators, analyzers, checkers. None of it ships.
- **The actual product — classifier, taxonomy engine, entity resolver, lifecycle engine, risk policy engine — is at ZERO lines**, is Tier 1/Tier 2 work, and is still LOCKED by the Execution Index.

**Guard.**
1. `README.md` states the "nothing of the product is built" line on the first screen, not as a footnote.
2. Any progress report that leads with green results must carry the same sentence in the same message. A test passing is evidence about a *tool*, never about the product.
3. When the Owner asks whether something is done, answer with the line count of what does **not** exist first.

**Status.** Caught by Owner challenge on 2026-09-06, not by me — the second time that has happened (see PF-08). Recorded in DEC-027.

### PF-12 · Building the product without reading the documents that specify it
**Risk.** The binding requirements live in L1 and L1-B. The digests — `CONSTITUTION_UNDERSTANDING.md`, `ARCHITECTURE_METHODOLOGY.md` — are convenient and incomplete by design. A session that reads only the digests can build something that works, passes its own tests, scores well on measures it chose itself, and quietly fails clauses that were written down before it started. Nothing goes red. The gap surfaces only when the Owner reads the output and recognises their own requirements being reported back as discoveries.

**Occurred 2026-09-06, twice in one session, and the Owner caught both.**

The Owner gave two design instructions — pace a large first index instead of racing it, and process only what changed in a video instead of every frame. Both were implemented and both were presented as new. Both were already mandatory:

- **L1 §24 Gate 3:** *"首次使用必须 Progressive Indexing。先给 Quick Wins 和基本目录，再逐渐补全深度索引。新增 TTFUV（Time To First Useful View）作为 P0 指标"*
- **L1 §24 Gate 1:** *"采用分层信号、轻量模型、分块/分时、checkpoint、增量处理和后台机会执行"*
- **L1-B §4:** *"禁止默认采用：Video → 每隔 N 帧抽图 → 每一帧跑完整视觉模型"*

Then: *"这些设计思想，都已经在文档中体现了，为何还要我这么碎片化的"*. Correct, and the honest answer is that I did not read them. `SESSION_HANDOFF.md` said to read L1 *"only if you need product-level detail"* — and I judged that building the product's core engine did not require product-level detail.

The audit that followed found more than the two clauses the Owner named. **L1 §18 defines eight KPIs the product is judged by — Automation Ratio, Human Review Burden, Weighted Error Cost, Catastrophic Error Rate, Classification Coverage, Retrieval Success, Continuous Hygiene Rate, Personalization Gain — and the evaluation reported none of them.** It reported F1 and precision, which I had chosen. An engine can score 0.998 F1 while handing 300 of every 1,000 assets back to the user, and the F1 cannot see it.

**Guard — structural, because an instruction to read more carefully is not one.**
1. `30_ENGINE/CONSTRAINTS.md` lists every binding L1/L1-B clause with its **verbatim source text**, an honest status, and the test or metric that proves it. 34 clauses: 21 DONE, 6 PARTIAL, 4 MISSING, 2 out of scope — the gaps named rather than absent.
2. `30_ENGINE/check_constraints.py` runs in CI and fails when a quote no longer appears in the source it cites, when a clause marked DONE names code that does not exist, or when a PARTIAL/MISSING has no explanation. **A constraint cannot be paraphrased into something easier to satisfy, and cannot claim completion on an intention.**
3. The evaluation reports the **§18 KPIs** alongside its own measures, and says which of the two wins when they disagree.
4. `SESSION_HANDOFF.md` no longer offers L1 as optional reading for engine work.

**Generalisation.** When a requirement is met by accident and reported as an insight, the requirement was not read. That is not a communication failure; it means the specification was not an input. Any component that implements product behaviour must cite the clauses it satisfies **before** it is called done.

**Status.** Caught by Owner challenge on 2026-09-06 — the third time (see PF-08, PF-11). Guarded in CI. Recorded in DEC-030.
