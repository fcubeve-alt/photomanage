# SESSION HANDOFF
Overwrite the CURRENT block at the end of every session. Template kept below it.

---

## CURRENT — Session 001 · 2026-08-22

| Field | Value |
|---|---|
| Repository | `D:\photomanage` |
| Remote | **none** — local only (open MAINTENANCE item) |
| Branch | `main` |
| Full SHA | see `git log -1 --format=%H` |
| Stage | M1 / Tier 0 — 生死开关 |
| Session did | Bootstrap + documentation audit + persistent state + validation matrix; started T0-C1 |
| Next action | Complete `20_TIER0/evidence/COMPETITOR_PRICING_MATRIX.md`, then T0-A-PREP |

**Must read (in order):** `PROJECT_STATE.md` → this file → `OPERATING_RULES.md` → `VALIDATION_MATRIX.md`.
Only if you need product-level detail: `10_SOURCE_DOCS/_extracted_text/L1_PRODUCT_CONSTITUTION_v1.3.txt`.

**Do NOT repeat:**
- Do not re-audit the documents. `DOCUMENTATION_MAP.md` is the finished result.
- Do not re-parse the .docx files. Use `10_SOURCE_DOCS/_extracted_text/*.txt`.
- Do not extract or read the Money OS zip. DEC-005 sealed it.
- Do not rebuild the governance files. They exist.
- Do not start Tier 1 or Tier 2 work. `TIER0_GO_NO_GO.md` does not exist yet.
- Do not report any device performance number as tested. No Mac, no iPhone benchmark (PF-01).

**Open Human Gates:** HG-2 (payment/landing page), HG-3 (Mac/Xcode/devices), HG-4 (external test users). Each blocks only its own workstream.

---

## TEMPLATE

```
## CURRENT — Session NNN · YYYY-MM-DD
| Field | Value |
|---|---|
| Repository | |
| Remote | |
| Branch | |
| Full SHA | |
| Stage | |
| Session did | |
| Next action | |

Must read:
Do NOT repeat:
Open Human Gates:
```

## Bootstrap integrity check (E-05) — run before any work
```bash
cat PROJECT_STATE.md | head -30 && git status --short && git log --oneline -5
```
If the coordinates disagree with this file, fix state first. Never re-run Phase 0 from scratch.
