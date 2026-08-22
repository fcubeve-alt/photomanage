# T0-A · MAC ENVIRONMENT & DEVICE GRADIENT PLAN
**Owner approved HG-3 in principle on 2026-08-22: cloud Mac only, no Mac purchase, existing iPhones, approval required before any actual payment.**
This document is the pre-payment report. **Nothing here has been purchased. No account has been created. No payment has been made.**
Created 2026-08-22 · Session 001

---

# PART 1 — THE BLOCKER IS NARROWER THAN IT LOOKED

With ~6 iPhones spanning iPhone 7 → iPhone 17 already in hand, Tier 0-A is missing exactly one thing: **a machine that can run Xcode and sign an iOS build.**

But there is a second, non-obvious blocker that the cloud-Mac decision exposes:

> **A cloud Mac cannot have an iPhone plugged into it.**

Normal iOS development installs a build over USB. That is impossible when the Mac is in a datacentre in France. So the plan must solve *delivery to device*, not just *build*. That is what drives most of the cost below — not the Mac itself, which turns out to be nearly free.

---

# PART 2 — FACT: what was verified (2026-08-22)

| # | Fact | Source | Confidence |
|---|---|---|---|
| F1 | Scaleway Mac mini M1 — **€0.11/hr or €75/month**, M1 8C CPU / 16-core Neural Engine, 8 GB RAM, 256 GB SSD, dedicated hardware, no hypervisor | scaleway.com/en/pricing/apple-silicon/ | HIGH |
| F2 | Scaleway M2 **€0.17/hr / €115 mo** (16 GB) · M2 Pro **€0.21/hr / €139 mo** · M4-S **€0.22/hr / €149 mo** · M4 Pro **€0.49/hr / €335 mo** | same | HIGH |
| F3 | Apple's licence terms impose a **24-hour minimum lease** on Apple-silicon-as-a-service | Scaleway docs / press | MEDIUM — confirm at checkout |
| F4 | **Apple Developer Program = 99 USD/year.** Requires an Apple Account with 2FA, legal name as App Store seller, and payment by the enrollee's own credit card — otherwise government photo ID is requested | developer.apple.com/support/enrollment/ | HIGH |
| F5 | **TestFlight requires iOS 16 or later** — verbatim: *"iPhone or iPad running iOS 16 or iPadOS 16 or later."* | testflight.apple.com | HIGH |
| F6 | **iPhone 7 maxes out at iOS 15.8.x** and cannot run iOS 16 | Apple device support / multiple | HIGH |
| F7 | **iPhone 7 (A10 Fusion) has no Neural Engine.** The ANE first shipped in A11 (iPhone 8 / X) | hollance/neural-engine device table; Apple silicon history | HIGH |

## F5 + F6 + F7 combine into a decisive conclusion

**The iPhone 7 cannot receive a TestFlight build at all** (F5 ∧ F6), **and** it has no Neural Engine to run Core ML on (F7), **and** targeting it would force the whole app to a deployment target of iOS 15, cutting off every Vision and Core ML API added since.

**RECOMMENDATION:** drop the iPhone 7 from the Tier 0-A campaign entirely. This is not a compromise of the Owner's instruction — the Owner already said iPhone 7 is a boundary reference and that core capability must not be sacrificed for it. The evidence now shows it would cost three separate compromises (delivery path, deployment target, ANE-less execution) to obtain one boundary datapoint. If that datapoint is ever genuinely wanted, it can be taken later via a separate Windows-side sideload path (Part 6), independent of this gate.

---

# PART 3 — DELIVERY PATH (this is the real decision)

| Path | How the app reaches the phones | Cost | Verdict |
|---|---|---|---|
| **A · Cloud Mac → TestFlight** | Build & archive on cloud Mac → upload to App Store Connect → install over the air on every iPhone | Mac ~€3 + **$99/yr Apple Developer** | ✅ **RECOMMENDED.** Only path that scales to 5 devices and repeated runs. The $99 is needed to ship anyway. |
| **B · Cloud Mac → .ipa → sideload from Windows** | Build on cloud Mac → download .ipa to the Windows box → sideload with a free Apple ID via an AltStore/SideStore-type tool | Mac ~€3, **no $99** | ⚠️ Fallback only. Free-Apple-ID profiles expire in **7 days** and must be re-installed per device; unofficial tooling; fragile across 5 devices. Viable to prove the harness works before committing $99. |
| **C · Local Mac** | USB | Mac purchase | ❌ Excluded by Owner. |
| **D · Xcode Cloud / GitHub macOS runners** | CI build only | — | ❌ Cannot attach a physical iPhone; still needs TestFlight to deliver, so it does not avoid the $99. |

**Path A is the recommendation. Path B exists specifically so the harness can be validated on one device before any $99 commitment**, if the Owner prefers to spend €3 before spending $99.

---

# PART 4 — COST (nothing purchased; approval requested)

## Minimum realistic cost to a first real-device benchmark

| Item | Cost | When approval is needed |
|---|---|---|
| Scaleway Mac mini **M1**, one 24-hour block | 24 × €0.11 = **€2.64** (~$3) | **Now** — the only thing being asked for today |
| Apple Developer Program, individual, annual | **$99 USD** | **Deferred until after a successful compile** (DEC-015). Also triggers **HG-1** (identity/KYC) |
| **Total, first round** | **≈ $102**, but committed in two steps rather than one | |

## If more Mac time is needed

| Usage shape | Cost |
|---|---|
| 4 × 24-hour blocks (spread over ~2 weeks of iteration) | ~€10.56 |
| Full month, M1, if iteration proves heavy | €75 |
| Upgrade to M2 (16 GB — more comfortable for Xcode) | €0.17/hr, €115/mo |

**Recommended purchase order:** M1 hourly, **one 24-hour block at €2.64**. If Xcode proves cramped at 8 GB RAM, escalate to M2 rather than pre-buying it. Do not take a monthly plan until hourly usage demonstrates it is cheaper.

## Cost notes
- Scaleway is a French/EU provider; billing in EUR. A payment method is required at signup.
- **No photo data ever reaches the cloud Mac.** The Mac compiles and signs; the benchmark executes on the Owner's own iPhones against a library that never leaves those devices. This preserves the Privacy-First constraint (Constitution §26) even though the build machine is rented.
- The $99 Apple Developer fee is not a sunk cost specific to Tier 0 — it is required for any eventual App Store release.

**➡️ Approval requested now for €2.64 only** (Scaleway, one 24h M1 block). The $99 is requested again separately, after the build is proven to compile (DEC-015). No further spend without a further request.

---

# PART 5 — DEVICE GRADIENT DESIGN (revised per Owner instruction)

The Owner's fleet is a **better** test grid than Tier 0 v1.1 asks for (it required 3 tiers). The design changes from "3 tiers" to **a performance gradient across every TestFlight-capable device**, with the minimum supported model **decided by the resulting curve, not assumed in advance.**

## 5.1 Required input from Owner (data collection, not a blocker)
For each iPhone: **exact model, iOS version, total storage, free storage, current photo-library asset count, and whether iCloud Photos "Optimise iPhone Storage" is on.** A one-line list is enough. Everything else proceeds without it.

## 5.2 Gradient axis
The variable that matters is the **Neural Engine generation**, not the model name. Expected shape (to be confirmed against the actual fleet):

| Chip era | ANE | Role in the gradient |
|---|---|---|
| A10 (iPhone 7) | **none** | Excluded — see Part 2 |
| A11–A12 (iPhone 8/X/XR/XS) | 1st–2nd gen | **Lower boundary candidate** — most likely to define the minimum supported model |
| A13–A14 (iPhone 11/12) | 3rd–4th gen | Mid |
| A15–A16 (iPhone 13/14/15) | mature | Mainstream |
| A18–A19 (iPhone 16/17) | current | Upper bound / headroom |

## 5.3 How the minimum supported model gets decided
Not by opinion. By this rule, fixed now:

> A device is **supported** if it meets the A1 time budget, the A2 thermal budget and the A4 incrementality requirement at that device's realistic library size. The **minimum supported model** is the oldest device in the fleet that passes. Devices that fail are reported with the specific budget they failed and by what margin.

If the curve shows a cliff (e.g. everything from A12 up passes comfortably and A11 fails badly), that cliff **is** the answer. If it degrades smoothly, the cut is a product decision for the Owner, informed by the measured numbers plus market share of each tier.

**Explicitly rejected:** picking a minimum model first and then testing it. That is the assumption the Owner told me not to make.

## 5.4 Run order — cheapest information first
1. **Owner's most-used current iPhone**, real library, as-is. Proves the harness works end to end and answers **A3 (survivability)** and **A4 (incrementality)** — the two claims that are fatal if they fail.
2. **Oldest TestFlight-capable device** (likely A11/A12). This is where A1/A2 will break if they break anywhere. Highest information per run.
3. **Everything in between**, to fill the curve.
4. **Scale-up runs** to 30k/100k on whichever devices have the storage headroom (Part 5.5).

Running the flagship first would prove the least — deliberately not first.

## 5.5 The 100k-library problem, and an honest solution
Tier 0 requires 10k / 30k / 100k. The Owner's real libraries are whatever size they are.

**Approach: hybrid corpus.**
- **Real portion** — the Owner's actual library. This is what produces a *realistic* OCR-gate ratio, screenshot proportion and iCloud-optimised mix. Synthetic images cannot give this.
- **Synthetic padding** — the benchmark app inserts generated assets into the photo library via `PHAssetCreationRequest` to reach 30k and 100k. Fully automatable on-device; no Mac sync, no iCloud upload, no 200 GB transfer.
  - Generate at **realistic pixel dimensions** (e.g. 4032×3024) with heavy JPEG compression: decode cost stays realistic (it tracks pixel count) while storage stays ~500 KB/asset → ~50 GB at 100k. Only devices with the free space participate in the 100k run.
  - Mix the synthetic set to approximate the real library's screenshot/photo ratio, so the OCR gate ratio is not artificially flattered.
- **Reporting rule:** every row in `DEVICE_BENCHMARK_TIER0.csv` records `real_asset_count` and `synthetic_asset_count` separately. A 100k number built mostly from synthetic assets is reported as such, never as a measurement on a real 100k library.
- **Cleanup:** synthetic assets are inserted into a dedicated album and removed afterwards. This must be tested on a throwaway basis **before** running against the Owner's primary device — see the safety note below.

> ⚠️ **Safety.** The harness writes to the Owner's real photo library. Insertion and cleanup must be proven on a secondary device with a disposable library **first**. Cleanup deletes only assets the harness itself created, tracked by local identifier — never anything pre-existing. This is the project's own no-silent-deletion red line applied to its own tooling.

**If the 100k run proves impossible on every device for storage reasons**, the honest output is a measured scaling curve at 10k/30k plus a labelled *projection* to 100k — reported as a projection, never as a PASS (PF-01).

---

# PART 6 — STEP-BY-STEP EXECUTION

### Phase 0 — Windows-side, no spend, can start immediately
0.1 Write the benchmark harness source (Swift) against the spec in `T0A_DEVICE_BENCHMARK_HARNESS_SPEC.md` — instrumentation, checkpointing, CSV schema, synthetic-corpus generator, cleanup logic. Cannot be *compiled* here, but can be *written* here.
0.2 Collect the fleet inventory from the Owner (§5.1).
0.3 Prepare the App Store Connect metadata and the TestFlight internal-tester list, ready to paste.

### Phase 1 — Approval gate ⛔  *(revised per DEC-015)*
1.1 Owner approves **€2.64** (Scaleway) only. ← *you are here*
1.2 **$99 is NOT paid yet.** Owner instruction: approved in principle, paid **only after the cloud Mac successfully compiles the project**. This sequences the risk correctly — the cheap reversible spend proves the toolchain first; the annual non-refundable fee is committed only once we know the build works.

### Phase 2a — Cloud Mac, build verification (before any $99)
2.1 Provision Scaleway Mac mini M1, connect over VNC/SSH.
2.2 Install Xcode + command line tools.
2.3 Pull the harness source, resolve compile errors, **build and run in the Simulator**. A signing identity is not required for this, which is what makes the pre-payment check possible.
**STOP. Report build success to Owner.**

### Phase 1b — Apple Developer enrollment (HG-1)
Owner enrolls **personally**: legal name, their own credit card, Apple Account with 2FA, possibly government photo ID (F4). I cannot and will not perform this step.

### Phase 2b — Cloud Mac, distribution
2.4 Archive, sign, upload to App Store Connect.
2.5 Release to TestFlight internal testing.
**Exit criterion:** a TestFlight build exists. Then release the instance — billing stops.
*Practical note:* confirm at provisioning whether the 24-hour block can be paused across the approval round-trip. If it cannot, budget a second €2.64 block rather than rushing the gate.

### Phase 3 — On device (no Mac needed, no ongoing cost)
3.1 Install via TestFlight on each device in the §5.4 order.
3.2 Run: cold index → interrupt deliberately → resume → incremental run. Record everything.
3.3 Export CSV from each device (share sheet → Files/email).
3.4 Verify PhotoKit V-1…V-5 from the harness spec. **V-5 (are app-deleted assets recoverable for 30 days) is the single most important check** — the Constitution's entire automation philosophy rests on it.

### Phase 4 — Analysis, Windows-side
4.1 Assemble `DEVICE_BENCHMARK_TIER0.csv` + `.md`.
4.2 Verdicts on A1–A4; plot the gradient; derive the minimum supported model per §5.3.
4.3 Feed into `TIER0_GO_NO_GO.md` alongside T0-B and T0-C.

**Further Mac blocks are needed only if Phase 3 reveals a harness bug.** Expect 1–3 additional 24-hour blocks (~€3 each). Each will be reported before purchase.

---

# PART 7 — WHAT THIS DOES AND DOES NOT UNBLOCK

| | |
|---|---|
| **Unblocks** | Tier 0-A entirely — and to a better standard than the document requires (5-device gradient vs 3 tiers) |
| **Partially unblocks** | Tier 0-B. The retrieval-entry prototype also needs a Mac and TestFlight; the same environment serves both, so B becomes purely a **user-recruitment** problem (HG-4) rather than a tooling problem |
| **Does not touch** | Tier 0-C2, still blocked on HG-2 (domain, landing page, payment path) |

**Consequence worth noting:** approving HG-3 collapses two of the three Tier 0 blockers into one environment. After this, the remaining gaps to a complete Tier 0 gate are **external test users** and **a real payment signal** — both of which are Owner-side and neither of which needs a Mac.

---

# PART 8 — OPEN QUESTIONS FOR OWNER (non-blocking; work continues regardless)
1. Fleet inventory per §5.1 — exact models, iOS versions, free storage, library sizes, iCloud optimisation setting.
2. ~~$99 sequencing~~ — **resolved by Owner (DEC-015): paid after the first successful compile.**
3. Confirm the harness may insert and then delete **its own** synthetic assets on a secondary device. Nothing pre-existing is ever touched, and this is proven on a disposable library before any primary device is used.
