# VALIDATION MATRIX
`TEST → SUCCESS CRITERIA → MEASUREMENT → PASS/FAIL → NEXT ACTION`
Source of truth: P0 Execution Index v1.0 + Tier 0/1/2 v1.1. Status is evidence-backed only.

Legend — **WINDOWS_OK** executable now · **REQUIRES_MAC** needs macOS/Xcode · **REQUIRES_DEVICE** needs real iPhones · **REQUIRES_USERS** needs external humans · **REQUIRES_OWNER** needs Owner action/spend

---

## TIER 0 — 生死开关 (CURRENT TIER · the only authorised build surface)

### T0-A · Real-device hardware & thermal limit  `REQUIRES_DEVICE` `REQUIRES_MAC`
| | |
|---|---|
| **Test** | First-run index of 10k / 30k / 100k real assets on ≥3 iPhone tiers (entry/mid/flagship; record model + iOS version). Layer 1 (metadata/time/GPS/hash/basic OCR) + Layer 2 (lightweight visual embedding) **only** — not the full 8-layer pipeline. Also verify PhotoKit full vs limited authorisation, deletion boundaries, change observer, and iCloud-only asset original/thumbnail request behaviour. |
| **Success criteria** | 100k first index completes in a reasonable wall time without thermal throttling or an unrecoverable background kill, **and** supports incremental update (no full rescan each run), **and** resumes from checkpoint after interruption. |
| **Measurement** | Wall time, peak memory, CPU %, thermal state (`ProcessInfo.thermalState`), battery drain %, index size on disk, checkpoint-resume success — per library size × device tier. Output: `DEVICE_BENCHMARK_TIER0.csv` + `.md`. |
| **Status** | **BLOCKED — NOT TESTED.** No Mac, no Xcode, no instrumented iPhones. No simulated result may be reported as a PASS. |
| **Next action** | Windows-side: derive the per-asset compute budget the device must hit, and write the benchmark harness spec + exact metric list so the on-device run is one working session once hardware exists. Escalated as **HG-3**. |

### T0-B · Retrieval Entry hypothesis  `REQUIRES_USERS` `REQUIRES_MAC`
| | |
|---|---|
| **Test** | Minimal Structure-First home skeleton (6 entries: Documents / People / Screenshots / Places / Timeline / Objects). Real **external** users (not the team) perform the same tasks — find ID card, find one person from one trip, find a receipt, find a screenshot — in **native Apple Photos** vs **this prototype**. |
| **Success criteria** | Under blind/semi-blind conditions, a **majority** of test users explicitly state the prototype is better and that they would rather use it as their first stop for finding photos. |
| **Measurement** | Per task: success rate, step count, time-to-find. Plus subjective forced choice, plus a structured list of concrete complaints about native Photos (turning "feeling" into failure cases). Output: `RETRIEVAL_ENTRY_USABILITY_TIER0.md`. |
| **Status** | **BLOCKED — NOT TESTED.** Prototype needs iOS; study needs recruited external users. |
| **Next action** | Windows-side: author the full test protocol (task set, standard test-library definition, scripting, scoring sheet, anti-bias rules) so the study is runnable the day the prototype exists. Escalated as **HG-4**. |

### T0-C1 · Competitor pricing matrix  `WINDOWS_OK`
| | |
|---|---|
| **Test** | Build the competitor pricing matrix required by Tier 0 §4 / original §9: CleanMyPhone, Clever Cleaner, Slidebox, Queryable, Lucent Pro and other relevant products. |
| **Success criteria** | For each competitor: free tier, price points and model (subscription / one-off / lifetime), rating and rating count, last update, and structured user complaints about subscriptions. Enough coverage to state which Value Ladder rung the market already prices at zero. |
| **Measurement** | `20_TIER0/evidence/COMPETITOR_PRICING_MATRIX.md`, each cell carrying source + retrieval date + confidence, with FACT / INTERPRETATION / RECOMMENDATION kept separate (Playbook E-13). UNKNOWN stays UNKNOWN (F-09). |
| **Status** | **IN PROGRESS — this session.** |
| **Next action** | Execute now. Highest-priority unblocked Tier-0 deliverable. |

### T0-C2 · Real payment signal  `REQUIRES_OWNER`
| | |
|---|---|
| **Test** | Obtain a **real** conversion signal by one of: waitlist + deposit (even a few dollars); tiny paid TestFlight beta; or landing page with a real price where the click reaches the step immediately before charging. Surveys are explicitly rejected as evidence. |
| **Success criteria** | Real intent-to-pay at the **Continuous Automatic Management** rung or above. Cleaner-rung willingness does not count — that market is already trained to free. |
| **Measurement** | Traffic, click-through to price, reach-checkout rate, deposits collected. Output: `REAL_PAYMENT_SIGNAL_TIER0.md`. |
| **Status** | **BLOCKED.** Requires domain/landing page, payment processing and spend → **HG-2**. |
| **Next action** | Windows-side: draft the landing-page value-ladder copy and measurement plan derived from T0-C1 findings, ready for Owner approval and launch. |

### T0-GATE · Tier 0 decision
| | |
|---|---|
| **Rule** | A or B FAIL → **NO-GO / PIVOT**, stop. · A+B PASS and C PASS → **Tier 1**. · A+B PASS but C FAIL → **TECHNICAL/PRODUCT GO + COMMERCIAL PIVOT**: fix the commercial model and retest before heavy investment. |
| **Deliverable** | `TIER0_GO_NO_GO.md` — mandatory before any Tier 1 work begins. |
| **Status** | NOT REACHED. |

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
