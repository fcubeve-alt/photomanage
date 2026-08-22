# FACILITATOR SCRIPT — T0-B then T0-D
**Read the quoted lines verbatim.** AB-2: either the facilitator is not the prototype's author, or this script is read word for word. Unconscious steering is the default failure mode of a founder-run usability test.

Session length ≈ 75 min (T0-B ~45, T0-D ~25, setup/wrap ~5).
Everything in `[brackets]` is an instruction to you, never spoken.

---

## BEFORE THE PARTICIPANT ARRIVES

| # | Check | Done |
|---|---|---|
| 1 | Ledger variant assigned from the rota below — **you do not choose on the day** (AB-11) | ☐ |
| 2 | Arm order assigned from the rota (AB-1) | ☐ |
| 3 | **Apple Photos fair-configuration verified**: full library authorisation, People fully indexed, indexing settled. Record it. A rigged win is worse than a loss (AB-5, PF-07) | ☐ |
| 4 | Prototype installed, catalogue loaded, launched once and closed | ☐ |
| 5 | Test library present and complete (`manifest.json` count matches device count) | ☐ |
| 6 | Device: full battery, Do Not Disturb ON, auto-lock 5 min, brightness fixed | ☐ |
| 7 | Timer, both scoring sheets printed, recorder ready | ☐ |
| 8 | Both apps **closed** (not backgrounded) so first-open is genuinely first-open | ☐ |

### Rota (n = 15 — raised from 10, DEC-021)

> Raised from 10. At n=10 the **only** result that clears a 70% threshold is a
> unanimous 10/10 — even 9/10 leaves the threshold inside the confidence interval.
> Five extra participants is what makes a 90% result statistically resolvable
> instead of merely suggestive. See protocol §8.1.

| P | Arm order | Ledger variant |
|---|---|---|
| P01 | A → B | V1 |
| P02 | B → A | V2 |
| P03 | A → B | V3 |
| P04 | B → A | V4 |
| P05 | A → B | V1 |
| P06 | B → A | V2 |
| P07 | A → B | V3 |
| P08 | B → A | V4 |
| P09 | A → B | V1 |
| P10 | B → A | V2 |
| P11 | A → B | V3 |
| P12 | B → A | V4 |
| P13 | A → B | V1 |
| P14 | B → A | V2 |
| P15 | A → B | V3 |

Balance check: arm order 8×(A→B) / 7×(B→A); variants V1×4, V2×4, V3×4, V4×3.

**A = Apple Photos · B = our prototype.** Introduce them only as **"app 1" and "app 2"** in the order the participant will meet them (AB-3). Never say "ours", never show branding.

---

## 0 · CONSENT AND FRAMING (3 min)

> "Thanks for coming. I'm testing two photo apps — I didn't make either of them, and I'm not testing you. There are no wrong answers, and if something is confusing that's useful information for me.
>
> The phone has a photo library on it that isn't yours. For today, please treat it as if these were your own photos — you're the person in them, you took them. I'll give you a few minutes to look around first.
>
> I'd like to record the screen and the audio, just for my own notes. Nothing is published and I'll delete it after I've written up. Is that OK?"

[Get explicit yes. If no → written notes only, record that on the sheet.]

> "One more thing: please think out loud. Say what you're looking for and what you expect to happen, even when it feels obvious."

---

## 1 · FIRST-OPEN, ARM 1 (5 min) — T0-B B-1

[Hand over the phone with the app closed. Start the timer as they tap.]

> "Please open app 1 and tell me what you see. Keep talking as you look."

[**Do not** explain anything. **Do not** answer questions yet — say "I'd like to see what you make of it first." Record:]

- Time to first meaningful reaction: ______ s
- Do they use organisation vocabulary unprompted (sorted / tidy / categories / it did this)? **Y / N** — verbatim: ______
- **Do they ask "did it do this by itself?"** → **Y / N** [that question is the §12 moment landing]
- First emotional reaction, verbatim: ______

Then, still before any tapping:

> "Without tapping anything — where would you expect to find your passport?"

- Their answer, verbatim: ______
- Correct? **Y / N** [correct = Documents → Identity → Passport, or an equivalent path they can name]

> **This is the sharpest single measurement in the study.** It tests predictability — whether this is a destination or just another app to search. Record the answer *before* they touch the screen, every time.

[Repeat this whole section for arm 2 at the handover point.]

---

## 2 · RETRIEVAL TASKS (25 min) — T0-B B-2

[Give the 3-minute free browse first, once per arm.]

> "Take three minutes to look around however you like. I'll tell you when to stop."

Then, for each task, read the prompt exactly and start the timer on the last word.

| # | Say exactly this |
|---|---|
| T1 | "Find both sides of your ID card — the front and the back." |
| T2 | "Last year you went to Tokyo. Find the photo of your friend wearing a white top on that trip." |
| T3 | "You bought a pair of headphones. Find the receipt." |
| T4 | "Show me all the photos of the same person, across the last three years." |
| T5 | "There's a bicycle that appears in your photos more than once. Find the times you photographed it." |
| T6 | "About seven weeks ago you got a parcel pickup code. Find that screenshot." |
| T7 | "There's a run of eight nearly identical photos from the beach. Keep the best one and get rid of the rest." |

**Rules while they work:**
- Say nothing. Do not hint. If they ask "is this right?" → *"Whatever you think."*
- **Stop at 3 minutes** and record as gave-up: *"That's fine, let's move on."*
- Record backtracks — every return to home or restart of approach. It is the clearest signal that the structure was unpredictable.
- T7 is done **manually in both arms**. We are not testing an automatic feature here; we are measuring what this costs today.

[After T7, in each arm:]

> "How confident are you that you kept the right one?" ______ /5

---

## 3 · ARM SWITCH

> "Now I'd like you to do the same kinds of things in app 2."

[Repeat §1 first-open and §2 tasks for arm 2. Same wording. Same order of tasks.]

---

## 4 · FORCED CHOICE (3 min) — T0-B P-1

> "If you needed to find a photo tomorrow — a document, a receipt, a picture of someone — which of these two would you open first?"

[**Never** ask "which is better". Predicted behaviour is the metric, preference is cheap (AB-4).]

- Choice: **app 1 / app 2** → resolves to **Apple Photos / prototype**: ______
- > "Why that one?"  Verbatim: ______

[Coded blind later for P-2: structural reason vs novelty/aesthetics.]

> "And what annoyed you most about the other one?"

- Verbatim: ______ [feeds the Apple Photos failure-case inventory]

---

## 5 · PART 2 — THEIR OWN LIBRARY (8 min, Apple Photos only)

> "Now let's use your own phone and your own photos, in the Photos app you normally use. Same kinds of things."

[Pick any 3 of: their own ID/passport, a receipt, a specific person on a specific trip, a screenshot from a known week.]

> "Our prototype can't do this part — it hasn't been set up with your photos. So this is just about how the app you already use handles it."

[Record per task: success / time / steps, and **every complaint verbatim**. This section produces the structured failure-case list Tier 0 §3 requires — turning "feeling" into cases.]

---

# ⏸ BREAK POINT — T0-B ENDS HERE

> **Do not merge what follows into the retrieval results.** T0-B and T0-D answer different questions, are recorded on separate sheets, and neither may substitute for the other (Owner instruction, DEC-014).

[Put the T0-B sheet away. Take out the T0-D sheet. Say:]

> "That's the first part done. Now something different — I want to show you one screen and ask what you make of it."

---

## 6 · LEDGER COLD READ (5 min) — T0-D D-2

[Show the **assigned** variant. Do not explain it. Start the timer.]

> "Tell me what this screen is telling you."

- Time to correct comprehension: ______ s [correct = they say the app has already organised/cleaned the library]
- Identify unprompted that the work is already done? **Y / N**
- Ask "did it do this by itself?" **Y / N**
- First reaction, verbatim: ______
- Anything they distrust or want to check? Verbatim: ______

[If asked whether the numbers are real: answer honestly — *"They're from a test library, not your phone."* — and record that it was asked (AB-13).]

---

## 7 · TRUST PROBE (2 min)

> "Would you let this run on your own photos?"

- **Yes / No / Conditional**
- If conditional: *"What would have to be true?"* Verbatim: ______

[These conditions are the Personal Policy design input (§14). Capture them exactly, not paraphrased.]

---

## 8 · MODE PREFERENCE (5 min) — T0-D D-1

[Read all three in the rota-assigned order. Neutral tone, no emphasis on any one (AB-9).]

> "Imagine three different versions of a photo app.
>
> **Version 1** — nothing happens without your approval. It shows you what it thinks and you decide every time.
>
> **Version 2** — it handles the obvious things by itself, and asks you about anything uncertain or important.
>
> **Version 3** — it manages your library continuously on its own, and only asks about the few things that really need you."

> "Which would you actually want?"  → **1 / 2 / 3**
> "Why?"  Verbatim: ______

> "Compared with Version 1, how much more would Version [their choice] be worth to you — nothing, a bit more, or a lot more?"

[Relative only. A real price is T0-C2's job, not this session.]

---

## 9 · RISK-GRADED TOLERANCE (5 min) — T0-D D-4

> "For each of these, tell me what you'd want the app to do: handle it automatically, ask you first, or never touch it."

[Read in this order. Record verbatim if they hesitate or qualify.]

| Content | auto / ask / never |
|---|---|
| A verification code screenshot from six months ago | |
| A meme you downloaded four times by accident | |
| Eight nearly identical burst photos | |
| A photo of a meal | |
| A receipt for something you bought | |
| A screenshot of a work document | |
| A family photo | |
| **A photo of your ID card** | |
| **A photo of a signed contract** | |

[This validates the R0–R6 ladder as *measured user preference* rather than assumption. No engine is being tested.]

---

## 10 · RECOVERABILITY (3 min) — T0-D D-5

[Pick the 2–3 items they were most protective about.]

> "One thing I didn't mention: anything the app removes goes to Recently Deleted, and you can restore it for 30 days. Knowing that — would you change any of your answers?"

- Changed answers: ______
- Verbatim: ______

[The size of this shift is the empirical value of §7's recoverability argument. It has never been measured.]

---

## 11 · REVIEW BURDEN (3 min) — T0-D D-3

> "Say the app has sorted about ten thousand photos, and at the end it leaves you a list of things it wasn't sure about. For each number, tell me: does that feel like it handled it for you, or like it gave you homework?"

[Read in the rota-assigned order — not always ascending.]

| Queue size | handled / homework |
|---|---|
| 5 items | |
| 23 items | |
| 80 items | |
| 300 items | |

- Crossover point: ______ [→ first empirical Human Review Burden target for §18]

---

## 12 · CLOSE (2 min)

> "That's everything. Is there anything you expected me to ask about and I didn't?"

- Verbatim: ______

> "Thank you — this was genuinely useful."

[Immediately after they leave, while it is fresh:]
- Anything that went wrong procedurally: ______
- Any moment you deviated from the script: ______ [record honestly; it affects how the data is read]
- Did anything about the setup make the prototype look better than it deserved? ______ [AB-6: counter-evidence is sought, not tolerated]
