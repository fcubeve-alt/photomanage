# SCORING SHEET — T0-D · AUTONOMOUS MANAGEMENT VALUE PROPOSITION
One per participant. **Separate sheet, separate deliverable.** Nothing here may be recorded on the T0-B sheet, merged into the retrieval report, or cited as evidence for it — and vice versa (Owner instruction, DEC-014).

Why this study exists: Constitution **§7** ends by requiring that the automation-tolerance bet be validated by real user testing *"而不能只凭工程师假设"*. The Tier 0 document contains no such test. This is it.

```
Participant ____   Date ________   Facilitator ____________
Ledger variant assigned BEFORE arrival (AB-11):  ☐V1 full  ☐V2 no-numbers  ☐V3 no-protected  ☐V4 review-first
Mode presentation order (rotated, AB-9): ______   Queue-size order (rotated): ______
T0-B completed first? ☐yes  ☐no  → if no, the session is out of protocol; record why: __________
```

---

## 1 · Ledger cold read (D-2)

```
Time to CORRECT comprehension: ______ s
   (correct = says the app has already organised and/or cleaned the library)

Identified UNPROMPTED that the work is already done?        ☐ yes  ☐ no
Asked "did it do this by itself?"                            ☐ yes  ☐ no
Asked whether the numbers are real? (answer honestly, AB-13) ☐ yes  ☐ no

First reaction (verbatim):
_____________________________________________________________________

What, if anything, they distrusted or wanted to check:
_____________________________________________________________________

Which block did their eye go to first? ☐Organised ☐Handled ☐Protected ☐Needs-you
   [V4 note: if review-first, does attention start on the homework?]
```

---

## 2 · Trust probe

```
"Would you let this run on your own photos?"
   ☐ Yes      ☐ No      ☐ Conditional

Conditions (VERBATIM — do not paraphrase; these are the Personal Policy design
input for §14, and a paraphrase loses the actual rule the user is proposing):
_____________________________________________________________________
_____________________________________________________________________
_____________________________________________________________________
```

---

## 3 · Mode preference (D-1) — the headline result

```
V1 nothing without approval  |  V2 obvious things auto, asks when uncertain
                             |  V3 manages continuously, asks only when it must

Choice:  ☐ Version 1   ☐ Version 2   ☐ Version 3

"Why?" (verbatim)
_____________________________________________________________________
_____________________________________________________________________

Value vs Version 1:  ☐ nothing more   ☐ a bit more   ☐ a lot more
   [relative only — a real price is T0-C2's job, not this session]
```

---

## 4 · Risk-graded tolerance (D-4)

| Content | auto | ask | never | Expected R-level | Hesitation / verbatim |
|---|:--:|:--:|:--:|---|---|
| Verification code screenshot, 6 months old | ☐ | ☐ | ☐ | R1 | |
| Meme downloaded four times | ☐ | ☐ | ☐ | R0 | |
| Eight near-identical burst photos | ☐ | ☐ | ☐ | R2 | |
| Photo of a meal | ☐ | ☐ | ☐ | R2 | |
| Receipt for a purchase | ☐ | ☐ | ☐ | R4 | |
| Screenshot of a work document | ☐ | ☐ | ☐ | R4 | |
| Family photo | ☐ | ☐ | ☐ | R3/R6 | |
| **Photo of an ID card** | ☐ | ☐ | ☐ | **R5** | |
| **Photo of a signed contract** | ☐ | ☐ | ☐ | **R5** | |

```
Does the pattern grade with risk, or is it flat?   ☐ graded   ☐ flat   ☐ inverted
Any item where they were MORE protective than §6 predicts: ______________
Any item where they were LESS protective than §6 predicts: ______________
```
> A **flat** pattern is the important negative result: it would mean the entire R0–R6 architecture rests on a distinction users do not actually make. Record it plainly.

---

## 5 · Recoverability effect (D-5)

```
Items re-asked (the 2-3 they were most protective about): ______________

After "it goes to Recently Deleted, restorable for 30 days":

| Item | Before | After | Changed? |
|------|--------|-------|----------|
|      |        |       |          |
|      |        |       |          |
|      |        |       |          |

Changed at least one answer?  ☐ yes  ☐ no

Verbatim:
_____________________________________________________________________
```
> The size of this shift is the first empirical measurement of §7's recoverability argument. Until now it has been an assertion.

---

## 6 · Review burden threshold (D-3)

| Queue size (of ~10,000) | handled for me | homework |
|---|:--:|:--:|
| 5 items | ☐ | ☐ |
| 23 items | ☐ | ☐ |
| 80 items | ☐ | ☐ |
| 300 items | ☐ | ☐ |

```
Crossover point (first size read as homework): ______ items
Per 1,000 assets: ______      → first empirical §18 Human Review Burden target
Verbatim at the crossover: ___________________________________________
```

---

## 7 · Counter-evidence (AB-12) — mandatory

```
Every refusal, hesitation, or "I'd want to check it myself":
_____________________________________________________________________
_____________________________________________________________________

Anything suggesting they said yes to be agreeable rather than because they meant it:
_____________________________________________________________________

Facilitator deviations from the script:
_____________________________________________________________________
```
> §7 is a **bet**, not a fact. This study exists to be able to lose. A sheet with no counter-evidence is a sheet that was not filled in properly.

---

## Data entry schema (one row per participant)

```csv
pid,ledger_variant,mode_order,queue_order,t0b_completed_first,
ledger_comprehension_s,identified_work_done,asked_byitself,asked_numbers_real,
first_gaze_block,trust_answer,trust_conditions_verbatim,
mode_choice,mode_reason_verbatim,relative_value,
tol_code,tol_meme,tol_burst,tol_meal,tol_receipt,tol_workdoc,tol_family,tol_id,tol_contract,
tolerance_pattern,recoverability_changed,recoverability_items_changed,
queue_crossover,hrb_per_1000,counter_evidence_present,notes
```

---

## PASS thresholds — pre-registered, no post-hoc changes (AB-7)

| ID | Criterion | Threshold |
|---|---|---|
| **D-P1** | Choose Version 2 or 3 over Version 1 | **≥ 70%** |
| **D-P2** | Choose Version 3 specifically | **≥ 40%** |
| **D-P3** | Understand the ledger unaided within 20 s | **≥ 70%** |
| **D-P4** | Identify unprompted that the work is already done | **≥ 60%** |
| **D-P5** | Tolerance is risk-graded | **≥ 80%** protect ID/contract **and** **≥ 60%** auto-handle expired codes + duplicate memes |
| **D-P6** | Recoverability raises tolerance on ≥1 previously protected item | **≥ 50%** |

**PASS** = **D-P1 and D-P5**. D-P5 is not optional — if tolerance is not risk-graded, the R0–R6 architecture rests on a distinction users do not share.

**GO WITH CONSTRAINTS** = D-P1 passes, D-P2 fails → users want assistance but not full autonomy. Default ships as Version 2; Version 3 becomes opt-in. Constitution §5/§17 unaffected; only the *default* changes.

**FAIL** = D-P1 fails → **escalate to Owner immediately as a potential Kill result.** Do not quietly redesign. This contradicts Constitution §5–§7 and §17, and a contradiction with Level 1 is escalated, never applied (PF-08).

### Variant comparison (across participants, not within)

| | V1 full | V2 no numbers | V3 no protected | V4 review-first |
|---|---|---|---|---|
| Median comprehension time | | | | |
| Identified work done | | | | |
| Trust = yes/conditional | | | | |
| Chose Version 3 | | | | |

> **V1 vs V4 is the sharpest comparison available.** Identical facts, opposite order. If V4 reads as homework and V1 reads as a service, then presentation — not capability — is carrying the value proposition. That is worth knowing before an engine exists.

**Limitation L-4, to appear in the report summary and not a footnote:** the ledger numbers were prepared for a test library. This validates the product *model*, not the engine. The question asked here is not "does our AI work" but "do users want an AI that does this at all".
