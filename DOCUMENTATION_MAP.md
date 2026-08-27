# DOCUMENTATION MAP
Personal Visual Memory Engine — Bootstrap / Documentation Audit
Audit date: 2026-08-22 · Auditor: Claude Code (Session 001)

## 1. Authority hierarchy (as instructed by Owner + Launch Instruction v1.0)

| Level | Role | Canonical document |
|---|---|---|
| L1 | **WHAT** — product truth | `10_SOURCE_DOCS/Personal_Visual_Memory_Engine_v1.3_Product_Constitution.docx` |
| **L1-B** | **HOW THE ARCHITECTURE MUST BE BUILT** — Information-Change-First / Minimum Necessary Inference | `10_SOURCE_DOCS/PVME_Information_Change_First_Methodology_Update_v1.0.docx` → digest `ARCHITECTURE_METHODOLOGY.md` |
| L2 | **NOW** — what must be proven first | `10_SOURCE_DOCS/P020Test20EXECUTION%20INDEX_v1.0.docx` + Tier 0/1/2 **v1.1** |
| L3 | **HOW TO WORK** | `10_SOURCE_DOCS/Cross_Project_Engineering_Playbook_v1.1_...docx` |
| L4 | Capability library (not requirements) | Skills/MCP available in this environment + Project M Preflight Spec (method only) |
| L0 | Launch/assembly instruction (one-shot, now consumed) | `10_SOURCE_DOCS/Personal_Visual_Memory_Claude_Code_正式启动指令_v1.0.docx` |

Plain-text extractions of every document above live in `10_SOURCE_DOCS/_extracted_text/`
(regenerate with `python 10_SOURCE_DOCS/_extracted_text/docx_to_text.py <file.docx>`).
**Search the .txt files; do not re-parse the .docx.** (Playbook T-02, T-07)

## 2. Canonical document register

| # | Document | Level | Version | Status | Notes |
|---|---|---|---|---|---|
| D1 | Personal Visual Memory Engine — PRODUCT CONSTITUTION | L1 | **v1.3** (2026-08-20) | **AUTHORITATIVE** | 26 sections. Defines Visual Library architecture, Taxonomy, R0–R6 risk ladder, Equivalence Margin, Progressive Intelligence Pipeline (8 layers), Gates 1–5, KPIs, Retrieval Entry, Monetization Guardrail. Only v1.3 exists locally; v1.1 referenced but not present (not required). |
| D2 | P0 Kill Test — MASTER EXECUTION INDEX | L2 | **v1.0** (2026-08-20) | **AUTHORITATIVE** | Sequencing controller. One Tier at a time. Gate file required before next Tier. |
| D3 | P0 Kill Test Tier 0 — 生死开关 | L2 | **v1.1** (2026-08-20) | **AUTHORITATIVE / CURRENT TIER** | Workstreams A (device), B (retrieval entry), C (real payment signal). |
| D4 | P0 Kill Test Tier 1 — 核心能力可行性 | L2 | **v1.1** | AUTHORITATIVE / **LOCKED** | Read-only until Tier 0 gate passes. |
| D5 | P0 Kill Test Tier 2 — 完整体验与规模化 | L2 | **v1.1** | AUTHORITATIVE / **LOCKED** | Read-only until Tier 1 gate passes. |
| D6 | Cross-Project Engineering Playbook | L3 | **v1.1** | **AUTHORITATIVE** | E-01..E-15, S-01..S-10, F-01..F-12, Bootstrap Checklist, §5A Context/Token Protocol T-01..T-17. Header text says "v1.0" internally; filename and Owner both say v1.1 — treated as v1.1. |
| **D8** | **PVME 底层方法论更新 — Information-Change-First / Minimum Necessary Inference** | **L1-B** | **v1.0** (2026-08-24) | **AUTHORITATIVE** | Binds all architecture and model decisions. Explicitly does *not* change product goals, taxonomy, risk grading, lifecycle, retrieval, or the Tier 0 execution order. Digest + conflict review: `ARCHITECTURE_METHODOLOGY.md` |
| D7 | Claude Code 正式启动指令 | L0 | v1.0 | CONSUMED | Identical in substance to the Owner's chat launch prompt. Executed by this session. |

## 3. Superseded / duplicate / out-of-scope (moved, nothing deleted)

`90_ARCHIVE/SUPERSEDED/`
| File | Superseded by | Delta |
|---|---|---|
| `P0 Kill Test Tier0 生死开关.docx` | Tier 0 **v1.1** | **Material change.** Old: any of A/B/C FAIL → stop entirely. New: A or B FAIL → NO-GO/PIVOT; **C FAIL → COMMERCIAL MODEL PIVOT only, does not kill the product.** |
| `P0 Kill Test Tier1 核心能力可行性.docx` | Tier 1 v1.1 | Version stamp only — content identical. |
| `P0 Kill Test Tier2 完整体验与规模化.docx` | Tier 2 v1.1 | Prerequisite clause updated to allow entry after a completed Commercial Model Pivot. |
| `Cross_Project_Engineering_Playbook_v1.1_... (1).docx` | Playbook v1.1 | **Byte-identical duplicate** (md5 `f84ce3fd…`). Pure download artifact. |

`90_ARCHIVE/OTHER_PROJECT_MONEY_OS/`
| File | Disposition |
|---|---|
| `Project_M_Master_Development_Package_v1.3.1_COMPLETE.zip` | **OUT OF SCOPE — DO NOT IMPORT.** Money OS / Project M (M1 Digital Worker, M2-A LUVYMIA, M2-B Monetools, M2-C Cubewithin). Owner instruction and Playbook §6 both forbid bringing its business content into this project. Left zipped and unextracted on purpose. Only the *engineering lessons* already distilled into Playbook v1.1 carry over. One reusable method — the "preflight before installing tools" discipline from its Skills Spec — is extracted to `_extracted_text/L4_SKILLS_PREFLIGHT_SPEC_v1.0_from_ProjectM.txt` for reference only. |

## 4. Conflicts found and how resolved

| ID | Conflict | Resolution |
|---|---|---|
| C-1 | Two Tier-0 docs with contradictory kill rules (unversioned vs v1.1) | v1.1 wins. Recorded as **DEC-002**. Old file archived so it cannot be executed by accident. |
| C-2 | Playbook internal title says "v1.0", filename/Owner say "v1.1" | Same artifact. Treated as **v1.1**. No action. |
| C-3 | Byte-identical Playbook duplicate `(1).docx` | Archived. |
| C-4 | Constitution §19 lists 9 new P0 validation items; Execution Index forbids building them now | **No real conflict.** §19 is a scope declaration for the *whole* P0 programme; the Index assigns them to Tier 1/Tier 2. Tier 0 stays narrow. Recorded as **DEC-003**. |
| C-5 | Constitution assumes on-device iPhone validation; current environment is Windows-only with no Mac | **Real, blocking, environmental.** Not a document conflict. Handled via `REQUIRES_MAC` / `REQUIRES_DEVICE` tagging in `VALIDATION_MATRIX.md`. Recorded as **DEC-004**. |

## 5. Gaps — documents referenced but absent

- **No P1 / P2 documents exist.** Owner's prompt says "P0、P1、P2". The folder contains only a **P0** programme split into **Tier 0 / Tier 1 / Tier 2**. Reading of the Execution Index confirms P1/P2 are not separate docs — "P0/P1/P2" in the launch prompt maps to **P0 Tier 0 / Tier 1 / Tier 2**. No missing file; naming ambiguity only. Recorded as **DEC-001**.
- No standalone Skills/Tools document specific to this project. L4 capability selection is therefore made per task from the live environment.
- Product Constitution v1.1 is referenced by v1.3 but not present locally. Not needed — v1.3 is self-contained.
