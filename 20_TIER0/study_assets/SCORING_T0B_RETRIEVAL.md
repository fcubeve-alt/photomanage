# SCORING SHEET — T0-B · RETRIEVAL ENTRY
One per participant. **Do not record any T0-D answer on this sheet** (DEC-014 separation rule).

```
Participant ____   Date ________   Facilitator ____________
Age band  ☐18-29 ☐30-44 ☐45-59 ☐60+     Own library size (approx) __________
Own phone model ____________   Recording consent ☐yes ☐no
Arm order  ☐ A→B   ☐ B→A          (A = Apple Photos, B = prototype)
```

### Fair-configuration verification (AB-5 / PF-07) — refuse to start without this
```
☐ Apple Photos has FULL library authorisation (not limited)
☐ People indexing COMPLETE (Albums ▸ People populated)
☐ Device idle ≥30 min since library load, indexing settled
☐ Prototype catalogue loaded, launched once, then closed
☐ Both apps CLOSED, not backgrounded
Notes: ______________________________________________
```
> A rigged win is worse than a loss. If any box is unticked, the session is a pilot, not data.

---

## 1 · First open (B-1) — record BEFORE any tapping

| | Arm 1 (____) | Arm 2 (____) |
|---|---|---|
| Time to first meaningful reaction (s) | | |
| Organisation vocabulary unprompted? Y/N | | |
| Asked "did it do this by itself?" Y/N | | |
| First reaction (verbatim) | | |

**Passport prediction — asked before any tap, both arms:**

| | Arm 1 | Arm 2 |
|---|---|---|
| Their answer (verbatim) | | |
| Correct? Y/N | | |

> Sharpest single measurement in the study. A participant who can predict where a thing lives, before touching the screen, has an entry point. One who cannot has another app to search.

---

## 2 · Retrieval tasks

Success: **F** found · **W** found-wrong · **G** gave up (3 min cap)

### Arm 1 — ____________
| # | Task | S | Time (s) | Steps | Backtracks | Notes / verbatim |
|---|---|---|---|---|---|---|
| T1 | ID card front + back | | | | | |
| T2 | White top, Tokyo, last year | | | | | |
| T3 | Headphones receipt | | | | | |
| T4 | One person, 3 years | | | | | |
| T5 | Bicycle across occasions | | | | | |
| T6 | Pickup code, ~7 weeks ago | | | | | |
| T7 | Burst of 8, keep best (**manual**) | | | | | |

T7 confidence they kept the right one: ____ /5

### Arm 2 — ____________
| # | Task | S | Time (s) | Steps | Backtracks | Notes / verbatim |
|---|---|---|---|---|---|---|
| T1 | ID card front + back | | | | | |
| T2 | White top, Tokyo, last year | | | | | |
| T3 | Headphones receipt | | | | | |
| T4 | One person, 3 years | | | | | |
| T5 | Bicycle across occasions | | | | | |
| T6 | Pickup code, ~7 weeks ago | | | | | |
| T7 | Burst of 8, keep best (**manual**) | | | | | |

T7 confidence they kept the right one: ____ /5

### Hard-negative observations (record if they surface at all)
```
Contract pages 1-4 treated as duplicates by either app?      ☐no ☐yes ☐n/a  ______
Burst frame with different expression collapsed/lost?        ☐no ☐yes ☐n/a  ______
ID front OR back hidden by grouping?                         ☐no ☐yes ☐n/a  ______
Re-shot ID card (months later) treated as a duplicate?       ☐no ☐yes ☐n/a  ______
```

---

## 3 · Forced choice (P-1 / P-2)

```
"If you needed to find a photo tomorrow, which would you open first?"
   ☐ app 1      ☐ app 2        → resolves to: ☐ Apple Photos  ☐ prototype

"Why that one?"  (verbatim — do not paraphrase, this is coded blind for P-2)
_____________________________________________________________________
_____________________________________________________________________

Blind coding (done later, by someone who did not run the session):
   ☐ STRUCTURAL  (predictable categories / already organised / knew where to look)
   ☐ NOVELTY or AESTHETIC  (looks nicer / newer / more modern)
   ☐ OTHER: ______________________
   Coder 1 ______  Coder 2 ______  Agree? ☐yes ☐no

"What annoyed you most about the other one?"  (verbatim)
_____________________________________________________________________
```

---

## 4 · Part 2 — their own library (Apple Photos only)

| # | Task chosen | S | Time (s) | Steps | Complaint (verbatim) |
|---|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |

### Apple Photos failure-case inventory
> The deliverable Tier 0 §3 explicitly asks for: 把「感觉」变成结构化的失败案例清单.
> Write cases, not adjectives. "Search for 'passport' returned 40 unrelated results" — not "search is bad".

```
1. ______________________________________________________________
2. ______________________________________________________________
3. ______________________________________________________________
4. ______________________________________________________________
5. ______________________________________________________________
```

---

## 5 · Counter-evidence (AB-6) — mandatory, not optional

```
Every moment the prototype confused, annoyed or failed this participant:
_____________________________________________________________________
_____________________________________________________________________

Anything about the setup that flattered the prototype:
_____________________________________________________________________

Facilitator deviations from the script:
_____________________________________________________________________
```
> Leaving this section blank is itself a finding — about the session, not the product.

---

## Data entry schema (one row per participant)

```csv
pid,age_band,own_library_size,arm_order,fair_config_ok,
first_open_a1_react_s,first_open_a2_react_s,
org_vocab_a1,org_vocab_a2,asked_byitself_a1,asked_byitself_a2,
passport_pred_a1_correct,passport_pred_a2_correct,
t1_a1_s,t1_a1_time,t1_a1_steps,t1_a1_back, ... (7 tasks x 2 arms x 4 fields),
t7_confidence_a1,t7_confidence_a2,
forced_choice,reason_verbatim,reason_code,coder_agree,
own_lib_task1_s,own_lib_task1_time,own_lib_task2_s,own_lib_task2_time,
own_lib_task3_s,own_lib_task3_time,
failure_cases_count,counter_evidence_present,notes
```

## PASS thresholds — pre-registered, no post-hoc changes (AB-7)

| ID | Criterion | Threshold |
|---|---|---|
| **P-1** | Forced choice = prototype | **≥ 70%** |
| **P-2** | Of those, structural reason (blind-coded) | **≥ 70%** |
| **P-3** | Prototype beats Apple Photos on median time **and** median steps | **≥ 4 of 6** retrieval tasks |
| **P-5** | Passport predicted correctly before tapping | **≥ 60%** |
| **P-6** | Spontaneous remark that the library is organised | **≥ 50%** |

*(P-4 retired — DEC-013 removed the Lucent arm.)*

**PASS** = P-1 **and** P-3 · **GO WITH CONSTRAINTS** = P-1 passes, P-3 fails · **FAIL** = P-1 fails → **NO-GO / PIVOT** per Tier 0 §3. A B FAIL is not a prompt to add features.

**Limitation L-1, to appear in the report summary and not a footnote:** the prototype's catalogue was prepared by hand for the test library. A PASS shows the interface concept works *if* the engine can be built — which Tier 1 must prove separately.
