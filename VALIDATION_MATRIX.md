# VALIDATION MATRIX
`TEST → SUCCESS CRITERIA → MEASUREMENT → PASS/FAIL → NEXT ACTION`
Source of truth: P0 Execution Index v1.0 + Tier 0/1/2 v1.1. Status is evidence-backed only.

Legend — **WINDOWS_OK** executable now · **REQUIRES_MAC** needs macOS/Xcode · **REQUIRES_DEVICE** needs real iPhones · **REQUIRES_USERS** needs external humans · **REQUIRES_OWNER** needs Owner action/spend

---

## TIER 0 — 生死开关 (CURRENT TIER · the only authorised build surface)

### T0-A · Real-device hardware & thermal limit  `REQUIRES_DEVICE` `REQUIRES_MAC`
| | |
|---|---|
| **Test** | First-run index of 10k / 30k / 100k assets across the **full TestFlight-capable device gradient** (DEC-008; record model, chip, iOS version, RAM, free storage). Layer 1 (metadata/time/GPS/hash/basic OCR) + Layer 2 (lightweight visual embedding) **only** — not the full 8-layer pipeline. Also verify PhotoKit full vs limited authorisation, deletion boundaries, change observer, and iCloud-only asset original/thumbnail request behaviour. |
| **Success criteria** | 100k first index completes in a reasonable wall time without thermal throttling or an unrecoverable background kill, **and** supports incremental update (no full rescan each run), **and** resumes from checkpoint after interruption. |
| **Measurement** | Wall time, peak memory, CPU %, thermal state (`ProcessInfo.thermalState`), battery drain %, index size on disk, checkpoint-resume success — per library size × device tier. Output: `DEVICE_BENCHMARK_TIER0.csv` + `.md`. |
| **Status** | **NOT TESTED.** HG-3 approved in principle: cloud Mac + existing ~6-iPhone fleet (DEC-008). Redesigned as a **cross-device performance gradient**; minimum supported model derived from the measured curve, never assumed. iPhone 7 excluded on verified evidence. No simulated result may be reported as a PASS. |
| **Next action** | Harness **compiles green** on GitHub Actions (run 32579093228, 48s, 0 billable min) — DEC-018. Build environment resolved at $0 (DEC-016). **Remaining: HG-1** — Owner enrols in Apple Developer ($99) and adds signing secrets, then `ios-testflight.yml` delivers to the device fleet. |

### T0-B · Retrieval Entry hypothesis  `REQUIRES_USERS`
| | |
|---|---|
| **Test** | Minimal Structure-First home skeleton (6 entries: Documents / People / Screenshots / Places / Timeline / Objects), presenting the **already-catalogued library** — not a search box (§12/§23). Real **external** users (not the team) perform the same tasks — find ID card, find one person from one trip, find a receipt, find a screenshot — in **native Apple Photos** vs **this prototype**. Two arms only; Lucent is not installed (DEC-013). |
| **Success criteria** | Under blind/semi-blind conditions, a **majority** of test users explicitly state the prototype is better and that they would rather use it as their first stop for finding photos. |
| **Measurement** | Per task: success rate, step count, time-to-find. Plus subjective forced choice, plus a structured list of concrete complaints about native Photos (turning "feeling" into failure cases). Output: `RETRIEVAL_ENTRY_USABILITY_TIER0.md`. |
| **Status** | **NOT RUN.** Protocol and prototype complete. **Blocked ONLY on participants (HG-4)** — corrected 2026-08-22: the HTML prototype needs no Mac, no TestFlight, no $99. |
| **Next action** | Protocol complete: `20_TIER0/T0B_RETRIEVAL_ENTRY_STUDY_PROTOCOL.md`. Remaining Windows-side work: build the §5 test library as an asset manifest, write the facilitator script and scoring sheet. Blocked on **HG-4** (participants) and HG-1/HG-2a (prototype). |

### T0-C1 · Competitor pricing matrix  `WINDOWS_OK`
| | |
|---|---|
| **Test** | Build the competitor pricing matrix required by Tier 0 §4 / original §9: CleanMyPhone, Clever Cleaner, Slidebox, Queryable, Lucent Pro and other relevant products. |
| **Success criteria** | For each competitor: free tier, price points and model (subscription / one-off / lifetime), rating and rating count, last update, and structured user complaints about subscriptions. Enough coverage to state which Value Ladder rung the market already prices at zero. |
| **Measurement** | `20_TIER0/evidence/COMPETITOR_PRICING_MATRIX.md`, each cell carrying source + retrieval date + confidence, with FACT / INTERPRETATION / RECOMMENDATION kept separate (Playbook E-13). UNKNOWN stays UNKNOWN (F-09). |
| **Status** | ✅ **COMPLETE** (2026-08-22) — 12 apps, US storefront. See also `evidence/LUCENT_PRO_BENCHMARK_COMPETITOR.md`. |
| **Next action** | Feeds T0-C2 landing-page pricing. No further work required for the gate. |

### T0-C2 · Real payment signal  `REQUIRES_OWNER`
| | |
|---|---|
| **Test** | Obtain a **real** conversion signal by one of: waitlist + deposit (even a few dollars); tiny paid TestFlight beta; or landing page with a real price where the click reaches the step immediately before charging. Surveys are explicitly rejected as evidence. |
| **Success criteria** | Real intent-to-pay at the **Continuous Automatic Management** rung or above. Cleaner-rung willingness does not count — that market is already trained to free. |
| **Measurement** | Traffic, click-through to price, reach-checkout rate, deposits collected. Output: `REAL_PAYMENT_SIGNAL_TIER0.md`. |
| **Status** | **NOT RUN.** Plan complete; nothing published, no domain, no ads, no money taken. Blocked on **HG-2b**. |
| **Next action** | Plan complete: `20_TIER0/T0C2_LANDING_PAGE_PLAN.md` — 3-arm rung test (Organised Library / Continuous Manager / Cleaner control) at a constant $39 one-off, full copy, funnel E1–E8, pre-registered C-P1…C-P4, no-charge fake-door with mandatory disclosure. Blocked on **HG-2b** (domain + ~$500-700 ad spend) and Owner approval of positioning/price/disclosure wording. **Run T0-D first** where possible — it tells us whether the rung is wanted before we pay to advertise it. |

### T0-D · Autonomous Management Value Proposition  `REQUIRES_USERS`
*Added 2026-08-22 by Owner instruction (DEC-014). Mandated by Constitution §7, absent from the Tier 0 document.*
| | |
|---|---|
| **Test** | Concept validation, run with the same participants immediately after T0-B on separate instruments. Does the user clearly prefer *AI 替我持续管理，只把少数问题交给我决定*? Does a first-screen **Work-Done Ledger** convey the value immediately? Four ledger variants; risk-graded tolerance probe across R0–R6 content types; recoverability probe; review-burden threshold. **Nothing from Tier 1/2 is built** — one screen plus a structured interview, ledger numbers hand-prepared. |
| **Success criteria** | Pre-registered D-P1…D-P6. PASS requires **D-P1** (>=70% choose assisted/autonomous over full manual control) **and D-P5** (tolerance is risk-graded: >=80% protect IDs/contracts, >=60% auto-handle expired codes and duplicate memes). |
| **Measurement** | `20_TIER0/evidence/AUTONOMOUS_MGMT_VALUE_PROP_TIER0.md` — **a separate deliverable. May never be merged with, or substituted for, the Retrieval Entry report** (Owner instruction). |
| **Status** | **NOT RUN.** Protocol complete: `20_TIER0/T0D_AUTONOMOUS_MANAGEMENT_VALUE_PROP_PROTOCOL.md`. |
| **Next action** | Ledger variants built (`study_assets/prototype/ledger_v1..v4.html`). **Blocked ONLY on HG-4** (participants). No Apple Developer dependency. |
| **Failure handling** | D-P1 FAIL contradicts Constitution §5–§7 and §17 — **escalate to Owner as a potential Kill result**, do not redesign around it (PF-08). |

### T0-GATE · Tier 0 decision
| | |
|---|---|
| **Rule** | A or B FAIL → **NO-GO / PIVOT**, stop. · A+B PASS and C PASS → **Tier 1**. · A+B PASS but C FAIL → **TECHNICAL/PRODUCT GO + COMMERCIAL PIVOT**: fix the commercial model and retest before heavy investment. · **D FAIL → escalate to Owner** — it contradicts Constitution §5–§7/§17, so it is an Owner decision, not an engineering adjustment (DEC-014). D is reported alongside A/B/C and is never substituted for B. |
| **Deliverable** | `20_TIER0/TIER0_GO_NO_GO.md` — **template written 2026-08-23**. Gate logic and failure handling fixed in advance, so completing it is transcription rather than argument. Every verdict slot must name the artifact it came from. Mandatory before any Tier 1 work begins. |
| **Status** | **NOT REACHED — zero measurements taken.** All four workstreams instrumented and blocked on Owner gates. |

---

## TIER 1 — 核心能力可行性  **LOCKED** (read-only until T0-GATE passes)
Recorded for sequencing only. Implementation is forbidden now (Execution Index v1.0).

| ID | Test | PASS criterion | Deliverable |
|---|---|---|---|
| T1-A | Visual Asset Taxonomy feasibility on a real library sample | Most common assets land in meaningful categories; Unknown ratio controlled; demonstrably finer than the Apple time/place/person grain | `VISUAL_ASSET_TAXONOMY.md`, `CLASSIFICATION_EVAL.md` + confusion matrix |
| T1-B | Category-Specific Entity Resolver (Document / Screenshot / Product) | **Document-class False Merge rate extremely low** (reported separately); overall Same-Entity clearly beats human eyeballing; low confidence → Review Queue only | `SAME_ENTITY_EVAL.md` + labeled test-set schema |
| T1-C | Visual Lifecycle Engine (OTP, pickup codes, tickets, receipts, error screenshots, IDs, contracts) | Reliable lifecycle calls on temporary content; **zero** auto-delete on high-risk classes; focus metric is Suggest-Delete **False Positive**, not overall accuracy | `LIFECYCLE_EVAL.md` + FP analysis |
| T1-D | Multi-dimensional index skeleton | One Asset carries Content/Time/Place/Person/Object/Event indices simultaneously without duplicating the original; inferred place stores source + confidence | `VISUAL_LIBRARY_DATA_MODEL.md` |
| T1-E | Four retrieval paths, lite | Browse / Timeline-Places / Intent Search / Relations — 2–3 real tasks each; the gap vs Apple must be stable, not novelty | `RETRIEVAL_PATHS_EVAL_LITE.md` |
| T1-GATE | | PASS / GO WITH CONSTRAINTS / NO-GO | `TIER1_GO_NO_GO.md` |

Note: T1-A/B/C/D are largely **WINDOWS_OK** once unlocked (algorithms, data models, labeled evals on a desktop photo corpus). They are blocked by *sequence*, not by hardware.

---

## TIER 2 — 完整体验与规模化  **LOCKED** (read-only until T1-GATE passes)

| ID | Test | PASS criterion | Deliverable |
|---|---|---|---|
| T2-A | Risk & Importance Policy Engine (R0–R6) | Zero auto-delete in R4–R6; high-volume automation in R0–R1; Weighted Error Cost controlled | `RISK_IMPORTANCE_POLICY_ENGINE.md` + policy table |
| T2-B | Equivalence Margin | Key metric **Significant Value Loss Rate**; hard negatives (different expression/action/document page) never merged | `EQUIVALENCE_MARGIN_EVAL.md` |
| T2-C | First-run full-library cataloguing + continuous ingestion | **TTFUV < 30s** to first value, **< 2 min** to a basic Visual Library; incremental ingest without periodic full rescan | `FIRST_RUN_LIBRARY_ORGANIZATION_EVAL.md`, `CONTINUOUS_INGESTION_EVAL.md` |
| T2-D | Full Structure-First home + retrieval paths | 11 top-level entries, drill-down, one Asset reachable from many entries with no copies; task success/steps/time on a real library | `VISUAL_LIBRARY_HOME_PROTOTYPE.md`, `RETRIEVAL_PATHS_EVAL_FULL.md` |
| T2-E | Multi-Signal Classification | Ablation proves which signals actually add accuracy; every classification emits category + confidence + evidence | `MULTI_SIGNAL_CLASSIFICATION_EVAL.md` |
| T2-F | Unit economics at 10k / 100k / 1M users | Gross margin and break-even hold, including the Apple cut and lifetime-purchase risk | `UNIT_ECONOMICS_MODEL.md` |
| T2-G | Global + Personal Policy learning | Review burden and wrong suggestions measurably fall after user corrections; rule source / sample count / confidence stored and resettable | `PERSONAL_POLICY_LEARNING_EVAL.md` |
| T2-GATE | | Final GO / GO WITH CONSTRAINTS / NO-GO | `FINAL_P0_GO_NO_GO_DECISION.md` |

---

## Cross-tier reporting rule
Every gate must report **Automation Ratio, Human Review Burden, Weighted Error Cost, Catastrophic Error Rate, Significant Value Loss Rate** — not just a near-zero false-positive number. Optimising only for FP=0 is an explicit anti-goal of the Constitution (§7, §20).
