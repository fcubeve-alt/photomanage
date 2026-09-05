# SESSION HANDOFF
Overwrite the CURRENT block at the end of every session. Template kept below it.

---

## CURRENT — Session 002 · 2026-09-06

| Field | Value |
|---|---|
| Repository | `D:\Documents\GitHub\photomanage` (**moved** — was `D:\photomanage` on the previous machine) |
| Remote | `github.com/fcubeve-alt/photomanage` (**PRIVATE**) |
| Branch | `main` |
| Full SHA | see `git log -1 --format=%H` — this session starts from `5abd016` |
| Stage | M1 / Tier 0 — 生死开关 |
| Session did | Cold-start recovery on a **new computer** (33 checks, 0 FAIL). Found and fixed **PF-10**: both Tier 0 analyzers died with `UnicodeEncodeError` under this machine's cp936 console, *after* completing their analysis. Pinned UTF-8 stdout in all seven Python entry points; added `tools-check.yml` CI with a verified negative control; re-verified generator determinism and manifest reproducibility on this machine; corrected stale coordinates and a stale build-ahead list in `PROJECT_STATE.md`. **DEC-025.** |
| Next action | Curate the 136 foreground test-library images (`TEST_LIBRARY_SPEC.md` §3) — the last thing between HG-4 and T0-B/T0-D running. Then put **FC-1** to the Owner as a decision. |

> ⚠️ **TOOLING — read before running anything.**
> **The previous machine's git trap is gone.** git here is **2.50.0**, on `PATH`, and reaches GitHub unprefixed. Ignore any older instruction to prefix `C:\Users\admin\tools` — that machine no longer exists (DEC-018 is historical).
> **`gh` is NOT installed on this machine.** Install GitHub CLI and `gh auth login` as `fcubeve-alt` (scopes `repo` + `workflow`) before adding HG-1 secrets or dispatching a workflow.
> **The console is cp936.** Python entry points pin their own stdout to UTF-8 — copy that snippet into any new script that prints `⚠️`/`✅`, or it will die on `print` after doing all its work (PF-10).
> Python here is **3.14.3**; `pillow` is available (needed only to render test-library pixels).

**Must read (in order):** `PROJECT_STATE.md` → this file → `CONSTITUTION_UNDERSTANDING.md` → `OPERATING_RULES.md` → `VALIDATION_MATRIX.md`.
Only if you need product-level detail: `10_SOURCE_DOCS/_extracted_text/L1_PRODUCT_CONSTITUTION_v1.3.txt`.

**Do NOT repeat:**
- Do not re-audit the documents. `DOCUMENTATION_MAP.md` is the finished result.
- Do not re-parse the .docx files. Use `10_SOURCE_DOCS/_extracted_text/*.txt`.
- Do not extract or read the Money OS zip. DEC-005 sealed it.
- Do not rebuild the governance files. They exist.
- **Do not rebuild the landing pages, the prototype, the test-library generator or the analyzers.** All four are finished, committed and re-verified on this machine (DEC-025). An older revision of `PROJECT_STATE.md` listed them as pending; it was wrong.
- Do not start Tier 1 or Tier 2 work. `TIER0_GO_NO_GO.md` is still an empty template.
- Do not report any device performance number as tested. No Mac, no iPhone benchmark (PF-01).

**Open Human Gates:** HG-1 (Apple Developer $99 + 8 signing secrets — critical path, precondition already met), HG-2 (domain + ad spend for T0-C2), HG-4 (n ≥ 15 external test users for T0-B **and** T0-D — needs no Mac and no spend, the cheapest way to answer two kill questions).

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
python recovery_check.py
```
That verifies the coordinates below still match reality and that every file this handoff points at still exists. Then:
```bash
cat PROJECT_STATE.md | head -40 && git status --short && git log --oneline -5
```
If the coordinates disagree with this file, fix state first. Never re-run Phase 0 from scratch.

`recovery_check.py` reads documents; it never executes a tool. On a machine this
project has not run on before, also confirm the instrumentation actually works —
this is exactly what PF-10 cost us:
```bash
python 20_TIER0/harness/analyze_benchmark.py --selftest > /dev/null && python 20_TIER0/study_assets/analyze_studies.py selftest > /dev/null && echo TOOLS OK
```
