# T0-A · BUILD ENVIRONMENT EVALUATION — GitHub Actions vs Scaleway
Requested by Owner 2026-08-22. **Scaleway procurement paused pending this.**
**No cost incurred. No account created. No workflow run. No repository published.**

---

# VERDICT

**GitHub Actions macOS runners can do the entire job, and should be primary. Scaleway is demoted to fallback.**

Standard **Apple Silicon** macOS runners are **free and unmetered on public repositories**, and cost roughly **$0–20 for our entire bring-up** on a private one. They cover Xcode build, test, archive, signing and TestFlight upload — the complete chain.

Two things this does **not** change:
1. **The $99 Apple Developer Program is still required** for signing and TestFlight. No CI avoids it.
2. **A cloud Mac still cannot have an iPhone plugged into it** — and neither can a CI runner. Delivery to the 5-device fleet is still TestFlight.

One thing it improves: **DEC-015 gets strictly better.** Build-and-test needs no signing at all, so we can prove the project compiles **for free, before any $99 is spent** — no €2.64 block needed for that step either.

---

# PART 1 — FACT (verified 2026-08-22)

| # | Fact | Source | Confidence |
|---|---|---|---|
| G1 | **"GitHub Actions usage is free for standard GitHub-hosted runners in public repositories"** (verbatim) | docs.github.com/en/actions/concepts/billing-and-usage | HIGH |
| G2 | `macos-latest` = **macOS 26, arm64 (Apple Silicon)**, GA. `macos-15` also arm64 GA. `macos-14` deprecated | github.com/actions/runner-images | HIGH |
| G3 | Standard macOS SKU is **"macOS 3-core or 4-core (M1 or Intel)" at $0.062/min**, billing SKU `actions_macos`. The `-xlarge` / `-large` variants are *larger* runners and are charged even on public repos | docs.github.com/en/billing/reference/actions-runner-pricing | HIGH |
| G4 | Included minutes on private repos: **Free 2,000/mo**, Pro/Team 3,000, Enterprise 50,000 | docs.github.com billing | HIGH |
| G5 | `macos-15-arm64` ships **Xcode 16.0, 16.1, 16.2, 16.3, 16.4 (default), 26.0.1, 26.1.1, 26.2, 26.3**; iOS SDKs 18.0–26.2; simulators for iOS 18.5/18.6 and 26.0–26.2 | runner-images macos-15-arm64 README | HIGH |
| G6 | Job limit **6 hours**; workflow run limit 35 days | docs.github.com/en/actions/reference/limits | HIGH |
| G7 | Concurrency: Free plan **20 total jobs, 5 macOS**; the macOS limit is shared between standard and larger runners | same | HIGH |
| G8 | Artifact storage: **Free 500 MB**, Pro 1 GB; cache 10 GB/repo on all plans | same | HIGH |

**UNKNOWN-6.** Whether macOS minutes still consume the private-repo included allowance at a **10× multiplier** or at **1×** after the January 2026 repricing. The billing docs reference "minute multipliers" as a live concept while the runner-pricing reference presents flat per-minute rates. **Both scenarios are costed in Part 3 — it does not change the recommendation.** Resolve by reading the account's own billing page once a repo exists.

---

# PART 2 — CAN IT DO THE WHOLE CHAIN?

| Stage | GitHub Actions | Notes |
|---|---|---|
| **Xcode build** | ✅ | `xcodebuild build` on `macos-15`, Xcode 16.4 selected via `xcode-select`. Our deployment target is iOS 16 — well inside range |
| **Test** | ✅ | `xcodebuild test -destination 'platform=iOS Simulator,name=iPhone 16'`. Simulators are preinstalled |
| **Build without signing** | ✅ | `CODE_SIGNING_ALLOWED=NO` or a Simulator destination. **Needs no Apple Developer account at all** — this is what makes the free pre-payment compile check possible |
| **Archive** | ✅ | `xcodebuild archive` — requires a signing identity |
| **Signing** | ✅ | Distribution cert (`.p12`) + provisioning profile imported into a temporary keychain from encrypted secrets; or automatic signing with `-allowProvisioningUpdates` plus an App Store Connect API key |
| **TestFlight upload** | ✅ | `xcrun altool --upload-app` (or `fastlane pilot`) authenticated with an **App Store Connect API key** — Issuer ID, Key ID, and the `.p8`, all stored as repository secrets |
| **Deliver to the 5 iPhones** | ✅ via TestFlight | Same as Scaleway. **Neither option can attach a phone.** |

**Conclusion: the chain is complete.** This is an ordinary, heavily-trodden iOS CI pipeline, not an experiment.

---

# PART 3 — COST

## Our actual volume
Bring-up of never-compiled code: estimate **15–25 builds**. A small SwiftUI app builds in roughly **4–8 minutes** on an M1 runner including checkout and Xcode selection. Call it **~150 minutes total** for the whole bring-up, and **~50 min/month** in steady state.

| Option | Cost for bring-up (~150 min) | Steady state | Notes |
|---|---|---|---|
| **GH Actions · public repo** | **$0** | **$0** | Free and unmetered (G1). **Cost is strategy exposure, not money** — see Part 5 |
| **GH Actions · private, if 1× multiplier** | **$0** | **$0** | 150 min sits inside the 2,000/mo Free allowance |
| **GH Actions · private, if 10× multiplier** | **$0** | **$0** | 150 min → 1,500 charged units, still inside 2,000/mo |
| **GH Actions · private, allowance exhausted** | **~$9.30** | ~$3/mo | 150 × $0.062 |
| **Scaleway M1** | **~€5.28** (2 × 24h blocks) | €2.64 per session | Cannot pause; cannot delete before 24 h; **stopping does not stop billing** |

**Even the worst GitHub case beats Scaleway**, and the realistic case is **free on either visibility setting** — because 150 minutes fits comfortably inside the 2,000-minute Free allowance under either multiplier reading.

> **This means going public is NOT required to get the cost benefit.** That matters, because publishing is the expensive part (Part 5).

## Payment requirements

| | GitHub Actions | Scaleway |
|---|---|---|
| Account needed | GitHub (free tier sufficient) | Scaleway |
| **Card required to start** | **No** — free tier and public repos need no payment method | **Yes** |
| Billing risk if forgotten | None — no persistent resource exists | **Real**: an undeleted instance bills indefinitely |

The forgotten-instance risk is not theoretical. Scaleway bills for as long as the Mac is *assigned*, stopping does not help, and deletion is impossible for the first 24 hours. GitHub Actions has no persistent resource to forget.

---

# PART 4 — WHERE SCALEWAY IS STILL BETTER

Being fair to the option we are demoting. One real advantage:

**Interactive debugging of code that has never compiled.**
Scaleway gives a full macOS desktop over VNC: open Xcode, see all errors at once, fix them in seconds, rebuild instantly. CI gives you a log, and each iteration is commit → push → wait ~5 min.

**How much does this actually cost us?** The harness is ~1,400 lines of Swift written blind. Realistically a handful of error classes (most likely the mach/`task_info` bridging in `Telemetry.swift`), fixable in batches. Estimate **6–10 CI iterations, roughly 45–80 minutes of wall-clock**, mostly spent waiting rather than working.

Mitigations, in order:
1. **Batch the fixes.** `xcodebuild` reports every error in one pass, so each round can fix all of them.
2. **Build with `-quiet` off and full diagnostics** so one log is enough per round.
3. **`tmate`-style SSH into the runner** if a problem genuinely needs poking at. Third-party action, works on macOS runners — worth keeping in the back pocket, not the default.
4. **Scaleway as fallback**, exactly as the Owner proposed: if bring-up stalls after ~10 CI rounds, spend €2.64 and finish it interactively.

**Judgement:** 45–80 minutes of waiting, once, is a smaller cost than a paid account, a card, a 24-hour minimum lease and a standing "did I delete it?" liability. And every build after the first is where CI wins permanently — reproducible, scripted, no manual steps, no per-session cost.

---

# PART 5 — THE REAL DECISION: PUBLIC OR PRIVATE

**Public is not free.** It costs strategy exposure. This repository currently contains:

- The full **Product Constitution v1.3** — the entire product thesis and roadmap
- The **competitor pricing matrix** and the Lucent Pro analysis
- **T0-C2**: the $39 price, the three positioning arms, and the landing-page copy *before it launches*
- Every decision, failure pattern and open UNKNOWN
- The user-study protocols and their pre-registered thresholds

Publishing that hands a competitor the strategy, the pricing test and the copy, in advance.

**Recommendation: PRIVATE repository.**

Part 3 shows the cost argument for going public **evaporates** — 150 minutes fits inside the free allowance under either multiplier reading, so private is free too for our volume. There is no reason to pay in strategy for a discount we already have.

> If minutes ever do run out, the correct response is to pay the few dollars, **not** to publish the strategy.

**Later option worth keeping in mind:** if the harness ever needs to be public (open-sourcing the benchmark would be good for credibility), split it into its own repository. The benchmark harness alone is publishable — it contains no strategy. The governance repo stays private. Not needed now.

---

# PART 6 — WHAT THE OWNER MUST DO

| # | Action | Why only you |
|---|---|---|
| 1 | **Create a GitHub repository (private)** and give me the remote URL | Account creation |
| 2 | Push the existing local history to it | Also fixes the standing MAINTENANCE item — the repo is currently **local-only**, a real single-point-of-failure for E-06 cross-machine recovery |
| 3 | *(later, after a green build)* Enrol in Apple Developer, $99 | HG-1 — legal name, own card, 2FA, possibly photo ID |
| 4 | *(later)* Create an **App Store Connect API key** and add secrets | Apple account access |

### Secrets needed at step 4 (not before)
```
APP_STORE_CONNECT_ISSUER_ID     APP_STORE_CONNECT_KEY_ID
APP_STORE_CONNECT_PRIVATE_KEY   (.p8 contents)
BUILD_CERTIFICATE_BASE64        (.p12, base64)
P12_PASSWORD                    PROVISIONING_PROFILE_BASE64
KEYCHAIN_PASSWORD               (any random string)
```

**I can do:** write and iterate the workflows, fix compile errors, tune the build. **I cannot:** create the repo, enrol with Apple, or generate/enter the signing credentials.

---

# PART 7 — REVISED SEQUENCING (supersedes DEC-015 mechanics, keeps its intent)

The Owner's rule was: **pay the $99 only after a successful compile.** GitHub Actions makes that cleaner, not just cheaper.

| Step | What | Cost | Gate |
|---|---|---|---|
| 1 | Owner creates a **private** repo, pushes | $0 | account |
| 2 | `ios-build.yml` runs: build + test **unsigned** on `macos-15` | **$0** | none |
| 3 | I fix compile errors until the build is green | **$0** | none |
| 4 | **Report a green build to Owner** | — | — |
| 5 | Owner enrols in Apple Developer | **$99** | HG-1 |
| 6 | Owner adds signing secrets | $0 | HG-1 |
| 7 | `ios-testflight.yml` (manual dispatch): archive → sign → upload | $0 | — |
| 8 | Install on the 5-device fleet, run the benchmark | $0 | — |

**Scaleway is not needed at any step.** It stays documented as a fallback for step 3 only, if CI bring-up stalls.

**Net effect: the €2.64 ask is withdrawn.** The only remaining spend on the T0-A path is the **$99**, and it is now paid strictly after a proven-green build.

---

# PART 8 — DELIVERED WITH THIS EVALUATION

Both workflows are written and committed, ready to run the moment a remote exists:

| File | Runs | Needs secrets? |
|---|---|---|
| `.github/workflows/ios-build.yml` | on push/PR — build + test, **unsigned** | **No** |
| `.github/workflows/ios-testflight.yml` | manual dispatch only — archive, sign, upload | Yes (step 6 above) |

`ios-build.yml` deliberately requires no Apple account, so step 2 can run the moment the repo exists.

---

## Sources
- https://docs.github.com/en/actions/concepts/billing-and-usage
- https://docs.github.com/en/billing/reference/actions-runner-pricing
- https://docs.github.com/en/actions/reference/limits
- https://github.com/actions/runner-images
- https://raw.githubusercontent.com/actions/runner-images/main/images/macos/macos-15-arm64-Readme.md

All retrieved 2026-08-22.
