# Personal Visual Memory Engine

Turn the Camera Roll from an unsorted file pile into a self-cataloguing, self-maintaining personal visual library.

**Current stage: P0 Kill Test — Tier 0. This is validation, not product development.**

> ## Nothing of the product is built. Zero lines.
> Everything in this repository is **measuring equipment**, not the product:
> ~1,650 lines of Swift that time how fast an iPhone can read a photo library,
> 82 hand-authored prototype pages with fixed content and no engine behind them,
> and ~3,100 lines of Python generators, analyzers and checkers that will never ship.
>
> **The classifier, the taxonomy engine, the entity resolver, the lifecycle engine
> and the risk policy engine do not exist.** They are Tier 1 / Tier 2 work, they are
> still LOCKED, and they are the hard part. A green test result here is evidence
> about a *tool*. It is never evidence about the product. (`FAILURE_PATTERNS.md` PF-11)

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
