# SESSION HANDOFF
Overwrite the CURRENT block at the end of every session. Template kept below it.

---

## CURRENT — Session 003 · 2026-09-06

| Field | Value |
|---|---|
| Repository | `photomanage` |
| Remote | `github.com/fcubeve-alt/photomanage` (**PRIVATE**) |
| Branch | `claude/classification-program-dev-yk88jj` |
| Full SHA | see `git log -1 --format=%H` |
| Stage | M1 / Tier 0 — 生死开关, **plus the classification engine by Owner instruction (DEC-028)** |
| Session did | **Two things, both on Owner instruction.** (1) **T0-A now has real measured data at $0** — a scale sweep of the full indexing pipeline on the iOS Simulator: **105–154 ms/asset across two runs of identical code**, linear within each run. Ceiling **35k–52k** assets in the 90-min foreground budget, **187k–275k** in the 8-h background budget, predicted device band **7k–26k** foreground. The 1.47x spread is CPU contention on a shared runner, not the harness — every deterministic output matched exactly — so the ceiling is a band and never a figure. Three findings: C-1's "OCR dominates" prediction is **inverted on this host** (embedding 84%, OCR 6%) and is now *in doubt* rather than refuted, because the Simulator has no Neural Engine and the embedding is exactly the stage that would use it; index size is **2× over its §8 budget**, all of it the 3,072-byte feature print; cost is linear. Evidence: `20_TIER0/evidence/T0A_SCALE_SIMULATOR_2026-09-06.md`. The first attempt came back **green having measured nothing** — the guard is the only reason that was caught. (2) **Built the classification engine** (`30_ENGINE/`, DEC-028): signal contract, escalating classifier, R0–R6 risk policy, duplicate / same-entity handling, SQLite catalogue with checkpoint-resume and incrementality, CLI, 55 tests, evaluation harness. On the 10,000-asset labelled library: root macro **F1 0.998**, leaf exact **99.8%** where the label is derivable, **0** wrong roots, 4/4 safety red lines audited against the written catalogue. Found and fixed a silent defect that lost 9 of 9 identity documents (location was settling the answer before OCR ran) and a corpus defect in A00126–A00132 whose GPS and label disagree. |
| Session also did | **DEC-029, two Owner rulings.** Paced ingestion (`pvm/schedule.py`, `pvm plan`): breadth pass measured at 0.17 ms/asset with no pixels decoded, so 100k is browsable in <30s and depth is paced. Change-driven processing (`pvm/deltas.py`): 61–88% of per-frame work saved, with the correction that comparison is against the last *keyframe* — the naive pairwise rule processes 1 frame of 600 on a slow pan and misses a 41-bit scene change — plus the FC-1a, document and run-cap guards. **A1 is no longer a kill question; A3 and A4 are now the whole of it.** |
| Next action | **Owner calls, in this order.** (1) **HG-1** — the $99 payment instrument; everything downstream of it is written and green, and only a device can answer A2/A3/A4. (2) **FC-1 + its FC-1a precondition** — and note the scale sweep changes the argument: the dedup skip now looks worth more than the OCR gate, since the embedding is what dominates. (3) **The index-size overrun** — store the feature print, quantise it, or recompute on demand. (4) **T0-B** stays live (DEC-027): 136 foreground images, then HG-4. (5) **OPEN-3** — whether `dHash` separates scenes on real footage; needs video, not a device, so HG-1 does not block it. (6) **The eleven MISSING clauses** in `30_ENGINE/CONSTRAINTS.md` — worst first: the **Visual Memory Graph** (§2 Remember / L1-B §4), **Intent Search** and **Relations** (two of §10's four retrieval paths), **per-category Entity Resolution** (§24 Gate 2), **Select Best** (§25 L6), **Personal Policy** (§14). And read the 34 PARTIAL rows harder than the MISSING ones — a partial clause passes its tests and still does not do what the document asks. |

> ⚠️ **TOOLING — read before running anything.**
> **The console is cp936.** Every Python entry point pins its own stdout to UTF-8 — copy that snippet into any new script that prints `⚠️`/`✅`, or it dies on `print` after doing all its work (PF-10). `tools-check.yml` runs every self-test under `PYTHONIOENCODING=gbk` as a verified negative control.
> **`gh` may not be installed.** Install GitHub CLI and `gh auth login` as `fcubeve-alt` (scopes `repo` + `workflow`) before adding HG-1 secrets or dispatching a workflow.
> **The engine needs no dependencies.** `cd 30_ENGINE && python -m unittest discover -s tests` and `python eval/evaluate.py --library ../20_TIER0/study_assets/library/manifest.json`. Python 3.11+, nothing to install.
> **Do not use `%-d` in a date format.** It is a glibc extension and raises on Windows.

**Must read (in order):** `PROJECT_STATE.md` → this file → `CONSTITUTION_UNDERSTANDING.md` → `OPERATING_RULES.md` → `VALIDATION_MATRIX.md`.

⚠️ **Before touching `30_ENGINE/`, read `30_ENGINE/CONSTRAINTS.md` and then the clauses it cites in `10_SOURCE_DOCS/_extracted_text/L1_PRODUCT_CONSTITUTION_v1.3.txt` and `L1B_*.txt`.** This file used to call L1 optional — *"only if you need product-level detail"* — and that framing is exactly how the engine came to be built without it (**PF-12**). The digests are convenient and incomplete by design. `python 30_ENGINE/check_constraints.py` tells you in one second whether the register still matches the sources.
Then `30_ENGINE/README.md` — its "five decisions worth arguing with" is the part to disagree with, not the file list.

**Do NOT repeat:**
- Do not re-audit the documents. `DOCUMENTATION_MAP.md` is the finished result.
- Do not re-parse the .docx files. Use `10_SOURCE_DOCS/_extracted_text/*.txt`.
- Do not extract or read the Money OS zip. DEC-005 sealed it.
- Do not rebuild the governance files, the landing pages, the prototype, the test-library generator or the analyzers. All finished and re-verified.
- **Do not score the classifier on all 10,000 leaf labels.** 4,155 of them were chosen by `random.choice` and no signal records which. `eval/evaluate.py` explains this in its own first section and refuses to score them; making that number look better is not possible and not the point.
- **Do not feed ground truth to the classifier.** `eval/adapter.py` raises on every label field. If a new signal is needed, add it to the allow-list deliberately or not at all.
- Do not report any device performance number as tested. The scale sweep is a Simulator ceiling, not an iPhone (PF-01).

**Open Human Gates:** HG-1 (Apple Developer $99 — blocked on a payment instrument, not willingness, DEC-027; critical path), HG-4 (n ≥ 15 external test users for T0-B — needs no Mac and no spend).

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
