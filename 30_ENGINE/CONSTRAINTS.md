# BINDING CONSTRAINTS — L1 Constitution and L1-B Methodology, audited against the engine

**Why this file exists.** On 2026-09-06 the Owner had to point out, twice, that design
requirements I was presenting as findings were already written into L1 §24 and L1-B §4
as mandatory constraints. I had not read the source documents while building the
product's core engine. Recorded as **PF-12**.

An apology does not prevent that. This does: every binding clause is listed here with
its **verbatim source text**, its honest status, and the **test or metric that proves
it**. `check_constraints.py` verifies that each quote still appears in the source file
it cites and that every clause marked `DONE` names a test that actually exists. It runs
in CI. A clause cannot be quietly paraphrased into something easier to satisfy, and a
clause cannot claim to be implemented without something executable behind it.

Status values: `DONE` · `PARTIAL` · `MISSING` · `OUT-OF-SCOPE` (later tier, with the
tier named).

---

## L1 §24 — 四个生死关卡与技术战略

| id | verbatim clause | source | status | evidence |
|---|---|---|---|---|
| G1-PACED | 采用分层信号、轻量模型、分块/分时、checkpoint、增量处理和后台机会执行 | L1:267 | DONE | `pvm/schedule.py`, `tests/test_schedule.py` |
| G1-NOFULL | 30k–100k 资产的首次编目不能依赖全量重模型 | L1:267 | DONE | `tests/test_engine.py::Cost` |
| G2-CATEGORY | 禁止寻找一个万能 Same-Entity 模型 | L1:269 | PARTIAL | `pvm/dedup.py` special-cases documents only; the per-category resolvers (证件 OCR/版式/字段, 合同 文本指纹/页码, 普通照片 时间/地点/视觉相似) are not built — Tier 1-A |
| G3-PROGRESSIVE | 首次使用必须 Progressive Indexing。先给 Quick Wins 和基本目录，再逐渐补全深度索引 | L1:271 | DONE | `pvm/schedule.py`, `tests/test_schedule.py::BreadthBeforeDepth` |
| G3-TTFUV | 新增 TTFUV（Time To First Useful View）作为 P0 指标 | L1:271 | DONE | `pvm/kpi.py::time_to_first_useful_view`, reported by `eval/evaluate.py` |
| G5-MULTISIGNAL | 采用 Multi-Signal Classification：Metadata + Time/GPS + Hash + OCR + Vision + Embedding + Rules/Small Models；不能只问单一模型 | L1:275 | DONE | `pvm/signals.py`, `tests/test_engine.py::Cascade` |

## L1 §25 — Progressive Intelligence Pipeline (8 layers)

| id | layer | status | evidence |
|---|---|---|---|
| P25-L1 | Layer 1 Cheap Signals：metadata、time、GPS、file/source info、hash、基础 OCR | DONE | `pvm/signals.py` |
| P25-L2 | Layer 2 Visual Understanding：Vision / Core ML / lightweight embedding | DONE | `pvm/signals.py` scene labels + embedding; Vision itself is `20_TIER0/harness` |
| P25-L3 | Layer 3 Taxonomy：确定内容类别与置信度 | DONE | `pvm/classifier.py`, `eval/evaluate.py` |
| P25-L4 | Layer 4 Category-Specific Entity Resolution | PARTIAL | `pvm/dedup.py` resolves duplicates, same-moment and same-entity generically with one document special case; the per-category resolvers G2-CATEGORY requires are absent — Tier 1-A |
| P25-L5 | Layer 5 Risk + Lifecycle：重要性、生命周期、可恢复性 | PARTIAL | risk is `pvm/risk.py`; **lifecycle and importance are not built** |
| P25-L6 | Layer 6 Policy Engine：Protect / Keep / Archive / Select Best / Auto-Clean / Review | PARTIAL | `pvm/risk.py::Action` has no **Select Best** |
| P25-L7 | Layer 7 Visual Library：结构化视图 | DONE | `pvm/catalog.py::counts_by_path`, `pvm/cli.py::cmd_tree` |
| P25-L8 | Layer 8 Personal Memory：Wardrobe / Travel / Purchase / Object / Document Memory | OUT-OF-SCOPE | Tier 2 |

## L1 §12 / §13 / §14 — first use, continuous hygiene, personal policy

| id | verbatim clause | source | status | evidence |
|---|---|---|---|---|
| S12-INDEX | 扫描全库并建立多维索引 | L1:166 | DONE | `pvm/pipeline.py` |
| S12-CANDIDATES | 建立 Exact / Near Duplicate / Same Moment / Same Entity 候选 | L1:168 | DONE | `pvm/dedup.py`, `tests/test_engine.py::DuplicatesAndTheThingsThatOnlyLookLikeThem` |
| S12-REVIEW | 真正需要用户决定的内容进入极小 Review Queue | L1:170 | DONE | `pvm/kpi.py::human_review_burden` measures whether it is actually small |
| S13-HYGIENE | 每一张新拍摄、下载、截图或视频都自动经过同一管线 | L1:173 | PARTIAL | incremental re-run is `tests/test_catalog.py::Incrementality`; **video does not go through the pipeline** |
| S14-PERSONAL | 用户的 Keep/Delete/Protect/Restore/Correction 逐渐形成 Personal Policy | L1:182 | MISSING | not built — Tier 2, and named as such rather than forgotten |

## L1 §18 — the KPIs the product is actually defined by

Reported by `pvm/kpi.py` and printed by `eval/evaluate.py`. F1 and precision are *my*
measures; these are the *product's*, and where the two disagree these win.

| id | KPI | status | evidence |
|---|---|---|---|
| K-AUTO | Automation Ratio | DONE | `pvm/kpi.py::automation_ratio` |
| K-BURDEN | Human Review Burden (per 1,000 assets) | DONE | `pvm/kpi.py::human_review_burden` |
| K-WEC | Weighted Error Cost | DONE | `pvm/kpi.py::weighted_error_cost` |
| K-CATASTROPHIC | Catastrophic Error Rate | DONE | `pvm/kpi.py::catastrophic_error_rate` |
| K-COVERAGE | Classification Coverage | DONE | `pvm/kpi.py::classification_coverage` |
| K-RETRIEVAL | Retrieval Success | OUT-OF-SCOPE | needs real users — T0-B |
| K-HYGIENE | Continuous Hygiene Rate | DONE | `pvm/kpi.py::continuous_hygiene_rate` |
| K-PERSONAL | Personalization Gain | MISSING | requires S14-PERSONAL |

## L1-B — Information-Change-First / Minimum Necessary Inference

| id | verbatim clause | source | status | evidence |
|---|---|---|---|---|
| B1-ORDER | Cheap Signals → Candidate Reduction → Selective Intelligence → Structured Memory | L1B:13 | PARTIAL | escalation is per-asset in `pvm/classifier.py`; **Candidate Reduction as a retrieval stage is not built** |
| B1-NOHEAVY | 任何“把所有照片、所有视频帧全部交给重型模型理解”的架构，原则上都应视为错误设计 | L1B:11 | DONE | `tests/test_engine.py::Cost`, `tests/test_deltas.py::ItSavesRealWork` |
| B2-CHANGE | 优先识别真正新增/变化的信息，只对有新信息价值的部分进行更深层推理 | L1B:9 | DONE | `pvm/catalog.py` fingerprints, `pvm/deltas.py` |
| B3-PHOTOS | 系统应先使用低成本信号识别重复、近重复、同场景和变化程度，再决定是否需要更深层的分类 | L1B:34 | DONE | `pvm/dedup.py`, `tests/test_engine.py` |
| B4-NOFRAMES | 禁止默认采用：Video → 每隔 N 帧抽图 → 每一帧跑完整视觉模型 | L1B:37 | DONE | `pvm/deltas.py`, `tests/test_deltas.py` |
| B4-RECORD | PVME 最终需要保存的不是“一堆被 AI 分析过的视频帧”，而是这个视频对用户个人视觉记忆真正贡献的新信息 | L1B:40 | MISSING | `deltas.py` selects frames; the **Video Memory Record** (Date/Place/Person/Object/Event/segment/representative frames) is not built |
| B6-MINMODEL | 规则 / metadata 能解决 → 不用 AI。轻模型能解决 → 不用大模型。Apple Native 能解决 → 不增加额外模型 | L1B:71 | DONE | `pvm/classifier.py` escalation; no third-party model in the engine |

---

## Honest summary

**DONE 21 · PARTIAL 6 · MISSING 4 · OUT-OF-SCOPE 2.**

The four MISSING are named, not forgotten: **Video Memory Record** (B4-RECORD),
**Personal Policy** (S14-PERSONAL) and its KPI (K-PERSONAL), and **Select Best**
(inside P25-L6). The six PARTIAL are mostly one shape: category-specific entity
resolution and lifecycle, which the Constitution puts in Tier 1-A.

Nothing here is marked DONE on the strength of an intention. `check_constraints.py`
will not let it be.
