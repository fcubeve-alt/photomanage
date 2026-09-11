# Personal Visual Memory Engine

Turn the Camera Roll from an unsorted file pile into a self-cataloguing, self-maintaining personal visual library.

**Current stage: internal alpha. Not shippable, not a product, and not on a phone.**

> ## What is and is not true here
>
> This block said **"Nothing of the product is built. Zero lines"** until 2026-09-11.
> That was written when it was true and was left standing for weeks after it stopped
> being true, which is worse than never having written it. A third-party audit found it
> on the repository's front page.
>
> **What exists.** A Python classification engine (`30_ENGINE/`) — classifier,
> taxonomy, entity resolver, lifecycle and risk policy, all five of the things this
> block called LOCKED — a Swift port of it (`40_APP/PVMCore/`) that CI compiles and
> tests on Linux and against Apple's Foundation, a conformance test that replays the
> engine's own answers and fails if the two implementations disagree, and a SwiftUI app
> (`40_APP/PVM/`) that browses, searches, remembers and asks.
>
> **What is not true.** Nothing here has run on a physical iPhone. No real person has
> used it. The accuracy figures come from a **synthetic fixture library**, not from
> photographs — see the warning on them below. The app cannot delete or modify a photo
> and is structurally prevented from doing so (`LibrarySafety`), because deletion
> landing in Recently Deleted and being restorable has never been observed on a device
> and §7's entire tolerance argument rests on it.
>
> PF-11 still holds and is why this block stays: **a green test is evidence about code,
> never about a product.** It just has to describe the code that is actually here.
>
> ⚠️ **The default branch is behind.** Development happens on
> `claude/classification-program-dev-yk88jj`. If you are reading `main`, you are
> reading the state from before any of the above.

## Start here
| File | Purpose |
|---|---|
| **`PROJECT_STATE.md`** | **Read first.** Current stage, work queue, blockers, next action. |
| `SESSION_HANDOFF.md` | Session coordinates + what not to redo. |
| `MISSION_SPEC.md` | Mission, success criteria, in/out of scope, hard constraints, Human Gates. |
| `MASTER_PLAN.md` | Milestones M0–M4 and their acceptance gates. |
| `VALIDATION_MATRIX.md` | Every test: criteria → measurement → status → next action. |
| `OPERATING_RULES.md` | How this project works (Engineering Playbook, filtered). |
| `DECISIONS.md` | Why things are the way they are. Append-only. |
| `FAILURE_PATTERNS.md` | Known traps and their guards. |
| `DOCUMENTATION_MAP.md` | Which document is authoritative, and what was superseded. |

## Layout
```
10_SOURCE_DOCS/          authoritative source documents (.docx)
  _extracted_text/       grep-able plain text — read these, not the .docx
20_TIER0/evidence/       Tier 0 experimental evidence and deliverables
90_ARCHIVE/SUPERSEDED/            older document versions, kept not deleted
90_ARCHIVE/OTHER_PROJECT_MONEY_OS/  a different project — do not import (DEC-005)
```

## Non-negotiables
- **One tier at a time.** Tier 1 opens only after `TIER0_GO_NO_GO.md` exists.
- **Real evidence only.** "Looks fine", "should work in theory" and "the code is written" are not PASS.
- **No fabricated device results.** Anything needing macOS/Xcode/a real iPhone is tagged `REQUIRES_MAC` / `REQUIRES_DEVICE` and reported as untested.
- **Safety red lines from day one.** No silent permanent deletion; IDs, contracts and family memories default to Protect; every suggestion must explain why.
- **Chat history is not project state.** Everything that matters is on disk.
