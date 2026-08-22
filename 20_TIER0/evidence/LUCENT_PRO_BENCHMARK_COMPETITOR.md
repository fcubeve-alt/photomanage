# LUCENT PRO — BENCHMARK COMPETITOR No.1
Deep analysis. Supersedes the Lucent section of `COMPETITOR_PRICING_MATRIX.md`.
Created 2026-08-22 · Session 001 · Triggered by Owner's independent research, verified against the archived App Store page (`raw/page_LucentPro.html`, retrieved 2026-08-22)

---

# PART 0 — CORRECTIONS TO MY EARLIER REPORT

| # | What I said | What is actually true | Why it matters |
|---|---|---|---|
| **X-1** | "**0 ratings**" | The iTunes API returns `userRatingCount: 0`, but that means **too few ratings for Apple to display an overview**, not literally zero. US, FR, ES, DE storefronts all show "not enough ratings". | "Zero" overstates the evidence. Correct phrasing: **rating volume too low for Apple to form a public overview**. |
| **X-2** | "no update in six months" — implying abandonment | Development was **dense**: v1.5 (2025-12-13), v1.6 (12-14), v1.7 (12-14), v1.8 (12-15), then **v2.0 (2026-02-04)**. Quiet since February. | "Shipped fast, then went quiet after v2" is a different story from "shipped once and died". |
| **X-3** | Implicitly treated the empty rung as near-evidence of an opening | Owner is right: it cannot distinguish weak demand from weak distribution. | Already logged as UNKNOWN-1; this file hardens it. |
| **X-4** | — | **A pricing string on the Lucent page — "$1.99 per week or $9.99 per year… export without watermarks" — belongs to a *recommended* app ("STP Swipeable panorama & grid"), not to Lucent.** Caught while verifying. | Attributing it to Lucent would have corrupted the pricing analysis. Recorded so no future session re-scrapes and re-introduces it. |

---

# PART 1 — FACT (verified from the archived page)

**Identity.** Individual developer Allan Smeyatsky. ~261.7 MB. iOS 16+. iPhone and iPad. Privacy label: Data Not Collected. All AI analysis on-device, no upload, no external servers.

**Shipped capability (v2.0):** natural-language photo search · 200+ AI-generated smart collections · duplicate/similar detection · photo map · face & object recognition · OCR · voice search · iCloud library support · Timeline view · Quality Scores.

**Version history — verbatim release notes:**

| Version | Date | Notes (quoted) |
|---|---|---|
| 1.5 | 2025-12-13 | — |
| 1.6 | 2025-12-14 | *"All photos in the library were showing instead of the 1000 freemium limit. All photos were being analysed instead of the 1000 only from freemium limit. I also removed the debug panel"* |
| 1.7 | 2025-12-14 | *"Enhanced AI analysis startup — analysis now begins automatically after setup"* |
| 1.8 | 2025-12-15 | *"Enhanced PhotoKit initialization timing to ensure smoother and more reliable photo library access… These updates address critical issues that were affecting app reliability, particularly for users experiencing problems with **photo loading on startup** and freemium usage limits"* |
| 2.0 | 2026-02-04 | NL search · Timeline View · Duplicate Detection · Quality Scores. *"Try everything free for 7 days. After that, keep **1,000 analyzed photos** at no cost, or upgrade to Premium for unlimited access to your full library."* |

**Monetisation.** Exactly two IAPs, both labelled "Lucent Pro": **$29.99** and **$2.99**. Free tier = 7-day full trial, then a **1,000-analysed-photo cap**.
**UNKNOWN-5:** the App Store page gives no period for either SKU. **$29.99 is not confirmed to be lifetime.** Do not assert it.

**Market signal.** Rating volume below Apple's display threshold in every storefront checked. No press, no reviews, no third-party coverage found.

---

# PART 2 — WHAT LUCENT PROVES *FOR* US

**P-1 · The on-device route is settled, and it is small.**
A full on-device stack — NL search, OCR, object and face recognition, embeddings, smart collections — ships in **262 MB**, built by one person. Queryable does comparable search in 206 MB.
**This closes the question `OPERATING_RULES.md` P-04 was holding open.** There is now a shipped existence proof that a 2 GB+ model dependency is not required. Apple-native + lightweight embedding stays the default route to test first, and the bar for adding a heavy model is correspondingly higher: it must beat a demonstrated 262 MB baseline, not merely work.
*Scope limit (E-14): this proves feasibility of shipping, not throughput, thermals or 100k scaling. It does not substitute for T0-A.*

**P-2 · Their bug list is free engineering intelligence — and it points exactly where we aimed.**
v1.6/1.7/1.8 were spent fixing: PhotoKit initialisation timing, photo loading on startup, analysis auto-start, and quota state entangled with analysis state. A solo developer who had already solved the AI part spent three consecutive releases on **library plumbing**.
That is direct external corroboration that Tier 0-A is aimed at the right target: the hard part is not "can the model recognise the picture", it is first-launch behaviour on a large library, PhotoKit reliability, resumption, and index state surviving restart. These are now explicit T0-A test cases.

**P-3 · Capability parity is not a market position.**
Lucent has the feature list and no traction. Whatever the cause, the safe read is that **shipping this capability set is necessary and not sufficient.**

---

# PART 3 — HOW WE ACTUALLY DIFFER

> **CORRECTED 2026-08-22 after Owner challenge.** An earlier version of this section claimed our differentiators "accrue over weeks" and were therefore hard to demo. **That was wrong**, and it contradicted Constitution §12, which I had already read. The Owner was right. The error and its correction are recorded in DEC-012.

## 3.0 The product has TWO organisation layers, not one

This is the distinction the earlier analysis destroyed by merging:

| Layer | What it is | When the user feels it |
|---|---|---|
| **基础整理 — first-run full-library cataloguing** | On first open, the entire library is already catalogued into a library-style hierarchy; expired temporary content is cleared; duplicates are cleared | **Immediately. The first time they open the app.** Constitution §12 |
| **持续整理 — continuous hygiene** | Every new photo from then on is auto-filed through the same pipeline | Over weeks and months. Constitution §13 |

Constitution §12 states the first-run outcome in plain terms: scan the whole library, build the multi-dimensional index, classify, risk-grade, form the Documents / People / Screenshots / Places / Timeline / Objects views, auto-handle the low-risk high-confidence items, and leave only a very small Review Queue. And it names the resulting first-value moment directly: **『原来我的照片可以这么整齐，而且我不用自己整理。』**

So the headline differentiator is **visible in the first session by design.** It is not a promise about the future.

## 3.1 The second differentiator: the entry point itself changes

Constitution §22 sets the north star: when the user wants to find an ID, a contract, a person, a receipt, a screenshot, a piece of clothing, a trip or an object, **their first move is to open this product — not to dig through Apple Photos.** §23 makes the home screen a catalogue, not another infinite scroll: *Structure First, Photos Second.*

This is a **behavioural** difference, not a feature difference. After install, the user stops going to Apple Photos to look at their own photos and comes here instead. That is precisely what Tier 0-B measures as **Retrieval Entry Share**, and it is the single thing the whole tier exists to test.

Lucent does not compete for this. Lucent is a **tool you open to search**. We are **where your photos live**.

## 3.2 Where Lucent actually sits

| | Lucent Pro | Us |
|---|---|---|
| What the user opens it for | To *search* for a photo when they already know they want one | To *look at their photos*, full stop — the default entry |
| Home screen | AI-generated collections + timeline + map | Fixed, predictable catalogue: Documents → IDs → Passport; Purchases → Receipts; Screenshots → Chat / Shopping / Maps / Temporary |
| First-run outcome | Library gets analysed so search works | **Library comes back organised, cleaned and cleared** |
| Cleanup | Duplicate detection + Quality Score, user-driven | Expired temporary content and duplicates already handled by risk policy |
| Ongoing | New photos get analysed | New photos get classified, filed, risk-graded, lifecycle-tracked |

## 3.3 Why "200+ smart collections" is weaker than a fixed hierarchy

Two hundred auto-generated albums is **another pile to search**. The user cannot predict what exists or where a thing lives; they have to go look, which means Lucent is still a *tool*, not an *entry point*.

A fixed hierarchy is less impressive in a feature list and better in the hand, because **predictability is the feature**: the user knows before opening the app that their passport is under Documents → IDs → Passport. Predictability is what converts a tool into a destination — and a destination is what §22 is asking for.

## 3.4 What remains genuinely slow-burn (a small list, not the headline)

Being accurate in both directions: these really do take time to pay off, and they are **not** what we lead with.

- Personal Policy learning from user corrections (§14)
- Same-Entity across long time spans — the same ID card re-shot months apart (§9)
- Derived services: Wardrobe, Travel, Purchase & Warranty memory (§15)

These are follow-on value. The first-session value is §12, and it is immediate.

## 3.5 One-line positioning
**Lucent is AI that searches your photos. We are where your photos live — already sorted, already cleaned, already yours to browse.**

# PART 4 — ADJUSTMENTS TO THE PLAN

| # | Change | Where |
|---|---|---|
| **ADJ-1** | Lucent Pro promoted to **Benchmark Competitor No.1**. Tier 0-B becomes a 3-way comparison: **Apple Photos vs Lucent Pro vs our prototype.** | T0-B protocol · DEC-010 |
| **ADJ-2** | **Fair-configuration rule** (see Part 5) — competitors must be tested fully paid and fully analysed. | T0-B protocol |
| **ADJ-3** | The Tier 0-B prototype must present the **already-catalogued library** as the first screen, per Constitution §12/§23 — including a visible summary of what was organised and cleared, and how little is left for the user. This is an *implementation* of §12, not a new idea. | T0-B protocol |
| **ADJ-4** | Competitor-derived test cases added to T0-A: first-launch stall on a large library, PhotoKit init reliability, **index state recovery after app restart** (distinct from the existing checkpoint-resume test). | `T0A_DEVICE_BENCHMARK_HARNESS_SPEC.md` |
| **ADJ-5** | P-04 tightened: a heavy on-device model must now beat a **demonstrated 262 MB baseline**, not merely function. | `OPERATING_RULES.md` |
| **ADJ-6** | New failure pattern **PF-06 "Becoming another Lucent"** — capability parity mistaken for differentiation. | `FAILURE_PATTERNS.md` |
| **ADJ-7** | Log the strategic risk that our primary differentiator is **unfalsifiable until Tier 2**. | DEC-010, Part 6 below |

---

# PART 5 — THE FAIR-CONFIGURATION PROBLEM (methodological, and it would have rigged the study)

**Lucent's free tier analyses only 1,000 photos.** A test user with a 20,000-photo library running free Lucent would be using a product that has seen 5% of their library.

If we ran the 3-way study that way, we would be **testing Lucent's paywall, not Lucent's product** — and we would produce a flattering result that falls apart the moment anyone checks. That is precisely the self-serving evidence the Playbook forbids (E-13, E-14, and the counter-evidence duty in §8).

**Rule, fixed before any data is collected:**
> Every competitor in a comparative study is configured to its **best available state**: fully paid, fully permissioned, and **fully finished analysing** before the session starts. If we cannot afford or cannot achieve that state, the comparison is not run and the limitation is reported.

**Consequences:**
- **Purchase Lucent Premium — $29.99.** (The 7-day trial is not a substitute: it expires mid-study and the analysis pass must complete before the session anyway.) Small spend approval, flagged with the others.
- Lucent must complete its full-library analysis **before** each session — schedule pre-session setup time per device.
- Apple Photos gets the same treatment: full library access, indexing settled.
- **Counterbalance task order** across participants (Latin square). Three apps × six tasks is long enough that fatigue and order effects would otherwise dominate the result.
- The person running the session must not be the person who built the prototype, or must follow a fixed script verbatim.

---

# PART 6 — THE LIMIT OF WHAT TIER 0-B CAN PROVE (do not paper over this)

Tier 0-B measures **Retrieval Entry**. All six proposed tasks are find-tasks, which is correct for that question.

But our headline differentiator is **management**, and Tier 0-B **cannot test it**, because the prototype will not have risk, lifecycle, or same-entity — those are Tier 1 and Tier 2, and building them now would violate the Execution Index (DEC-003, P-01).

The Owner's sixth proposed task — *clean up 8 near-identical burst photos* — is an **Equivalence Margin** task, i.e. Tier 2-B. **Recommendation:** keep it, but invert it — have the user do it **manually in each app** and measure the effort. That measures the *pain* our differentiator would remove, without us building the solution early. It yields a baseline number we can beat later, and it stays inside Tier 0.

**Therefore, recorded honestly:** a Tier 0-B PASS proves users prefer our **structure and retrieval**. It does **not** prove they want autonomous management, and it does not prove they will pay for it. Those remain open until Tier 2-A/C and the T0-C2 payment signal. Anyone reading `TIER0_GO_NO_GO.md` must not over-read a B PASS.

---

# PART 7 — VERDICT

| Question | Answer |
|---|---|
| Real product? | Yes — shipped, functional, actively developed through v2.0 |
| Does it validate our technical route? | **Yes, strongly** — 262 MB on-device, and their bug list confirms where the hard parts are |
| Does it cover our full direction? | No — no risk model, no lifecycle, no same-entity, no personal policy |
| Does it prove the market is dead? | **No.** Cannot separate weak demand from weak distribution (UNKNOWN-1) |
| Does it prove search + collections is insufficient? | **Probably — and this is the strongest warning available to us** |
| Benchmark Competitor No.1? | Yes |
| Reason to stop? | **No** |

**The most useful thing Lucent tells us is not about Lucent. It is that a complete, private, on-device AI photo product can exist and still not matter.** Our answer to that is not more capability — Lucent had capability. It is that we are not selling the same thing. Lucent analysed the library so the user could search it. We hand the library back **already organised, already cleaned**, and become the place the user goes to look at their photos. That is §12 plus §22, and it is visible on first open.

## Sources
Archived App Store page `raw/page_LucentPro.html` and `raw/itunes_LucentPro.json`, both retrieved 2026-08-22. Version history and release notes quoted verbatim from that page. Owner's independent research (2026-08-22), verified against the same archive.
