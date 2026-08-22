# TIER 0 — GO / NO-GO DECISION
**STATUS: ⛔ NOT REACHED. This is a template, not a result.**
Nothing below is filled in, because **no Tier 0 measurement has been taken yet.**

Authority: `P0 Kill Test Tier 0 v1.1` · `P0 KILL TEST MASTER EXECUTION INDEX v1.0` · DEC-002, DEC-014
Created 2026-08-23 · to be completed when evidence exists, not before

---

## How this document is meant to be used

The gate logic, the thresholds and the failure handling were all fixed **before** any
data was collected. When the evidence arrives, completing this file should be
*transcription*, not argument. If filling it in requires a fresh debate about what
counts as a pass, something has gone wrong upstream — go back to the protocol.

**Every verdict slot must name the artifact it came from.** A verdict with no
artifact path is not a verdict; it is a recollection. Leave it blank instead.

**`NO DATA` is not a soft `PASS`.** A workstream that was not run is recorded as not
run, and the gate is INCOMPLETE. The Execution Index requires a Tier 0 gate
conclusion before Tier 1 begins; it does not permit inferring one.

---

## 1. Evidence register — fill this first

| Workstream | Deliverable | Exists? | Verdict | Analyzer output |
|---|---|---|---|---|
| **T0-A** device & thermal | `evidence/DEVICE_BENCHMARK_TIER0.csv` + `.md` | ☐ | ☐ PASS ☐ FAIL ☐ NO DATA | `analyze_benchmark.py` |
| **T0-B** retrieval entry | `evidence/RETRIEVAL_ENTRY_USABILITY_TIER0.md` | ☐ | ☐ PASS ☐ GO-WITH-CONSTRAINTS ☐ FAIL ☐ NO DATA | `analyze_studies.py b` |
| **T0-C1** competitor pricing | `evidence/COMPETITOR_PRICING_MATRIX.md` | ☑ **DONE** | ✅ complete (2026-08-22) | — |
| **T0-C2** real payment signal | `evidence/REAL_PAYMENT_SIGNAL_TIER0.md` | ☐ | ☐ PASS ☐ FAIL ☐ NO DATA | `server.py --report` |
| **T0-D** autonomous mgmt | `evidence/AUTONOMOUS_MGMT_VALUE_PROP_TIER0.md` | ☐ | ☐ PASS ☐ GO-WITH-CONSTRAINTS ☐ FAIL ☐ NO DATA | `analyze_studies.py d` |

> **T0-B and T0-D are recorded separately and neither may be cited as evidence for
> the other** (DEC-014). If one is a PASS and the other a FAIL, both are reported.
> That combination is informative, not a contradiction to be resolved.

---

## 2. Gate logic — fixed in advance, Tier 0 v1.1 §6

| A (device) | B (retrieval entry) | C (payment) | → Outcome |
|---|---|---|---|
| **FAIL** | any | any | **NO-GO / PIVOT.** Stop. |
| any | **FAIL** | any | **NO-GO / PIVOT.** Stop. |
| PASS | PASS | PASS | **GO → Tier 1** |
| PASS | PASS | **FAIL** | **TECHNICAL / PRODUCT GO + COMMERCIAL MODEL PIVOT** |

**The C-failure rule is the substantive change in v1.1 and must not be reverted
(DEC-002):** a commercial failure does **not** kill the product. It requires the
pricing, free/Pro boundary, one-off vs subscription and ad models to be re-tested,
and forbids heavy investment until the commercial model is fixed. Technical and
product work continues.

### T0-D handling (DEC-014)
D is **not** in the A/B/C gate arithmetic. It is reported alongside them.

- **D PASS** → the automation thesis has user support; Tier 2 may invest in the
  policy engine.
- **D GO WITH CONSTRAINTS** (D-P1 passes, D-P2 fails) → users want assistance, not
  full autonomy. Ship the balanced mode as default, autonomous as opt-in. §5/§17
  unaffected; only the *default* changes.
- **D FAIL** → ⛔ **ESCALATE TO OWNER AS A POTENTIAL KILL RESULT.** A D-P1 failure
  contradicts Constitution §5–§7 and §17. Per PF-08 a contradiction with Level 1 is
  escalated, never quietly redesigned around.

### Within T0-A, not all failures are equal (Tier 0 §2)
- **A3 (survivability) FAIL is fatal.** An index that cannot survive interruption
  cannot exist on a phone.
- **A1 (throughput) FAIL alone is survivable** — it degrades the product to a reduced
  scope ("recent N months") rather than killing it. Record the degraded scope
  explicitly if this happens.
- **A4 FAIL** means the index cannot be maintained without periodic full rescans.
  Report the measured `required_full_rescan` rate and the change-token lifetime.

---

## 3. Verdict

```
T0-A  ____________    artifact: ______________________________
T0-B  ____________    artifact: ______________________________
T0-C  ____________    artifact: ______________________________
T0-D  ____________    artifact: ______________________________

TIER 0 OUTCOME: ______________________________________________
```

**Reasoning (2–5 sentences, referencing the artifacts above — not recollection):**

```


```

---

## 4. Mandatory reporting — the Constitution's own KPIs

Constitution §18 and §20 require these to be reported **together**. Optimising for a
near-zero false-positive rate alone is an explicit anti-goal (§7, §20): it is the
Cleaner failure mode this product exists to reject.

| KPI | Tier 0 value | Source | Notes |
|---|---|---|---|
| Automation Ratio | | | mostly Tier 2 — record what Tier 0 can support |
| **Human Review Burden** | | T0-D queue crossover | per 1,000 assets; replaces the invented "23" |
| Weighted Error Cost | | | Tier 2 |
| Catastrophic Error Rate | | | Tier 2 |
| Significant Value Loss Rate | | | Tier 2-B |
| **Retrieval Entry Share** | | T0-B forced choice | §22 north star |
| **TTFUV** | | T0-A / CD-2 | first-screen stall as the floor |

Where a KPI belongs to a later tier, write "Tier 1"/"Tier 2" — **do not leave it
blank and do not estimate it.**

---

## 5. Limitations that must appear in the summary, not a footnote

Carry these forward verbatim. Each one bounds what a PASS actually means.

- **L-1 · Prepared catalogue.** The T0-B prototype's catalogue *and* its category tree
  were hand-made for the test library. A B PASS shows the interface concept works
  **if the engine can be built** — which Tier 1 must prove independently. It is not
  evidence that a classifier can produce this structure.
- **L-2 · Persona library.** Participants navigated someone else's life, not their own.
- **L-3 · Novelty.** Unfamiliarity cuts both ways; P-2 (blind-coded structural reason)
  exists to detect inflation.
- **L-4 · Prepared ledger numbers.** T0-D validates the product *model*, not the
  engine. The question asked was "do users want an AI that does this at all", not
  "does our AI work".
- **L-6 · Web prototype vs native app.** Arm B is HTML added to the Home Screen; arm A
  is native. This works **against** arm B, so a B PASS is conservative.
- **Sample size (DEC-021).** n=15 resolves an effect of ~90% or above. A result in the
  **70–89%** band is *directionally positive but not statistically resolved* and
  **must not be written as PASS** — say so in this document.
- **Single storefront / single channel.** T0-C1 covers the US App Store on one date;
  T0-C2 covers one traffic source.

---

## 6. What a Tier 0 PASS does NOT establish

Stated here so nobody reads the gate as more than it is.

| Not established by Tier 0 | Where it is decided |
|---|---|
| That the classifier can produce the taxonomy reliably | **Tier 1-A** |
| That Same-Entity works, especially Document-class False Merge | **Tier 1-B** |
| That lifecycle judgements are safe | **Tier 1-C** |
| That risk-aware automation is safe at scale | **Tier 2-A** |
| That Equivalence Margin selection loses no significant value | **Tier 2-B** |
| That TTFUV targets are met on a real first run | **Tier 2-C** |
| That the unit economics work at 10k / 100k / 1M users | **Tier 2-F** |

---

## 7. Next action, by outcome

- **GO** → open Tier 1. Create `TIER1_GO_NO_GO.md`. The Execution Index forbids
  starting Tier 1 work before this file exists with a conclusion.
- **GO + COMMERCIAL PIVOT** → Tier 1 technical work may proceed; commercial re-test
  runs in parallel. **No heavy investment until the commercial model is fixed.**
- **NO-GO / PIVOT** → stop. Write what specifically failed, whether it is fixable, and
  what alternative route exists. Per the Owner instruction: *不要为了「完成计划」掩盖失败.*
- **INCOMPLETE** → name the missing workstream and its blocking Human Gate. Do not
  proceed to Tier 1 on partial evidence.

---

## 8. Current state — 2026-08-23

**All four workstreams: instrumentation complete, ZERO measurements taken.**

| | Prepared | Blocked on |
|---|---|---|
| T0-A | harness compiles green on CI; analyzer self-tested | **HG-1** — $99 Apple Developer + signing secrets |
| T0-B | protocol, clickable prototype, test library, script, scoring sheet, analyzer | **HG-4** — 15 external participants |
| T0-C1 | ✅ **COMPLETE** | — |
| T0-C2 | three landing pages, instrumented, smoke-tested | **HG-2b** — domain + ~$500–700 ad spend |
| T0-D | protocol, 4 ledger variants, scoring sheet, analyzer | **HG-4** — same cohort as T0-B |

**Cheapest path to the most evidence: recruit the participants.** T0-B and T0-D need
no Mac, no TestFlight and no spend — they would answer two of the four kill questions
for the cost of fifteen people's time.
