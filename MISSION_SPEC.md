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
Gate: A or B FAIL → NO-GO/PIVOT. C FAIL → **COMMERCIAL MODEL PIVOT only** (does not kill the product). A+B+C PASS → Tier 1.

## IN SCOPE (now)
- Tier 0 Workstreams A, B, C and their required deliverables.
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
4. **No on-device claims without a device.** Anything requiring macOS/Xcode/real iPhone is tagged `REQUIRES_MAC` / `REQUIRES_DEVICE` and reported as untested — never simulated and presented as validated.
5. **No 2GB+ model dependency without benchmark evidence.** Apple-native capability is the default hypothesis to test first; Gemma / external GPT API are neither presumed nor excluded. Route decided by benchmark, not by model name.
6. **One Tier at a time.** Later-Tier docs may be read for planning; their tasks may not be implemented.

## Human Gates (escalate ONLY for these)
| Gate | Trigger | Status |
|---|---|---|
| HG-1 | Apple Developer account / KYC / CAPTCHA | DORMANT |
| HG-2 | Real payment or spend (domain, ads, deposit collection, Mac/cloud-Mac rental) | **UPCOMING** — needed for Tier 0-C |
| HG-3 | Access to a Mac / Xcode / real iPhones for Tier 0-A | **BLOCKING for Tier 0-A** |
| HG-4 | Recruiting real external test users for Tier 0-B | **UPCOMING** — needed for Tier 0-B |
| HG-5 | Irreversible / high-risk operations | DORMANT |
| HG-6 | Material product scope change | DORMANT |
| HG-7 | Two reasonable technical routes with major long-term architectural divergence | DORMANT |
| HG-8 | A P0 result that genuinely could kill the project | DORMANT |
| HG-9 | All valuable work externally blocked | DORMANT |

A gate blocks **its own branch only**, never the whole mission (Playbook S-03).
Ordinary bugs, test failures, dependency installs, research, refactors, docs and local technical choices are **never** escalated.
