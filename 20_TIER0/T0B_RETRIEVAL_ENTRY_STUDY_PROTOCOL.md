# T0-B · RETRIEVAL ENTRY STUDY PROTOCOL
**Windows-side preparation for Tier 0-B.** Status of Tier 0-B itself: `REQUIRES_USERS` `REQUIRES_MAC` — **NOT RUN.**
Purpose: make the study runnable the day a prototype and participants exist, with every criterion fixed in advance so the result cannot be argued afterwards.
Created 2026-08-22 · Session 001 · Design authority: Constitution §12, §22, §23 · Tier 0 v1.1 §3 · DEC-011, DEC-012, **DEC-013**

---

## 1. The question this study answers

Tier 0 v1.1 §3, PASS bar, verbatim:

> 在盲测/半盲测条件下，多数测试用户明确表示本产品原型比苹果原生更好用、更愿意作为找照片的第一入口。

The north star behind it (Constitution §22): **when the user wants to find something visual, their first move is to open this product — not to dig through Apple Photos.** The metric is **Retrieval Entry Share**.

### What we are actually showing them

Not a search box, and **not a dashboard** (DEC-017). Per Constitution §12 and §23, the participant opens the app and gets **two immediate values at once**:

1. **A catalogued library they can browse right now** — a stable, predictable hierarchy that drills down through second and third levels. This takes the prime real estate.
2. **Evidence the system already did the work** — compressed into a three-line header (*N analysed · N organised or handled · only 23 need your attention*), with the detail below the library.

*Structure First, Photos Second.* Photos appear only once the participant has arrived somewhere specific.

Two things are therefore under test, both visible on first open:
- **B-1 · The first-open moment.** Does "my library is already organised and I did nothing" land?
- **B-2 · Retrieval Entry.** When they need to find something, is this where they would rather start?

## 2. What this study cannot prove — fixed before data collection

Per DEC-012. Anyone reading the result must carry this:

| Provable here | NOT provable here |
|---|---|
| Users prefer (or do not prefer) an organised-library entry point over Apple Photos | That our engine can actually produce that catalogue reliably at scale — **Tier 1** |
| The first-open organised moment lands (or does not) | That risk-aware automation is safe and wanted — **Tier 2** |
| Concrete, structured failure cases in native Photos | That users will pay — **T0-C2** |

The Tier 0 document requires only a *Structure First skeleton*. **The prototype's catalogue is therefore prepared by hand for the test library** — legitimate, because this tier tests the interface concept, not the classifier. **This must be disclosed in the report as the study's principal limitation** (see §9 L-1).

---

## 3. Two-arm design (DEC-013 — supersedes the three-way design in DEC-010)

**Owner decision 2026-08-22: Lucent Pro is not to be purchased or installed.** The study returns to the comparison Tier 0 v1.1 §3 specifies.

| Arm | What it is | Configuration |
|---|---|---|
| **A · Apple Photos** | The incumbent and the default entry today — the baseline §22 names | Native, full library access, People identified, indexing settled |
| **B · Our prototype** | Structure First catalogued library **with real drill-down** | **11 top-level entries** per Constitution §23 (Documents / People / Screenshots / Places / Travel / Objects / Purchases / Clothing / Work / Downloads / Timeline), each opening into second and third levels — e.g. `Documents › Identity › Passports`. **Not a set of flat count tiles** (DEC-017). Built: `study_assets/prototype/`, 82 pages |

Lucent remains a **documentary reference** (`evidence/LUCENT_PRO_BENCHMARK_COMPETITOR.md`) for what the AI-search position looks like. It is not an arm, and its absence removes the $29.99 spend and the pre-session analysis wall-time.

### 3.1 Fair-configuration rule — still binding (PF-07)
> Any competitor that *is* included in a comparative study is tested **fully permissioned and fully finished indexing** before the session. If that state cannot be reached, the comparison is not run and the limitation is reported.

With Lucent removed this now applies to **Apple Photos**, and it matters: an Apple Photos instance that has not finished indexing People, or lacks full library authorisation, would hand us a rigged win. **Verify and record per session.**

---

## 4. Two-part study

### PART 1 — Standardised library, loaner device (both arms)
Controls content across participants so task times are comparable, and is the only way arm B can exist before the engine does.

- One prepared library of **8,000–12,000 assets** on a loaner iPhone, with documented ground truth.
- Participant is briefed on a persona: *"These are your photos. You are the person in them."* Give them **3 minutes** to browse freely before any task, so they are not searching a stranger's life cold.
- Both arms on the same device with the same library.

### PART 2 — Participant's own library (arm A only)
Our prototype cannot participate — no engine, so we cannot organise a stranger's library. Say so plainly.

- Same task *types*, run against their own photos on their own phone, in Apple Photos.
- This is where the **real** pain and the **real** failure cases come from, and it produces the structured complaint list Tier 0 §3 explicitly asks for: *把「感觉」变成结构化的失败案例清单*.
- Those failure cases feed directly into our taxonomy granularity and UI design.

**Why both.** Part 1 gives comparability and lets our prototype exist at all before the engine does. Part 2 gives ecological validity and the complaint inventory. Neither alone is sufficient.

---

## 5. Test library specification (Part 1)

Composition must approximate a real camera roll, not a curated demo. Target distribution:

| Content class | Share | Must include |
|---|---|---|
| Ordinary photography (scenery, food, street) | ~35% | — |
| Screenshots | ~25% | chat, shopping, maps, web, **expired verification codes / pickup codes**, error screens |
| People & family | ~15% | at least 4 recurring identities, one appearing across multiple years |
| Bursts / same-moment groups | ~8% | **≥3 groups of 6–10 near-identical frames**, incl. one with a meaningfully different expression (hard negative) |
| Documents & IDs | ~6% | ID card **front and back**, passport, driver licence, a **multi-page contract (4 pages)** |
| Purchases | ~5% | receipts, order confirmations, a warranty card |
| Downloaded / memes | ~4% | including **one image downloaded 4 times identically** |
| Objects | ~2% | **the same object photographed on 3 separate occasions** |

Required ground-truth annotations: for every target asset — its true category path, capture date, place, people present, and its same-entity / same-moment group id.

**Deliberate hard negatives** (these decide whether the structure is real or just pretty):
- Contract pages 1–4 look near-identical but are different content → must not be treated as duplicates.
- One burst contains a genuinely different expression → must not be silently collapsed.
- ID front and back are the same entity but both must remain findable.

---

## 6. Tasks

Six retrieval tasks (Owner-specified), plus one inverted effort task.

| # | Task | Measures |
|---|---|---|
| T1 | Find the **front and back** of the ID card | Document structure; entity grouping |
| T2 | Find the photo of the person in the white top from last year's Tokyo trip | Person × place × time × attribute |
| T3 | Find the receipt for a specific purchase | Purchase structure |
| T4 | Find all photos of one person over the last three years | Person over time |
| T5 | Find the same object photographed on different occasions | Same-entity across time |
| T6 | Find a specific screenshot (a pickup code from a given week) | Screenshot sub-classification + lifecycle |

### 6.1 T7 — the inverted burst task (DEC-011)
> Clean up a group of 8 near-identical burst photos, keeping the best one.

**The participant does this manually in each arm.** We are **not** building Equivalence Margin selection — that is Tier 2-B and building it now would violate the Execution Index. We measure the **effort it costs today**: time, taps, and whether they end up confident they kept the right one. That produces the baseline our differentiator must later beat, and it stays entirely inside Tier 0.

### 6.2 Per-task measurement
- **Success** — found / found-wrong / gave up (cap at **3 minutes**, then record as gave-up)
- **Time to find** (seconds)
- **Step count** (taps/screens)
- **Backtracks** (returning to home or restarting the approach) — the clearest signal that structure was unpredictable
- **Verbatim quote** whenever the participant expresses frustration or surprise

---

## 7. First-open measurement (B-1)

Run **before** any task, once per arm, in the arm's assigned order.

1. Hand over the phone with the app **not yet opened**.
2. *"Open this app and tell me what you see. Talk out loud."*
3. Record: **time to first meaningful reaction**, unprompted use of organisation vocabulary (sorted / tidy / categories / it did this for me), and whether they ask *"did it do this by itself?"* — that question is the §12 moment landing.
4. Then: *"Without tapping anything, where would you expect to find your passport?"* Record their answer, then whether their guess was **correct**.

**Step 4 is the sharpest single measurement in this study.** It tests *predictability* — the property that separates a destination from a tool (Lucent analysis §3.3). A user who can correctly predict where a thing lives before touching the screen has an entry point. One who cannot has another app to search.

---

## 8. PASS criteria — fixed in advance

| Criterion | Threshold |
|---|---|
| **P-1 Preference (primary)** | **≥ 70%** of participants name our prototype as where they would rather start looking for something, in a forced choice between the two arms |
| **P-2 Reasoned preference** | Of those choosing our prototype, **≥ 70%** cite a **structural** reason (predictable categories, already organised, know where things are) rather than novelty or aesthetics. Coded blind by two coders |
| **P-3 Task performance** | Arm B beats arm A on **median time** and **median steps** on **≥ 4 of 6** retrieval tasks |
| **P-4** *(retired — DEC-013 removed the Lucent arm)* | — |
| **P-5 Predictability** | **≥ 60%** correct at level 1 **and ≥ 40%** correct at every level (full path) before tapping |
| **P-6 First-open moment** | **≥ 50%** spontaneously remark on the library being organised, without prompting |

**Overall:** PASS requires **P-1 and P-3**. GO WITH CONSTRAINTS if P-1 passes but P-3 fails. **FAIL** if P-1 fails — and per Tier 0 §3, a B FAIL is a **NO-GO / PIVOT**, not a prompt to add features.

**Sample size:** **n ≥ 10** external participants. Not team members, not friends who know the project. Recruit for mixed ages and mixed photo-library sizes; record library size per participant.

---

## 9. Anti-bias rules

| ID | Rule | Why |
|---|---|---|
| **AB-1** | **Counterbalance arm order** across participants (half A-then-B, half B-then-A). | Two arms × seven tasks is still long enough for order and fatigue effects to matter. |
| **AB-2** | The facilitator is **not** the prototype's author, or reads a **fixed script verbatim**. | Unconscious steering is the default failure of founder-run usability tests. |
| **AB-3** | Arms are introduced **neutrally** — "app 1 / app 2". No branding, no "ours". | Semi-blind per Tier 0 §3. |
| **AB-4** | Never ask "which is better?" Ask **"if you needed to find a photo tomorrow, which would you open first?"** | Preference is cheap; predicted behaviour is the actual metric. |
| **AB-5** | Fair-configuration rule (§3.1) verified and **recorded per session** — Apple Photos fully authorised, People identified, indexing complete. | PF-07. A rigged win is worse than a loss. |
| **AB-6** | Record **every** gave-up and every failure **in arm B** with equal prominence. Counter-evidence is sought, not tolerated. | Playbook §8. |
| **AB-7** | Pre-register §8 thresholds before the first session; **no post-hoc threshold changes**. | Otherwise the criteria drift to meet the data. |
| **AB-8** | Report the prepared-catalogue limitation (**L-1**) in the summary, not a footnote. | See below. |

### Known limitations, to be stated in the report
- **L-1 · Prepared catalogue and hand-authored taxonomy.** Arm B's organisation *and* its category tree are hand-made for the test library. It demonstrates the *concept*, not the *engine*, and not that a classifier could produce this tree. A PASS means the interface concept works if the engine can be built — which Tier 1 must prove independently.
- **L-5 · `Documents › Medical` is unresolved (OPEN-1).** Rendered as "pending decision" and excluded from every task, pending an Owner ruling against Constitution §16.
- **L-2 · Persona library.** In Part 1 the participant is navigating someone else's life. Mitigated by the 3-minute browse and by Part 2, but time-to-find is inflated across all three arms equally.
- **L-3 · Novelty.** Arm B is unfamiliar; both novelty inflation and unfamiliarity penalty are possible. P-2 (reasoned preference) exists to detect the former.

---

## 10. Deliverable

`20_TIER0/evidence/RETRIEVAL_ENTRY_USABILITY_TIER0.md` containing:
1. Participant table — n, ages, library sizes, device, arm order assignment
2. Fair-configuration verification per session
3. Per-task table — success / time / steps / backtracks, per arm
4. First-open results (§7), incl. passport-prediction accuracy
5. Forced-choice preference + blind-coded reasons (P-1, P-2)
6. **Structured failure-case inventory for Apple Photos** — from Part 2, the deliverable Tier 0 §3 explicitly asks for
7. Verbatim quotes, including every negative one about arm B
8. PASS / GO WITH CONSTRAINTS / FAIL against §8, with L-1…L-3 stated in the summary

## 10A. Prototype build

`20_TIER0/study_assets/prototype/` — 82 pages, generated by `build_prototype.py`. Home, every taxonomy node to leaf level, and the four T0-D header variants of the same home.

Regenerate rather than hand-edit; counts and structure are defined in one place in the script. The four T0-D variants differ **only** in the header and work-report treatment — the library below is byte-identical across them, which is what keeps the between-subjects manipulation clean.

## 11. Companion study
**T0-D Autonomous Management Value Proposition** runs with the same participants, **after** this study, on separate instruments. Its results are recorded in a separate deliverable and **neither study may substitute for the other** (Owner instruction, DEC-014). See `T0D_AUTONOMOUS_MANAGEMENT_VALUE_PROP_PROTOCOL.md`.

## 12. Dependencies
| Need | Gate |
|---|---|
| Prototype built and delivered to a device | **HG-1 + HG-2a** (same Mac/TestFlight environment as T0-A) |
| ≥10 external participants recruited | **HG-4** |
| Loaner iPhone + prepared 8–12k test library | Owner fleet — one device set aside, library prepared per §5 |

**Windows-executable next steps, no gate required:** build the test-library specification into a concrete asset manifest and generate the synthetic portion; write the facilitator script and the scoring sheet as fillable files.
