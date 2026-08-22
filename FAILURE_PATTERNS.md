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
**Guard.** Use the Write tool for prose documents. Reserve heredocs for code and short content without apostrophes.
**Status.** Occurred 2026-08-22 while writing `VALIDATION_MATRIX.md`. Recovered by switching tools; no data lost.

### PF-06 · Becoming another Lucent — capability parity mistaken for differentiation
**Risk.** Lucent Pro shipped natural-language search, OCR, object/face recognition, 200+ smart collections and duplicate detection, entirely on-device, in 262 MB — and got rating volume too low for Apple to display. The tempting reading is "we need *more* capability". That is the wrong lesson and the expensive one: Lucent had capability. What it appears to have lacked is a reason for the user to feel, quickly, that something valuable had already been done for them.
**Sharper form of the risk.** Our differentiators (risk-aware autonomy, continuous hygiene, personal policy) accrue over weeks and months. Lucent's differentiator (NL search) is demoable in ten seconds and *still* did not convert. So "we are more differentiated" may in practice mean **"we are harder to sell"**.
**Guard.** (a) The first session must produce a **quantified receipt of work already done**, including how little is left for the user — not a promise of future upkeep. (b) Feature additions are judged by whether they are *felt in the first session*, not by whether they extend the capability list. (c) Any comparison against Lucent must run under the fair-configuration rule (`LUCENT_PRO_BENCHMARK_COMPETITOR.md` Part 5) — beating a paywalled competitor proves nothing.
**Status.** Guard active. No occurrence yet. Full analysis: `20_TIER0/evidence/LUCENT_PRO_BENCHMARK_COMPETITOR.md`.

### PF-07 · Rigging a comparative study through competitor configuration
**Risk.** Lucent's free tier analyses only 1,000 photos. A 3-way study run against free Lucent on a 20,000-photo library would measure Lucent's paywall and report it as our advantage — a result that collapses the first time anyone checks, after we have already made decisions on it.
**Guard.** Fair-configuration rule, fixed before data collection: every competitor is tested **fully paid, fully permissioned and fully finished analysing**. If that state cannot be reached, the comparison is not run and the limitation is reported. Task order counterbalanced across participants. Session facilitator follows a fixed script or is not the prototype's author.
**Status.** Guard active. Caught during study design, before any data was collected.
