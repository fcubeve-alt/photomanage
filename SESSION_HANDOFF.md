# SESSION HANDOFF
Overwrite the CURRENT block at the end of every session. Template kept below it.

---

## CURRENT — Session 004 · 2026-09-07

| Field | Value |
|---|---|
| Repository | `photomanage` |
| Remote | `github.com/fcubeve-alt/photomanage` |
| Branch | `claude/classification-program-dev-yk88jj` |
| Full SHA | see `git log -1 --format=%H` |
| Stage | M1 / Tier 0, plus the classification engine and the app (DEC-028) |
| Session did | **Closed clauses by building and by measuring, and corrected the register where it had drifted.** §5's sixth factor, **Importance**, now exists as an axis of its own (`30_ENGINE/pvm/importance.py`) alongside §4's thirteen 大类 — the two were one omission seen from two sides, and §18's Weighted Error Cost had been squaring risk in place of 内容重要性. §11 now **infers a place** from the photographs either side in time, and refuses far more often than it claims. §10's Browse path grew its **Person level inside Documents** without opening `Documents` as an extensible root. §10's **Relations join** links a receipt, an order screenshot and a warranty by a shared reference. §11's other **Event candidates** — a day out, a gathering — are derived. Tier 1-D's six indexes are reachable from a single asset. And three things were measured for the first time: **Tier 2-E's ablation arms** (the two expensive signals do not overlap — People is 0.995 with vision and 0.000 without; Documents and Purchases are 1.000 with OCR and 0.000 without), **§19 risk grading** (99.7% exact, 0 under-graded, and 0 of 34 acted-on assets have a true risk of R4+), and **Tier 1-C's Suggest Delete false-positive rate** (0 of 21 offered). |
| Numbers | Classifier unchanged where it should be: macro **F1 0.997** *(fixture conformance on a synthetic library — not product accuracy; see the warning at the top of the evaluation report)*, leaf exact **99.8%**, **0** wrong roots. Automation Ratio 94.1%, Human Review Burden 59/1,000, Catastrophic Error Rate 0, Coverage 94.8%. **Five** safety red lines now, all PASS, checked against the written rows rather than the code. 294 Python tests. |
| Register | `30_ENGINE/CONSTRAINTS.md`: 91 clauses · **52 DONE · 26 PARTIAL · 4 MISSING** (was 36/34/11 as *claimed* and 48/29/5 as *counted* — the summary table had drifted and `check_constraints.py` now fails when any cell of it disagrees with the rows). |
| Next action | **The four MISSING are all blocked on evidence, not effort**, and so is most of the PARTIAL list. (1) **T1B-EMBEDDING** — a visual embedding for objects; the ceiling on object identity, on Object Memory and on open-vocabulary search. Wiring `VNGenerateImageFeaturePrintRequest` is a day; choosing the distance at which two feature prints are the same object needs **real photographs**, and `20_TIER0/study_assets/library` is PIL-drawn placeholders. (2) **T2B-SELECTBEST** — sharpness, closed eyes, framing, blur; same blocker. (3) **T1E-PATHS** and every 成功率 in the same family — blocked on **real users**. (4) **T2B-VALUELOSS** — blocked by (2). Then: a **device** (PF-01 still stands, nothing here has run on a phone), and the **PhotoKit write path** (S2-CLEAN — the engine proposes and protects and cannot execute). |

> ✅ **CI works. This block previously said it did not, and that was the most
> misleading claim in the file.**
> `swift-core.yml` (Linux) compiles `PVMCore` and runs its tests in about a minute;
> `app-build.yml` (macOS) builds the app for the Simulator, runs the same core tests
> against Apple's Foundation, and captures screenshots; `tools-check.yml` regenerates
> the shared Swift and fails on any diff. All three have run green today.
> **Run them in that order.** On 2026-09-07 an `app-build` run was dispatched at the
> same moment as a push and died in 38 seconds on two Swift compile errors, on a runner
> billed at ten times the Linux rate, when the Linux job would have said the same thing
> for a tenth of the cost.
> The Swift is **not** unverified: `PVMCore` passes on Linux and on Apple Foundation,
> and a conformance test replays the engine's own answers over an 85-asset fixture and
> fails if the two implementations disagree about a path, a risk, an importance, a §4
> class, an action, an inferred place, a document holder or a reference join.

> ⚠️ **What is still NOT verified, and PF-01 stands.** Nothing has run on a physical
> device: no thermal behaviour, no jetsam, no real photo library, no PhotoKit writes.
> No real person has used the app. Every number in this repository was measured on a
> desk, and the two things every remaining gap is waiting for are **real photographs**
> and **real users**.

> ⚠️ **TOOLING — read before running anything.**
> **`./verify.sh` is the one local command.** It runs the engine tests, the constraint
> register, both evaluation self-tests, the Gate 2 gate, the generated-Swift check and
> the schema check. `./verify.sh --selftest` breaks something on purpose and proves the
> script still notices — it once printed "ok" under a failing test.
> **The console may be cp936.** Every Python entry point pins its own stdout to UTF-8 —
> copy that snippet into any new script that prints `⚠️`/`✅`, or it dies on `print`
> after doing all its work (PF-10).
> **The engine needs no dependencies.** `cd 30_ENGINE && python -m unittest discover -s tests`
> and `python eval/evaluate.py --library ../20_TIER0/study_assets/library/manifest.json`.
> Python 3.11+, nothing to install.
> **There is no Swift compiler here.** `download.swift.org` is denied by the egress
> policy, so Swift is only ever verified in CI. Do not try to install one.
> **Do not use `%-d` in a date format.** It is a glibc extension and raises on Windows.

**Must read (in order):** `PROJECT_STATE.md` → this file → `CONSTITUTION_UNDERSTANDING.md` → `OPERATING_RULES.md` → `VALIDATION_MATRIX.md`.

⚠️ **Before touching `30_ENGINE/`, read `30_ENGINE/CONSTRAINTS.md` and then the clauses it cites in `10_SOURCE_DOCS/_extracted_text/L1_PRODUCT_CONSTITUTION_v1.3.txt` and `L1B_*.txt`.** This file used to call L1 optional — *"only if you need product-level detail"* — and that framing is exactly how the engine came to be built without it (**PF-12**). The digests are convenient and incomplete by design. `python 30_ENGINE/check_constraints.py` tells you in one second whether the register still matches the sources, and now also whether its own summary table matches its own rows.
Then `30_ENGINE/README.md` — its "five decisions worth arguing with" is the part to disagree with, not the file list.

**One pattern this project keeps hitting, named so it can be watched for:**
*the thing that reports is never exercised by the thing it reports on.* It has appeared
five times — `verify.sh` printing "ok" under a failing test; a UI test that could pass
having reached nothing; a summary step buried under upload output; a safety audit whose
failure path had never executed; and an evaluation self-test that had never once called
`report()`, so a `NameError` in a new section passed every local check and surfaced only
on a full 10,000-asset run. Each is fixed and each fix is a self-test that fails when the
checker goes blind.

**Do NOT repeat:**
- Do not re-audit the documents. `DOCUMENTATION_MAP.md` is the finished result.
- Do not re-parse the .docx files. Use `10_SOURCE_DOCS/_extracted_text/*.txt`.
- Do not extract or read the Money OS zip. DEC-005 sealed it.
- Do not rebuild the governance files, the landing pages, the prototype, the test-library generator or the analyzers. All finished and re-verified.

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
