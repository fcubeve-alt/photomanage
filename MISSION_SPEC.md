# MISSION SPEC
Personal Visual Memory Engine · compiled from Product Constitution v1.3 (L1) + P0 Kill Test programme (L2)
Status: ACTIVE · Owner defines WHAT, AI owns HOW (Playbook E-02)

## Mission
Turn the Camera Roll from an unsorted file pile into a **self-cataloguing, self-maintaining personal visual library** that the user can browse, search, relate and trust — and that keeps doing so for every new photo, automatically.

One line (Constitution §21): *把 Camera Roll 从混乱的文件堆，变成一座自动编目、自动维护、随时可找到任何东西，并能逐渐理解生活的个人视觉图书馆。*

## Current mission (this is NOT the product build)
**Prove or kill the P0 assumptions, in Tier order, with real evidence.**
The mission right now is validation, not product development. Shipping an app is downstream of a GO decision that does not yet exist.

## Success criteria — Tier 0 (current)
Mission-level success for this phase = a defensible `TIER0_GO_NO_GO.md` backed by real measurements, not opinion.
- **A** Device: 100k-asset first index completes on real iPhones (3 tiers) without thermal death or unrecoverable background kill, and updates incrementally.
- **B** Retrieval Entry: in blind/semi-blind task tests against native Apple Photos, a majority of **external** users prefer this product as their first stop for finding visual assets.
- **C** Payment: a real conversion signal (not a survey) at the *Continuous Automatic Management* rung or higher.
**Superseded 2026-09-06 by DEC-026.** The Owner has decided the product is a GO and cancelled **C** and **D**; **B** is frozen pending OPEN-2. **A is the only remaining kill test** — it asks a physics question that the build decision does not answer. A3 failure is fatal; an A1-only failure degrades scope rather than killing. The Constitution §7 automation-tolerance bet is now a named accepted risk carried into M4 rather than a Tier 0 finding.

## IN SCOPE (now)
- Tier 0 Workstreams **A, B, C and D** and their required deliverables. D was added by Owner instruction (DEC-014) to satisfy Constitution §7, which requires the automation-tolerance bet be validated by real users.
- Windows-executable research, modelling, data structures, protocols, test harnesses and benchmark design that directly serve Tier 0.
- Persistent state, evidence store, decision log.

## OUT OF SCOPE (now) — hard boundary, Execution Index v1.0
Do **not** build, even "while we're here":
- Full Visual Asset Taxonomy · Category-Specific Entity Resolver · Lifecycle Engine → **Tier 1**
- R0–R6 Risk Policy Engine · Equivalence Margin selection · full Structure-First home · Multi-Signal Classification · Personal Policy learning · unit economics at scale → **Tier 2**
- Any production iOS app.
- Any Money OS / Project M business content (Playbook §6).
- Any redesign of the product defined in Constitution v1.3.

## Hard constraints
1. **Safety red lines (active from Tier 0):** no silent permanent deletion; IDs / contracts / family memories default to Protect; every suggestion must be able to explain *why*.
2. **Privacy-first:** private photos, IDs, relationships, purchases and travel data must never be uploaded or exploited for ad profiling (Constitution §26).
3. **Evidence only:** "looks fine", "should work in theory", "the code is written" are never PASS. Real run, real numbers, real users (Launch Instruction, Phase C).
4. **No on-device claims without a device.** Anything requiring a real iPhone is tagged `REQUIRES_DEVICE` and reported as untested — never simulated and presented as validated. *Scope corrected 2026-08-22:* only **T0-A** is device-bound. T0-B and T0-D use an HTML prototype and need no Mac, no TestFlight and no Apple Developer account.
5. **No 2GB+ model dependency without benchmark evidence.** Apple-native capability is the default hypothesis to test first; Gemma / external GPT API are neither presumed nor excluded. Route decided by benchmark, not by model name.
6. **One Tier at a time.** Later-Tier docs may be read for planning; their tasks may not be implemented.

## Human Gates (escalate ONLY for these)
| Gate | Trigger | Status |
|---|---|---|
| **HG-1** | Apple Developer Program enrolment — $99, legal name, own credit card, 2FA, possibly photo ID. Then 8 signing secrets | **BLOCKING T0-A.** Precondition satisfied: the harness compiles green at $0 (DEC-018), which was the rule DEC-015 set |
| **HG-2** | Real payment or spend | **CLOSED 2026-09-06 (DEC-026)** — T0-C2 cancelled, no domain and no ad spend. *Formerly: BLOCKING T0-C2* — domain (~$12) + ~$500–700 ad spend, plus Owner approval of positioning, the $39 price and the disclosure wording. *The cloud-Mac rental was withdrawn (DEC-016) — GitHub Actions replaced it at $0* |
| **HG-3** | Access to a Mac / Xcode for Tier 0-A | ✅ **RESOLVED at $0** (DEC-016) — GitHub Actions standard arm64 macOS runners |
| **HG-4** | Recruiting real external test users | **T0-D cancelled (DEC-026); T0-B frozen pending OPEN-2.** *Formerly: BLOCKING T0-B and T0-D.* n ≥ 15 (raised from 10 — DEC-021). **Needs no Mac and no spend**: the cheapest path to answering two of the four kill questions |
| **HG-5** | Irreversible or high-risk operations | DORMANT |
| **HG-6** | Material product scope change | DORMANT |
| **HG-7** | Two reasonable technical routes with major long-term architectural divergence | DORMANT |
| **HG-8** | A P0 result that genuinely could kill the project | DORMANT. **Armed trigger:** a T0-D `D-P1` failure contradicts Constitution §5–§7/§17 and escalates here (DEC-014, PF-08) |
| **HG-9** | All valuable work externally blocked | DORMANT |

> ~~HG-5 "create a private GitHub repository"~~ — ✅ **DONE 2026-08-22.** That gate was
> assigned an ID already in use by "irreversible operations"; the collision is removed
> and HG-5 means only its original definition. The repo exists at
> `github.com/fcubeve-alt/photomanage` (private), which also closed the E-06
> local-only single point of failure.

A gate blocks **its own branch only**, never the whole mission (Playbook S-03).
Ordinary bugs, test failures, dependency installs, research, refactors, docs and local technical choices are **never** escalated.
