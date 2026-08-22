# T0-C2 · Landing pages

Three arms, one template. Implements `../T0C2_LANDING_PAGE_PLAN.md`.
**Nothing is deployed. No domain, no ads, no money taken. Publishing is gated on HG-2b.**

```bash
python build_landing.py     # generates site/a, site/b, site/c
python server.py --port 8000
python server.py --report   # funnel table against the pre-registered criteria
```

## The arms

| URL | Rung | Thesis |
|---|---|---|
| `/a` | **L1 Organised Library** | Open it once and everything is already sorted (§12, §22) |
| `/b` | **L2 Continuous Manager** | You stop managing photos, permanently (§13) |
| `/c` | **L3 Cleaner** | **CONTROL.** Not a candidate positioning — §24 Gate 4 forbids shipping as a Cleaner. It exists so a low number on A or B is interpretable |

**Positioning is the manipulation; price is held constant at $39.** The Tier 0 kill question is *which rung carries willingness to pay*, not *what is the optimal price*. Layout, price, CTA mechanics, disclosure and instrumentation are byte-identical across arms — `build_landing.py` **verifies this on every build and aborts if it drifts**. Only the header, the proof points, the description block, the `<title>` and the meta description differ.

## Ethics — structural, not decoration

- **No money is ever taken.** There is no payment processor wired in at all, so it is not possible to charge someone by accident. Verified: no Stripe/PayPal/Braintree object exists on the page.
- **The disclosure fires the instant anyone commits** — before anything else. Full screen, and it **locks the page behind it** so it cannot be scrolled past.

  > **We are not charging you.**
  > Personal Visual Memory is not out yet. You just helped us prove people want it — that is genuinely what we needed to know.
  > Leave your email and you will get first access at $39, locked in.

- **No dark patterns.** No countdown, no fake scarcity, no invented reviews or ratings, no fake company. The description blocks state plainly what the app would do; there are no fabricated screenshots.
- **Ad copy must not claim the app is available today.**

## Privacy (§26)

- **Zero external requests.** Verified at build: no third-party pixel, no CDN, no web fonts, no Google Analytics. The page loads nothing from any other host.
- No cookies. A random per-session id is generated client-side in `sessionStorage`, which is enough to compute a funnel and nothing more.
- **The server does not store IP addresses.**
- **Emails are written to `emails.jsonl`, never into the event stream.** Verified: the captured address appears zero times in `events.jsonl`.
- Both files are **git-ignored**. `emails.jsonl` will contain real people's addresses and must never be committed.

> Running a privacy-first product's own test on surveillance infrastructure would be the first broken promise, made before we ship anything.

## Funnel

| Event | Meaning |
|---|---|
| E2 | landing page view |
| E3 | scrolled ≥ 50% — the pitch held attention |
| E4 | price block entered the viewport — they saw a real number |
| **E5** | **clicked "Get it — $39" — PRIMARY METRIC** |
| E6 | disclosure shown |
| E7 | email captured — intent survived the truth |
| E8 | "No thanks" — wanted the product, not the waitlist |

`--report` counts **unique sessions** per event, not raw hits, and prints C-P1/C-P3/C-P4 against the thresholds pre-registered in the plan. Those thresholds **must not be revised to fit the data** (AB-7).

## Deploying (Owner, after HG-2b)

`site/` is static. The only server-side requirement is a single `POST /event` route — `server.py` is the reference implementation, and the whole contract is: accept JSON, append to a file, return 204.

1. Register a domain.
2. Deploy `site/` to any static host; point `/a` `/b` `/c` at the three directories.
3. Deploy the `/event` route (any runtime — it is ~20 lines).
4. Split ad traffic evenly three ways.
5. **Do not add an ad-platform pixel to the page.** Report conversions server-side from the event log if the platform needs them.

## Status

Built and smoke-tested locally end to end: E2 → E3 → E4 → E5 → E6 → E7 confirmed firing, disclosure verified full-screen with scroll lock, email verified stored apart from the funnel. Smoke-test data has been deleted so the first real run starts clean.

**Not deployed. Awaiting HG-2b:** Owner approval of positioning, the $39 price and the disclosure wording, plus a domain (~$12) and ~$500–700 of ad spend.

**Run T0-D first where possible** — it tells us whether the Continuous Management rung is wanted before ~$600 is spent advertising it, and participants' own words should rewrite this copy, including replacing the invented "23 things" with the measured review-burden crossover.
