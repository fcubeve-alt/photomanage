# COMPETITOR PRICING MATRIX
**Tier 0-C1 deliverable** · P0 Kill Test Tier 0 v1.1 §4
Retrieved: **2026-08-22** · Storefront: **US** · Method: Apple iTunes Lookup API + App Store product pages
Raw evidence: `20_TIER0/evidence/raw/` (`itunes_*.json`, `page_*.html`, `iap_extracted.json`)
Format follows Playbook E-13 — **FACT / INTERPRETATION / RECOMMENDATION are kept separate.** UNKNOWN stays UNKNOWN (F-09).

---

# PART 1 — FACT

Every figure below was read from the Apple US storefront on 2026-08-22. Confidence **HIGH** unless stated.

## 1.1 Core matrix

| App | Developer | Install price | Rating | # ratings | First release | Last update | Size |
|---|---|---|---|---|---|---|---|
| Cleanup: Phone Storage Cleaner | DEEP FLOW SOFTWARE | Free | 4.66 | **701,832** | 2020-12-05 | 2026-08-12 | 176 MB |
| Cleaner Guru: Clean Up Storage | GM UniverseApps | Free | 4.52 | 148,583 | 2019-11-06 | 2026-08-06 | 169 MB |
| Cleaner Neat: Clean Up Storage | Smart Tool Studio | Free | 4.58 | 113,611 | 2019-08-17 | 2026-08-16 | 179 MB |
| Swipewipe: Photo Cleaner | MWM | Free | 4.69 | 88,854 | 2022-03-05 | 2026-07-24 | 236 MB |
| Clever Cleaner: AI CleanUp | CleverFiles (Disk Drill) | Free | 4.78 | 80,467 | **2025-02-27** | 2026-08-17 | 116 MB |
| CleanMy®Phone | MacPaw | Free | 4.59 | 22,706 | 2017-12-15 | 2026-06-12 | 176 MB |
| Smart Cleaner: Free Up Storage | NAICOO | Free | 4.57 | 20,210 | 2023-05-05 | 2026-01-15 | 122 MB |
| Slidebox: Photo Cleaner | Slidebox LLC | Free | **4.81** | 16,411 | 2015-06-16 | 2026-08-19 | 38 MB |
| Cleansmith: Photo Cleaner | Monocraft | Free | 4.68 | 4,076 | 2014-10-07 | 2026-08-21 | 93 MB |
| Photo cleaner - Swipick | Krobe.net | Free | 4.47 | 3,425 | 2024-01-10 | 2025-07-07 | 73 MB |
| **Queryable — Photo Search** | SmashMelon | **$4.99 paid up-front** | 4.73 | **88** | 2022-12-28 | 2026-08-11 | 206 MB |
| **Lucent Pro** | Allan Smeyatsky | Free | n/a | **below display threshold** | **2025-12-12** | 2026-02-04 | 262 MB |

## 1.2 In-app purchase tiers (verbatim labels and prices)

| App | Weekly | Monthly | Yearly | Lifetime / one-off |
|---|---|---|---|---|
| Cleanup (Deep Flow) | $5.95 / $7.39 / **$7.99** / $9.99 / $11.99 | — | $29.99 | — |
| Cleaner Guru | $4.99 / $5.99 / $6.99 / $7.99 / $8.99 / $9.99 | — | — | $39.99 |
| Cleaner Neat | $1.99 / $3.99 / $6.99 | $9.99 | $29.99 / $39.99 | $39.99 / **$59.99** |
| Swipewipe | $3.99 / $4.99 / $5.99 / $7.99 / **$9.99** | — | $29.99 | — |
| Clever Cleaner | $6.99 (w/ trial) | — | — | $39.99 |
| CleanMy®Phone | — | $7.99 | $36.99 | $34.99 |
| ↳ *Gemini Photos SKUs inside the same app* | — | $2.99 / $4.99 | $19.99 / $39.99 | — |
| Smart Cleaner | $5.99 / $6.99 / $9.99 | $12.99 | $19.99 / $34.99 | $23.99 / $39.99 |
| Slidebox | $1.99 / $2.99 | — | $19.99 / $29.99 | $29.99 / $49.99 |
| **Lucent Pro** | — | — | — | **$2.99 / $29.99** — periods not stated (UNKNOWN-5) |
| **Queryable** | — | — | — | **$4.99 (up-front, no IAP block on page)** |

Annualised weekly pricing: **$3.99/wk = $207/yr · $7.99/wk = $415/yr · $11.99/wk = $623/yr.**

## 1.3 Documented market behaviour

**FACT.** MacPaw has folded **Gemini Photos** into CleanMy®Phone — Gemini SKUs still appear in CleanMy®Phone's IAP list. Gemini Photos no longer surfaces as a standalone app in US search results. *(Source: CleanMy®Phone App Store page IAP list, 2026-08-22. Confidence HIGH for the SKU bundling; MEDIUM for "discontinued as standalone", since absence from search is not proof of removal.)*

**FACT.** Clever Cleaner markets itself explicitly as *"a truly free iPhone cleaner app with no annoying ads and no mandatory subscription"*, with free daily limits, from the makers of Disk Drill. It reached **80,467 ratings in ~18 months**, the fastest accumulation in this set. *(Source: App Store description + itunes lookup.)*

**FACT.** An independent January 2025 technical teardown of seven iOS cleanup apps documented: subscription prompts gating all functionality; **Cleanup** transmitting metadata through 6+ tracking SDKs (Adjust, Firebase, Cerebro, Admost, Facebook, Unity Ads) **after** the user paid $7.99/week; privacy labels claiming data "not linked to me" while payloads carried user IDs; calendar/contacts/GPS/microphone permission requests justified as "for ad content"; Swipewipe raising its weekly price from $4.99 to $9.99 within one year; and clusters of apparently AI-generated 5-star reviews. Two of the apps ranked **#7 and #14** among top free utilities in December 2024. *(Source: Tumbleson, "Predatory iOS Cleanup Applications", 2025-01-13. Confidence HIGH — primary technical analysis with traffic captures.)*

**FACT.** Apple Support forum and review-aggregation threads record recurring complaints: users unaware that deleting the app does not cancel the subscription; charges immediately after trial; refusal of refunds by both developer and Apple; and over-aggressive cleaning that removed content users wanted to keep. *(Confidence MEDIUM — user reports, not audited.)*

**FACT.** **Queryable** states it reached #1 on the Hacker News front page, topped the paid tools chart across all European countries and ranked #2 in the US on the same day. It is open-source, fully offline, pay-once. It has **88 US ratings**. *(Source: App Store description — the ranking claims are the developer's own; confidence MEDIUM. The 88-rating figure is HIGH.)*

**FACT (CORRECTED 2026-08-22 — see `LUCENT_PRO_BENCHMARK_COMPETITOR.md`).** **Lucent Pro**: individual developer, ~261.7 MB, iOS 16+, privacy label Data Not Collected. Shipped v2.0 capability: natural-language search, 200+ AI-generated smart collections, duplicate detection, photo map, face/object recognition, OCR, voice search, iCloud support, Timeline, Quality Scores — all on-device. Version history: v1.5–1.8 shipped 2025-12-13 to 12-15, **v2.0 on 2026-02-04**, quiet since. Free tier = 7-day full trial, then a **1,000-analysed-photo cap**; two IAPs both labelled "Lucent Pro", **$29.99** and **$2.99**, **periods not stated (UNKNOWN-5 — $29.99 is NOT confirmed to be lifetime)**. Rating volume is **below Apple's threshold for displaying a public overview** in every storefront checked.

> ⚠️ **Two corrections to the first version of this file.** (1) It said "0 ratings" — the API zero means *too few to display*, not literally none. (2) It said "no update in six months", which understated a dense v1.5→v2.0 development run. (3) A pricing string on the same page — "$1.99 per week or $9.99 per year… export without watermarks" — belongs to a **recommended app**, not Lucent, and must not be attributed to it.

**FACT.** Queryable (206 MB) and Lucent Pro (262 MB) both ship on-device semantic-search capability inside a normal App Store binary.

---

# PART 2 — INTERPRETATION

Clearly separated from fact. These are readings, not measurements.

## 2.1 The Cleaner rung is commoditised and its price floor is collapsing
Ten cleaner apps, all free to install, one with **701k ratings**. Free-to-install is not a choice in this category — it is the entry requirement. Clever Cleaner then attacks the floor directly by making genuine cleaning free with no ads, and it is growing faster than anything else in the set. Anyone entering at the Cleaner rung competes against 700k-rating incumbents *and* against free.

This confirms the Constitution's premise (§24 Gate 4) and Tier 0 §4's warning that Cleaner-rung willingness-to-pay does not count as a payment signal.

## 2.2 The category's revenue comes from subscription pressure, not from product value
The dominant SKU is a **weekly** subscription of $4–12, i.e. $207–623/year for a storage utility. Lifetime options cluster at $29.99–$59.99 — roughly one to three months of the weekly price. A rational buyer would never choose weekly; weekly exists because it converts under trial-flow pressure and renews unnoticed.

Combined with the documented tracking-after-payment, permission over-reach and price doubling, the reasonable reading is that a large share of this category's revenue is extracted rather than earned. **This is a strategic opening and a strategic trap at once**: users in this category are primed to distrust subscriptions, so a subscription pitch inherits that distrust — but it also means high satisfaction is genuinely scarce, and Slidebox (4.81, oldest, simplest, smallest at 38 MB) shows what honest scores look like.

## 2.3 The Search rung monetises, but thinly
Queryable is the cleanest available experiment on the Search rung: technically excellent, offline, privacy-first, widely publicised (HN #1, top of EU paid charts), pay-once at $4.99 — and **88 US ratings** in 3.5 years. Interpretation: *Search alone is a $5 one-off feature, not a business.* It supports the Constitution's decision (§17, §24 Gate 4) to anchor paid value above Search, at Continuous Management and Visual Memory.

## 2.4 The Continuous-Management / Visual-Library rung is essentially unoccupied
> **Superseded in part.** Lucent Pro is now analysed in depth as **Benchmark Competitor No.1** — see `LUCENT_PRO_BENCHMARK_COMPETITOR.md`. It occupies the *search + collections* half of this rung but not the *risk-aware management* half. Read that file before citing this section.
Across this search, exactly one product occupies the position this project is aiming at — Lucent Pro — and it has zero traction, zero coverage and no update in six months. Every other product is a cleaner or a search tool.

**This does not establish demand.** An empty rung is equally consistent with "nobody has served it well" and with "nobody wants it". Distinguishing those two is precisely what Tier 0-B and Tier 0-C2 exist to do, and this matrix cannot settle it. See UNKNOWN-1.

## 2.5 A relevant technical read (feeds T0-A and P-04)
Two shipping apps deliver on-device natural-language photo search in 206–262 MB binaries, one of them from a single developer. **Interpretation:** the on-device semantic-search route is demonstrably shippable at ~200–260 MB, and the assumption that this class of capability requires a 2 GB+ model dependency is not supported by what is actually on the store. This is consistent with `OPERATING_RULES.md` P-04 and is an argument for testing Apple-native + lightweight-embedding first. It is **not** a substitute for T0-A: nothing here measures indexing time, thermal behaviour or 100k-library scaling.

---

# PART 3 — UNKNOWN (must not be collapsed in either direction)

| ID | Unknown | Why it matters | Resolution plan |
|---|---|---|---|
| **UNKNOWN-1** | Is Lucent Pro's zero traction a **demand** verdict or a **distribution** verdict? | It is the closest thing to a natural experiment on this project's exact positioning. Read wrongly in either direction it either falsely kills or falsely validates the product. | Evidence so far points to distribution (solo developer, no press, no marketing, no update since 2026-02-04) — but that is inference. Resolve via T0-B (do users prefer this structure at all?) and T0-C2 (will they pay?). Do **not** cite it as a market verdict in `TIER0_GO_NO_GO.md`. |
| **UNKNOWN-2** | Actual revenue and conversion rates for any app here | Rating counts are a proxy for installs, not for revenue. Whether the weekly model is highly profitable or merely noisy is unmeasured. | Third-party estimates (Appfigures/Sensor Tower) are paid. Defer — not required for the Tier 0 gate. |
| **UNKNOWN-3** | Non-US storefront pricing | Pricing power may differ materially by region. | Defer to Tier 2-F unit economics. Out of Tier 0 scope. |
| **UNKNOWN-4** | Whether Gemini Photos was formally withdrawn or merely delisted from search | Minor; affects only the MacPaw consolidation narrative. | Low priority. |
| **UNKNOWN-5** | Whether Lucent Pro's $29.99 SKU is lifetime, annual or something else | It is the closest real price point to our own proposed anchor | The App Store page does not state a period. Resolve by installing the app during T0-B setup and reading the purchase sheet. |

---

# PART 4 — RECOMMENDATION

Directed at Tier 0-C2 design. These are proposals, not decisions — pricing decisions require the Evidence Gate (Playbook §8, `OPERATING_RULES.md` P-07) and Owner sign-off.

1. **Do not test a Cleaner-rung price at all.** §2.1 settles it. Testing willingness-to-pay for cleaning would burn the one real payment experiment on a question already answered in the negative.
2. **Aim the T0-C2 landing page at the Continuous Management rung**, exactly as Tier 0 §4 requires — "your photo library stays organised by itself, every day", not "free up 12 GB".
3. **Lead with a lifetime/one-off price point around $29.99–$49.99**, which is where every credible non-predatory competitor lands (Slidebox $29.99/$49.99, Clever Cleaner $39.99, CleanMy®Phone $34.99, Lucent Pro $29.99). Weekly pricing should be excluded on trust grounds — §2.2 — and because Constitution §26 makes user trust load-bearing.
   - Counter-consideration to hand the Owner: a lifetime price cannot fund indefinite maintenance, which Tier 2-F must model explicitly. Do not resolve this here.
4. **Make privacy and honesty a visible price component.** The documented tracking-after-payment and refund complaints mean "processed on device, no tracking, cancel anytime, no weekly trap" is a differentiator with evidence behind it, not a slogan.
5. **Use Lucent Pro as the closest positioning reference when writing the landing page** — same rung, so its feature framing shows what the market has already been told — but never as proof that the rung is empty because it is unwanted (UNKNOWN-1).

---

## Coverage statement (Playbook E-14)
This matrix covers **12 apps** on the **US** storefront on **2026-08-22**, selected to span all three Value Ladder rungs plus the highest-install incumbents. It is sufficient to characterise the Cleaner and Search rungs with confidence. It is **not** a census of the App Store, contains no revenue data, and no conclusion here extends beyond the US storefront on that date.

## Status
**T0-C1 COMPLETE.** Does not by itself PASS or FAIL Tier 0-C — Tier 0 §4 requires a **real conversion signal** (T0-C2), which is blocked on HG-2.

## Sources
- Apple iTunes Lookup / Search API, US storefront, 2026-08-22 (raw JSON archived)
- App Store product pages for all 12 apps, 2026-08-22 (raw HTML archived)
- Tumbleson, C., "Predatory iOS Cleanup Applications", 2025-01-13 — https://connortumbleson.com/2025/01/13/predatory-ios-cleanup-applications/
- Apple Support Communities thread 256046421 (user complaints, unaudited)
- MacPaw CleanMy®Phone product pages — https://macpaw.com/cleanmyphone
- CleverFiles Clever Cleaner — https://www.cleverfiles.com/clever-cleaner/
