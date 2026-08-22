# CONSTITUTION — CANONICAL UNDERSTANDING
Section-by-section digest of **Personal Visual Memory Engine v1.3 Product Constitution** (L1).
Created 2026-08-22 after Owner challenge. Purpose: no session may act on this project without reading this file first.

> **This digest never overrides the source.** Full text: `10_SOURCE_DOCS/_extracted_text/L1_PRODUCT_CONSTITUTION_v1.3.txt`.
> Whenever a decision touches a section below, **re-read that section in the source before acting** (PF-08).

**Motto:** *Organize first. Understand deeply. Automate by risk. Ask only when necessary.*
**v1.3 repositioning:** from "Cleaner + Search" → **"Visual Library + Risk-Aware Autonomous Management"**.

---

## THE FIVE THINGS THAT DEFINE THIS PRODUCT

Everything else serves these. If a proposal weakens any of them, it is wrong regardless of how good it sounds.

1. **§12 · The library comes back organised on first open.** The user installs, opens, and their whole library is already catalogued, risk-graded, deduplicated, with only a tiny Review Queue left. Value moment, verbatim: **『原来我的照片可以这么整齐，而且我不用自己整理。』** — *Immediate. Not a promise.*
2. **§22 · We become the entry point.** When the user wants to find anything visual, their first move is to open this product, not Apple Photos. Metric: **Retrieval Entry Share**.
3. **§5–§7 · Automation is decided by risk, and the convenience gain must not be held hostage by tiny-probability risk.** The system takes the work away; it does not hand every candidate back for review.
4. **§13 · It keeps doing it.** Every new photo runs the same pipeline, forever. Continuous Photo Hygiene.
5. **§3 · One asset, many indexes.** Never duplicate a photo to put it in two places.

---

## SECTION MAP

| § | Mandates | Tested by | Notes / traps |
|---|---|---|---|
| **1** | Camera Roll = an uncatalogued personal visual library. The problem is the *absence of a system*, not the photo count | — | Never reframe this as a storage problem |
| **2** | Pipeline: Understand → Classify → Index → Assess Risk → Decide → Clean/Protect → Remember → Retrieve → Maintain → Derive Services | T1, T2 | Order matters — see §9 |
| **3** | Visual Library Architecture: 9 index dimensions (Content, Time, Place, Person, Object, Event, Risk, Lifecycle, Equivalence). **One Asset stored once, reachable from many entries** | **T1-D** | Copying an asset to satisfy a UI category is forbidden (§23) |
| **4** | 13-category taxonomy with default risk. Rule:細分 only when it changes Browse / Risk / Lifecycle / Action | **T1-A** | 分类不是为了展示 AI 聪明 |
| **5** | `Category × Importance × Lifecycle × Confidence × Recoverability × Personal Preference → Action Policy` | **T2-A** | Category alone never decides an action |
| **6** | Risk ladder **R0 Disposable … R6 Irreplaceable** with default policy per level | **T2-A** | R4–R6: zero auto-delete |
| **7** | **The core philosophical bet.** Do not push 99% of the work back to the user to avoid any blame. Everyday mess and search time are *real costs too*. Allow occasional AI error; avoid unrecoverable loss. **"这必须通过真实用户测试验证，而不能只凭工程师假设"** | **T0-D** ← *this is why AMVP exists* | Optimise Automation Benefit vs Weighted Error Cost — **never FP=0** |
| **8** | Equivalence Margin. Near-equivalent candidates need no proof that 92 beats 91 — only that deleting the rest loses no significant value. Different expression / different action / different document page ≠ equivalent | **T2-B** | Must be gated by Risk Policy: same similarity, different action for a meme vs a family photo |
| **9** | **Cleaning and classification are one thing.** Understand → classify → *then* decide duplicate/version/same-moment/same-entity. Never similarity-first | **T1-B** | Contract pages 1–4 look alike and must not be merged; the same image downloaded 4× may be handled aggressively |
| **10** | Four retrieval paths: Browse · Timeline/Places · Intent Search · Relations | **T0-B**, T1-E, T2-D | Browse is listed first, deliberately |
| **11** | Time and Place are **first-class** indexes. Inferred place must store confidence. Trips form automatically — the user never builds a travel album | T1-D | |
| **12** | **First-run full-library cataloguing.** Not a screen of tool buttons — the system is already working. Auto-handle low-risk/high-confidence; **只有真正需要用户决定的内容进入极小 Review Queue** | **T0-B (concept)**, T2-C (engine) | "極小 Review Queue" is a product requirement, not an aspiration |
| **13** | **Continuous Photo Hygiene** — every new asset repeats the whole pipeline. 只有必要时才打扰用户 | **T0-D (concept)**, T2-C | |
| **14** | Global Default Policy → **Personal Policy** learned from Keep/Delete/Protect/Restore/Correction | **T2-G** | Goal is not one shared right answer, it is learning this user |
| **15** | Derived services (Wardrobe, Travel, People, Purchase & Warranty, Home/Object, Document Memory, Reminders) **must derive from existing data** | Post-P0 | Never ask the user to re-enter anything |
| **16** | **Boundary.** No unrequested inference about personality, health, politics, religion or intimate relationships | Always | Hard ethical line. **DEC-020 draws the line precisely for the one case that came up:** classifying an explicit medical *document* is allowed; inferring a health *state* from it is not. Documents, never diagnoses — see `OPERATING_RULES.md` P-08 |
| **17** | Phase 1 is **Autonomous Photo Organizer / Visual Library Manager**, NOT an AI Photo Cleaner. Classification = skeleton · Risk-Aware Decision Engine = basis of autonomy · Cleaner = internal capability · Search = retrieval · Continuous Hygiene = retention | Everything | Cleaner is a *capability*, never the positioning |
| **18** | KPIs: **Automation Ratio · Human Review Burden · Weighted Error Cost · Catastrophic Error Rate · Classification Coverage · Retrieval Success · Continuous Hygiene Rate · Personalization Gain** | Every gate | Report together, never FP alone |
| **19** | Names 9 additional P0 validation items | Allocated across T1/T2 by the Execution Index — **DEC-003** | Not a licence to build in Tier 0 |
| **20** | Final philosophy: act like a real librarian — bold on low-risk/recoverable/near-equivalent, careful on high-risk/irreplaceable, learn the user over time | Everything | |
| **21** | One-line strategy: turn the Camera Roll into a self-cataloguing, self-maintaining personal visual library | — | |
| **22** | **Retrieval Entry Strategy.** Apple keeps Capture and Storage; we take Management, Browsing and Finding. North star: their first instinct is to open us. New KPI **Retrieval Entry Share** | **T0-B** | We are the Intelligence + Management + Retrieval layer over the system library |
| **23** | **Structure First, Photos Second.** Home = a catalogue, not another infinite scroll. 11 top-level entries; drill down; one asset reachable from many entries **without copying the original** | **T0-B**, T2-D | Must validate that real users *start here* instead of Apple Photos |
| **24** | Five gates: **G1** local hardware/thermal · **G2** no universal Same-Entity model — use category-specific resolvers · **G3** Progressive Indexing + TTFUV · **G4** must not degrade into a Cleaner · **G5** classification reliability via multi-signal | G1→**T0-A**, G2→T1-B, G3→T2-C, G4→T0-C, G5→T2-E | G2 forbids the single-magic-model approach outright |
| **25** | **Progressive Intelligence Pipeline, 8 layers:** L1 cheap signals · L2 visual understanding · L3 taxonomy · L4 category-specific entity resolution · L5 risk+lifecycle · L6 policy engine · L7 visual library views · L8 personal memory | T0-A uses **L1+L2 only** | Scope lock for the benchmark harness |
| **26** | **Monetization guardrail.** Private photos, IDs, relationships, purchases and travel must never be uploaded or abused for ad profiling. Ads are not a P0 premise and must not break Privacy-First trust | T2-F | |

---

## HARD PROHIBITIONS (from the Constitution itself)

- **No silent permanent deletion.** Aggressive handling means *recoverable* handling.
- **No auto-delete at R4–R6.** High risk stays protected even at high model confidence.
- **No asset duplication for UI convenience** (§3, §23).
- **No universal Same-Entity model** (§24 G2) — category-specific resolvers only.
- **No FP=0 as the objective** (§7, §18, §20) — that is the Cleaner failure mode this product rejects.
- **No unrequested sensitive inference** (§16). Specifically: `Documents > Medical` classifies **documents**, never health states, conditions or medications (P-08, DEC-020).
- **No cloud upload or ad profiling of private visual data** (§26).
- **No degradation into a Cleaner** (§24 G4) — Cleaner is an internal capability, never the product.

---

## HOW I GOT THIS WRONG ON 2026-08-22 (read this before repeating it)

I merged **§12 (first-run cataloguing — immediate)** with **§13 (continuous hygiene — gradual)**, concluded the product's value "accrues over weeks", and inferred it might be harder to sell than a competitor. §12 states the first-run outcome and names its value moment explicitly. I had read it and did not internalise it.

Compounding error: I let a competitor whose failure cause is recorded as **UNKNOWN-1** outrank a Level 1 document.

**Binding rule (PF-08):** competitor evidence with an unknown causal mechanism may inform **how we test**, never **what we build**. Any conclusion that contradicts a Constitution section is a **finding to escalate to the Owner**, not a change to apply.

## Reading order for a new session
`PROJECT_STATE.md` → `SESSION_HANDOFF.md` → **this file** → `OPERATING_RULES.md` → `VALIDATION_MATRIX.md`.
Open the Constitution source itself whenever a decision touches a specific section.
