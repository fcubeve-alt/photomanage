# T0-D · AUTONOMOUS MANAGEMENT VALUE PROPOSITION — CONCEPT VALIDATION
**Windows-side preparation.** Status: `REQUIRES_USERS` `REQUIRES_MAC` — **NOT RUN.**
Added to Tier 0 by Owner instruction, 2026-08-22. Recorded as **DEC-014**.
Design authority: Constitution **§7, §12, §13, §18** · Tier 0 v1.1 · Execution Index v1.0

---

## 1. Why this belongs in Tier 0 — it is not scope creep

Constitution **§7** ends with an explicit instruction:

> 用户获得巨大持续便利时，对少量、低代价、可恢复的判断错误可能具有容忍度；**这必须通过真实用户测试验证，而不能只凭工程师假设。**

The Constitution therefore *mandates* a real user test of the automation-tolerance bet. The Tier 0 document does not contain one. **T0-D closes that gap.** It is the Constitution's own requirement, arriving at the tier where kill-questions belong.

And it is a genuine kill-question. Constitution §17 makes the **Risk-Aware Decision Engine the basis of autonomy**, and §5–§7 build the entire product on it. If users do not want a system that decides for them, that is not a feature to adjust — it is a foundation that failed, and it would fail *before* Tier 1 spends anything on taxonomy and entity resolution.

## 2. Compliance with the Execution Index — what is NOT built

The Execution Index forbids pre-building Tier 1/2 capability. T0-D obeys this completely:

| Not built here | Belongs to |
|---|---|
| Classifier / taxonomy engine | Tier 1-A |
| Category-specific entity resolvers | Tier 1-B |
| Lifecycle engine | Tier 1-C |
| R0–R6 risk policy engine | Tier 2-A |
| Equivalence Margin selection | Tier 2-B |
| Personal Policy learning | Tier 2-G |

**What IS built:** one screen and a structured interview. The numbers on the screen are **prepared by hand for the test library**, exactly as the T0-B catalogue is (T0-B L-1). This validates the *product model*, not the algorithm. Stated in the report as **L-4**.

> The question is not "does our AI work". It is **"do users want an AI that does this at all"** — and that can be asked before a single classifier exists.

## 3. Kill questions

- **D-1 · Model preference.** Do users clearly prefer *"AI 替我持续管理，只把少数问题交给我决定"* over *"我自己控制每一个决定"*?
- **D-2 · Ledger comprehension.** Does the first-screen **Work-Done Ledger** communicate the core value **immediately**, without explanation?
- **D-3 · Review burden.** What **Human Review Burden** (§18) reads as "it handled it for me" versus "it gave me homework"?
- **D-4 · Risk-differentiated tolerance.** Is tolerance for automation *risk-graded* the way §6 assumes — aggressive on R0/R1, protective on R5/R6?
- **D-5 · Recoverability effect.** Does 30-day recoverability materially raise tolerance, as §7 assumes?

## 4. Separation rule — Owner instruction, binding

> **T0-D results are recorded separately from T0-B and neither may substitute for the other.**

They answer different questions and can dissociate in both directions:

| | T0-B Retrieval Entry | T0-D Autonomous Management |
|---|---|---|
| Question | Will they come *here* to find things? | Will they let it *manage* for them? |
| Constitution | §22, §23 | §5, §7, §12, §13 |
| Deliverable | `RETRIEVAL_ENTRY_USABILITY_TIER0.md` | `AUTONOMOUS_MGMT_VALUE_PROP_TIER0.md` |

A B PASS with a D FAIL means: *a good browsable library, but users want to stay in control* → the automation thesis needs rework before Tier 2 invests in the policy engine. A D PASS with a B FAIL means the management model is wanted but our entry point is not earning the visit. **Both must be reported; neither may be cited as evidence for the other.**

Practical consequence: **run D after B in the same session, never interleaved**, and record them on separate instruments.

## 5. The Work-Done Ledger (the artifact under test)

The first screen after first-run cataloguing. It is the visible form of §12 — the system has already worked — and of §18's **Human Review Burden** as a headline rather than an internal metric.

Content (numbers prepared for the test library, all reversible, all explainable per §3 safety line):

```
Your library is organised.                      12,431 photos · finished 2 min ago

  ORGANISED
  Documents  47      Purchases  212     Screenshots 3,904
  People  1,208      Places  2,663      Objects  389
  Travel  4 trips    Timeline 2019–2026

  HANDLED FOR YOU                                        all recoverable for 30 days
  340   expired verification & pickup codes     cleared      why?
  1,867 duplicate downloads                     cleared      why?
  612   near-identical burst frames             best kept    why?

  PROTECTED
  12 documents · 3 IDs · 1 contract              never auto-touched

  NEEDS YOU
  23 items                                                            Review →
```

Design rules under test, each traceable:
- **Order:** organised → handled → protected → needs-you. Work first, homework last.
- **"Needs you: 23"** is the §18 Human Review Burden made the headline number.
- **"all recoverable for 30 days"** is the §7 recoverability claim, visible.
- **"why?"** on every action — the §3 safety red line (每一条建议都要能解释原因) present even in a throwaway prototype.
- **"Protected"** shown as a *positive*: this is what it refused to touch (§6 R5/R6).

### 5.1 Ledger variants (between-subjects, 1 per participant)
To isolate what actually carries the value:

| Variant | Change | Isolates |
|---|---|---|
| **V1 Full** | as above | baseline |
| **V2 No numbers** | qualitative only ("expired codes cleared") | whether *quantification* is what lands |
| **V3 No Protected block** | protection hidden | whether visible restraint drives trust |
| **V4 Review-first** | "23 items need you" at top, work below | whether ordering changes it from service to homework |

**V4 is the sharpest.** Same facts, opposite framing. If V4 reads as homework and V1 reads as a service, presentation — not capability — is carrying the value proposition, and that is a finding worth having before any engine exists.

## 6. Procedure (~25 min, after T0-B, same participants)

**Step 1 — Ledger cold read (D-2).** Show the assigned variant. *"Tell me what this screen is telling you."* Record: time to correct comprehension, whether they identify unprompted that the app already did the work, first emotional reaction, and whether they spontaneously ask "did it do this by itself?"

**Step 2 — Trust probe.** *"Would you let this run on your own photos?"* Yes / No / Conditional — record the conditions verbatim. These conditions are the Personal Policy design input (§14).

**Step 3 — Model preference (D-1).** Three modes described neutrally, order rotated:
- **M1 Full control** — nothing happens without your approval; you review every suggestion
- **M2 Balanced** — obvious things handled automatically, anything uncertain or important asked
- **M3 Autonomous** — it manages continuously and only asks about the few things that really need you

Forced choice, then *"why?"*, then: *"how much would you pay more for your choice than for M1?"* (relative, not absolute — a real price is T0-C2's job).

**Step 4 — Risk-graded tolerance (D-4).** For each content type, choose: auto-handle / ask me / never touch.
Expired verification code · meme downloaded 4× · 8-frame burst · food photo · receipt · work screenshot · family photo · **ID card** · **contract**.
This is the R0–R6 ladder validated **as a user preference**, with no engine built. If real users grade risk roughly as §6 predicts, the ladder is grounded in behaviour rather than assumption.

**Step 5 — Recoverability effect (D-5).** Re-ask step 4 for the two or three items they were most protective about, adding: *"everything deleted goes to Recently Deleted and is restorable for 30 days."* Record every changed answer. **The size of that shift is the empirical value of §7's recoverability argument.**

**Step 6 — Review burden threshold (D-3).** Show queue sizes in rotated order: 5 / 23 / 80 / 300 items out of ~12,000. For each: *"does this feel like it handled it for you, or like it gave you homework?"* The crossover point is the **first empirical target for Human Review Burden per 1,000 assets**, replacing an engineering guess.

## 7. PASS criteria — pre-registered, no post-hoc changes

| ID | Criterion | Threshold |
|---|---|---|
| **D-P1** | Choose **M2 or M3** over M1 | **≥ 70%** |
| **D-P2** | Choose **M3** specifically | **≥ 40%** — the model the product is actually built on |
| **D-P3** | Understand the ledger unaided within **20 s** | **≥ 70%** |
| **D-P4** | Identify unprompted that the app already did the work | **≥ 60%** |
| **D-P5** | Risk-graded tolerance broadly matches §6 (aggressive R0/R1, protective R5/R6) | **≥ 80%** protect IDs/contracts **and** ≥ 60% auto-handle expired codes/duplicate memes |
| **D-P6** | Recoverability raises tolerance on ≥ 1 previously protected item | **≥ 50%** |

**PASS** = D-P1 **and** D-P5. D-P5 is not optional: if tolerance is *not* risk-graded, the entire R0–R6 architecture rests on an assumption users do not share.
**GO WITH CONSTRAINTS** = D-P1 passes, D-P2 fails → users want assistance but not full autonomy; default to M2 and treat M3 as opt-in. Constitution §5/§17 unaffected; the *default* changes.
**FAIL** = D-P1 fails → **escalate to Owner immediately as a potential Kill result.** Do not quietly redesign. This would contradict Constitution §5–§7 and §17, and per PF-08 a contradiction with Level 1 is escalated, never applied.

## 8. Anti-bias

Inherits **AB-1…AB-8** from the T0-B protocol, plus:

| ID | Rule |
|---|---|
| **AB-9** | Modes M1/M2/M3 described in **neutral** language, presentation order rotated. Never "the smart option". |
| **AB-10** | Never ask "would you like AI to help?" — everyone says yes. Force a **trade-off**: control vs effort. |
| **AB-11** | Ledger variant assigned **before** the participant arrives; the facilitator does not choose on the day. |
| **AB-12** | Record **every** refusal, hesitation and "I would want to check it myself" verbatim. §7 is a bet, not a fact — this test exists to be able to lose. |
| **AB-13** | Do **not** tell participants the ledger numbers are prepared, and do **not** claim they are real. If asked directly, answer honestly and record that it was asked. |

## 9. Deliverable

`20_TIER0/evidence/AUTONOMOUS_MGMT_VALUE_PROP_TIER0.md` — separate file, never merged into the retrieval report:
1. Participants, variant assignment, order
2. D-1…D-5 results against §7 thresholds
3. Mode preference distribution + verbatim reasons
4. Risk-graded tolerance matrix vs the §6 ladder
5. Recoverability shift (§7 quantified for the first time)
6. Human Review Burden crossover → first empirical §18 target
7. Ledger variant comparison, especially **V1 vs V4**
8. All counter-evidence, at equal prominence
9. Verdict + **L-4 limitation stated in the summary**: the ledger numbers were prepared; this validates the model, not the engine

## 10. Feeds forward
- **T0-C2** — tells us whether the Continuous Management rung we intend to price is wanted at all
- **T2-A** — the R0–R6 default policy table starts from measured user preference instead of assumption
- **T2-G** — step 2 conditions are the initial Personal Policy design input
- **§18 KPI** — first real Human Review Burden target

## 11. Dependencies
Prototype + device (**HG-1/HG-2a**) · participants (**HG-4**, same cohort as T0-B) · ledger screen and interview instrument (**Windows-executable now**).
