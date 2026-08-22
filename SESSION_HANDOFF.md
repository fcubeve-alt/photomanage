# SESSION HANDOFF
Overwrite the CURRENT block at the end of every session. Template kept below it.

---

## CURRENT — Session 001 · 2026-08-22

| Field | Value |
|---|---|
| Repository | `D:\photomanage` |
| Remote | `github.com/fcubeve-alt/photomanage` (**PRIVATE**) |
| Branch | `main` |
| Full SHA | see `git log -1 --format=%H` |
| Stage | M1 / Tier 0 — 生死开关 |
| Session did | Bootstrap, doc audit, persistent state, validation matrix, T0-C1, T0-A harness + CI, T0-B/D protocols + prototype, T0-C2 plan; repo live; **first CI build GREEN** |
| Next action | Owner: HG-1 ($99 Apple Developer + secrets). Meanwhile: wire prototype leaves to the real manifest; build T0-C2 landing pages |

> ⚠️ **TOOLING — read before running any git or gh command.**
> The system default `git` is **2.9.0 (2016) and cannot reach GitHub at all** — it fails with exit 128 and *empty stderr*. Prefix PATH every session:
> ```
> export PATH="/c/Users/admin/tools/git/cmd:/c/Users/admin/tools/bin:$PATH"
> ```
> (PowerShell: `$env:PATH = "C:\Users\admin\tools\git\cmd;C:\Users\admin\tools\bin;$env:PATH"`)
> `gh` 2.98.0 is authenticated as **fcubeve-alt** with `repo` + `workflow` scopes.
> The repo-local credential helper is `!gh auth git-credential`; the global `manager` helper is broken (GCM was never installed). See DEC-018.

**Must read (in order):** `PROJECT_STATE.md` → this file → `CONSTITUTION_UNDERSTANDING.md` → `OPERATING_RULES.md` → `VALIDATION_MATRIX.md`.
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
