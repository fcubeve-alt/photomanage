# FULL AUDIT — every authority document, clause by clause, against what is built

**Read this first: nothing here has run on a phone.** This line said "there is no
app" until 2026-09-07 and by then that was false — `40_APP/` holds a SwiftUI application
with a Structure-First home, category browse, asset detail, search, memory and a review
queue, plus `PVMCore`, a port of the engine that CI compiles and tests on Linux and on
Apple's Foundation, and a conformance test that replays the engine's own answers and
fails if the two disagree.

What is still true, and is the thing to hold on to: **it has never run on a physical
device and no real person has ever used it.** CI builds it for the Simulator and takes
screenshots; the UI test suite has not yet had a fully green run. So PF-01 stands —
there are no device claims in this file — and every "DONE" below means *a clause is
satisfied by code that has been measured on a desk*, never that a user experienced it.

**Why this file exists (PF-12).** On 2026-09-06 the Owner had to point out that design
requirements I was presenting as findings were already mandatory in L1 §24 and L1-B §4.
I had not read the source documents while building the engine. The first version of
this register then repeated the mistake one level up — it audited only the sections I
had happened to read. **This version covers L1 §1–26, L1-B, and L2 Tier 0/1/2 in full.**

Every clause carries its status and the code or test behind it.
`check_constraints.py` runs in CI and fails when a quoted clause is no longer verbatim
in the source it cites, when a clause marked DONE names code that does not exist, or
when any non-DONE status carries no explanation. A constraint cannot be softened by
rewording it into this file, and cannot claim completion on an intention.

Status: `DONE` · `PARTIAL` · `MISSING` · `OUT-OF-SCOPE` (tier named) · `NOT-CODE`
(a principle with no single implementation — still requires an explanation).

---

## L1 §2 — 核心流程 (the ten steps the product is defined as)

| id | step | status | evidence |
|---|---|---|---|
| S2-UNDERSTAND | Understand：理解照片/视频内容 | PARTIAL | the engine consumes OCR text, scene labels and face clusters via `pvm/signals.py`, but produces none of them — Vision lives in `20_TIER0/harness`, and video is not understood at all |
| S2-CLASSIFY | Classify：尽可能细地归入有实际决策意义的类别 | DONE | `pvm/classifier.py`, `pvm/rules.py`, `eval/evaluate.py` |
| S2-INDEX | Index：内容、时间、地点、人物、物品、事件、风险多维索引 | DONE | all seven, in `pvm/catalog.py`: content and time and place from the assignments table, person and object and event from the entities and observations tables, risk and importance as their own indexed columns. Traversable in both directions — `pvm/catalog.py::sightings` from an entity to its assets, `pvm/catalog.py::entities_for` from one asset to everything it is indexed under. `pvm/catalog.py::index_coverage` counts each of them from the rows, and `eval/evaluate.py` prints the table: Time 100%, Content 94.8%, Place 44.1%, Person 15.4%, Event 9.2%, Object 0% — that last one because this corpus carries no scene labels for its 205 object assets, not because the index is missing |
| S2-RISK | Assess Risk：判断误处理的潜在损失和内容重要性 | DONE | the clause names two outputs and the engine produces both: 误处理的潜在损失 is `pvm/risk.py::classify_risk` (§6 R0–R6), 内容重要性 is `pvm/importance.py::assess` (I0–I4). They are genuinely different axes rather than one renamed — on the 10k library 1,102 assets (11.0%) sit two or more levels apart, a passport photograph grading R5/ORDINARY and a recurring person R3/TREASURED |
| S2-DECIDE | Decide：根据类别、风险、置信度、生命周期和可恢复性决定动作 | DONE | `pvm/risk.py::decide_action`, `pvm/risk.py::policy_table` |
| S2-CLEAN | Clean/Protect：该大胆清理的大胆清理，该保护的保护 | PARTIAL | the engine proposes and protects; it cannot execute anything — no PhotoKit write path exists outside the Tier 0 harness |
| S2-REMEMBER | Remember：把照片变成现实人物、物品、地点、文件、购买和事件的证据 | DONE | `pvm/memory.py` builds entities of all six kinds with evidence, `pvm/catalog.py::write_memory` persists them, `tests/test_memory.py` locks the claims it may not make, `pvm/cli.py::cmd_remember` answers L1-B's worked example. Objects and documents are **category-level** entities — see S3-ENTITY and T1B-RESOLVER, which track that limit rather than double-counting it here |
| S2-RETRIEVE | Retrieve：分类浏览、时间地点、自然语言和关系网络 | PARTIAL | all four paths exist: browse (`pvm/cli.py::cmd_tree`), timeline and places, the relation network from an entity (`pvm/memory.py::MemoryGraph.history`), and natural language (`pvm/intent.py`). PARTIAL because Intent Search is bounded by what is indexed — see S10-INTENT — and none of the four has been measured with real users, which is T0-B |
| S2-MAINTAIN | Maintain：每一张新照片进入后自动重复以上过程 | PARTIAL | incremental re-classification works (`tests/test_catalog.py`) and video now enters the pipeline (B4-RECORD). What is still missing is the automatic part: nothing schedules a run when new photos arrive — on a device that is `BGProcessingTask`, which is C-4 and lives in the app |
| S2-DERIVE | Derive Services：衣橱、旅行、购物、物品、提醒 | OUT-OF-SCOPE | Tier 2 / §15 — explicitly a later value layer, not skipped work |

## L1 §3 — the index dimensions

| id | dimension | status | evidence |
|---|---|---|---|
| S3-CONTENT | Content Taxonomy | DONE | `pvm/taxonomy.py`, `pvm/classifier.py` |
| S3-TIME | Time：Year → Month → Day → Moment | DONE | all four levels, in `pvm/classifier.py::_timeline` and `pvm/context.py::find_moments`, ported to `40_APP/PVMCore/Sources/PVMCore/Classifier.swift`. Moment is a capture session derived from neighbours, not a clock hour — an hour boundary splits a burst — and a lone photograph gets none. `tests/test_engine.py::Cascade` locks both |
| S3-PLACE | Place：Country → City → Place | PARTIAL | Country and City are indexed; the third level (a named place within a city) is not |
| S3-PERSON | Person | DONE | `pvm/classifier.py::_faces` |
| S3-ENTITY | Object / Entity：同一件衣服、设备、证件、商品 | PARTIAL | entities now persist and accumulate across the library (`pvm/memory.py::Entity`), so "every sighting of a suitcase" is answerable. **同一件** is not: telling one suitcase from another is per-category entity resolution (T1B-RESOLVER), so object and document entities stay category-level — and the answer says so out loud rather than implying an instance |
| S3-EVENT | Event：旅行、生日、会议、活动 | PARTIAL | three kinds now, all in `pvm/memory.py::_events`: 旅行 from a run of days away from home, a **day out** (`pvm/context.py::find_days_out`) for a day away that no trip covers, and a **gathering** (`pvm/context.py::find_gatherings`) for a capture session with two or more named people in it. PARTIAL because 生日 and 会议 need knowledge the engine does not have — a birthday needs a date only the user knows and a meeting needs a calendar — and inventing either from photo density would be a guess wearing a label
| S3-RISKDIM | Risk / Importance | DONE | both are indexed dimensions: the risk, importance and asset_class columns of the assets table in `pvm/catalog.py`, the first two each with their own index. `eval/evaluate.py` reports the library against both and prints the cross-tabulation |
| S3-LIFECYCLE | Lifecycle：Temporary / Active / Expired / Long-term | DONE | `pvm/risk.py::lifecycle_of`, `tests/test_engine.py::LifecycleIsWhenNotHowMuch` |
| S3-EQUIV | Equivalence Group | DONE | `pvm/dedup.py`, `tests/test_engine.py::DuplicatesAndTheThingsThatOnlyLookLikeThem` |
| S3-ONEASSET | 同一视觉资产同时拥有多个索引维度…底层只保存一个 Asset | DONE | `pvm/catalog.py` stores one asset row with many assignment rows; `tests/test_engine.py::Cascade` |

## L1 §4 — 精细 Visual Asset Taxonomy

| id | verbatim clause | source | status | evidence |
|---|---|---|---|---|
| S4-DECISION | 尽可能细，但只细到足以改变用户体验或处理决策 | L1:57 | DONE | `pvm/classifier.py` returns the deepest node the evidence supports and stops; `tests/test_engine.py::Cascade` |
| S4-CATEGORIES | 分类不是为了展示 AI 很聪明，而是为了改变整理、风险、生命周期和动作策略 | DONE | §4's thirteen 大类 are `pvm/importance.py::ASSET_CLASSES`, each carrying its 细分类示例 and 默认风险 verbatim, and every asset is stored under one, in the asset_class column of `pvm/catalog.py`. Two of the thirteen are not tree branches and never could be — 珍贵记忆 is a property of one asset, 连拍/同一时刻 a relation between assets — which is why the earlier attempt to map §4 onto the navigational tree stalled; `pvm/importance.py::classify_asset_class` takes both as arguments instead. A fourteenth entry, （§4 未描述）, exists so a fall-through says so rather than being filed under whichever class was nearest. It 改变动作策略 rather than only labelling: the class sets the importance baseline, and importance decides §8 pruning and the §14 ceiling. `tests/test_importance.py::TwoReadingsOfOneDocument` sweeps every node of the tree and fails when §4's 默认风险 band disagrees with what §6 assigns — it found two real disagreements on its first run |

## L1 §5–§9 — risk, philosophy, equivalence, ordering

| id | verbatim clause | source | status | evidence |
|---|---|---|---|---|
| S5-FORMULA | Category × Importance × Lifecycle × Confidence × Recoverability × Personal Preference → Action Policy | L1:101 | DONE | all six are inputs to `pvm/risk.py::Factors` and are read by `pvm/risk.py::decide_action`. Importance became an axis of its own on 2026-09-07 (`pvm/importance.py`); Personal Preference is derived by `pvm/personal.py::learn` and is now passed at run time by `pvm/pipeline.py` — until that commit `pvm/risk.py::decide_action` honoured a preference nothing ever supplied. Two of the six change the outcome in ways nothing else could: §8's 同样的相似度，在 Meme 和家庭照片上采取不同策略 is decided by Importance, and a §14 habit is stopped from reaching MEANINGFUL content by it |
| S6-SCALE | 建立 R0 Disposable / R1 Low Value / R2 Normal / R3 Personal / R4 Important / R5 Critical / R6 Irreplaceable 默认风险层 | T2:9 | DONE | `pvm/risk.py::Risk`, pinned to §6 by `tests/test_engine.py::TheRiskScaleIsTheConstitutionsNotMine` |
| S6-R6 | 老照片、特殊家庭影像 | L1:133 | PARTIAL | the level exists and protects; **detection is a conservative heuristic** (`pvm/pipeline.py::looks_irreplaceable`) because real irreplaceability is knowledge only the user has — that is §14, which is missing |
| S7-BALANCE | 产品不是以“零错误”作为唯一目标，而是优化 Automation Benefit 与 Weighted Error Cost 的平衡 | L1:141 | DONE | `pvm/kpi.py::automation_ratio`, `pvm/kpi.py::weighted_error_cost`, both printed by `eval/evaluate.py` |
| S7-RECOVERABLE | 允许 AI 判断偶尔出错，但尽量避免错误成为不可恢复的重大损失 | L1:138 | DONE | `pvm/risk.py::Recoverability`, enforced in `pvm/risk.py::Proposal` |
| S8-MARGIN | Same Moment + Same Subject + High Similarity + Low Risk → 选代表照，其余自动进入可恢复清理 | L1:144 | PARTIAL | the group is formed and `Action.SELECT_BEST` is issued, but **nothing selects the representative** — no sharpness, eyes-closed, framing or blur assessment exists (Tier 2-B) |
| S8-HARDNEG | 人物表情明显不同、关键动作不同、文档不同页面 → 不属于等价组 | L1:145 | DONE | `pvm/dedup.py`, `tests/test_engine.py::DuplicatesAndTheThingsThatOnlyLookLikeThem` |
| S9-ORDER | 先理解，才能正确整理；先整理，才能安全清理 | L1:153 | DONE | `pvm/pipeline.py` classifies before it relates and relates before it scores; `tests/test_catalog.py` |

## L1 §10–§14 — retrieval, indexes, first use, hygiene, personal policy

| id | verbatim clause | source | status | evidence |
|---|---|---|---|---|
| S10-BROWSE | Browse：用户知道类别，直接 Documents → IDs → Person → ID Card | L1:155 | DONE | `pvm/cli.py::cmd_tree` browses the tree and `pvm/classifier.py::_document_holder` grows the Person level, in §10's own ordering: a passport reachable under Documents > Identity > Jane Doe > Passports as well as on its type shelf. A cross-listing rather than a replacement, which §3 blesses — 同一 asset 可以出现在多个入口，但保留一个原始归属 — so both 'where are the passports' and 'where are Jane's documents' arrive. The name is read off the document by `pvm/resolver.py::holder_names`, which requires an explicit NAME/SURNAME/HOLDER/姓名 label followed by capitals: transcription, not the inference §16 forbids, and nothing derives anything further about the person. Two names on one document files under neither. Making this possible needed `pvm/taxonomy.py::extensible_branch` rather than adding Documents to EXTENSIBLE_ROOTS, so an invented Documents > Crypto still raises — `tests/test_browse_person.py` (14 tests) holds both halves |
| S10-TIMEPLACE | Timeline / Places：按年月日、城市、地点、旅行/事件浏览 | L1:156 | PARTIAL | 年月日 all work now (S3-TIME), as do city and trip; the missing piece is a *named place* within a city, which needs a place database this build does not have — S3-PLACE |
| S10-INTENT | Intent Search：用户直接说“找我的身份证正反面” | L1:157 | PARTIAL | `pvm/intent.py` resolves a sentence against what the library actually indexes — categories, people, places, remembered entities, exact time windows, media type, and 正反面 — in Chinese and English, and `pvm/cli.py::cmd_find` answers the Constitution's first worked example. It cannot answer the second, 找所有有气球的照片, because there is no open-vocabulary visual index; it names 气球 as a term it cannot search and **refuses to answer broadly** rather than returning the whole library. `tests/test_intent.py` (18 tests) is mostly about that refusal |
| S10-RELATIONS | Relations：从某个人、物品、订单、旅行进入，找到相关照片、截图、文件和收据 | L1:158 | PARTIAL | `pvm/memory.py::MemoryGraph.history` goes from a person, object, purchase, event or trip to its assets and `pvm/cli.py::cmd_remember` exposes it. The **join across categories** now exists too: `pvm/memory.py::_link_by_reference` puts a receipt, an order screenshot and a warranty document under one 订单 entity when they carry the same labelled reference — three assets under three different roots, reachable from each other. It is the same evidence §24 Gate 2 already trusts to decide two documents are the same thing, used one level up, and it refuses more than it accepts: a reference needs at least three digits, at least two assets must carry it, and there is no fuzzy matching on shop names or dates. `tests/test_relations_join.py` (11 tests) is mostly about the refusals. PARTIAL because a purchase with no reference number on it — the common case for a shop receipt — cannot be joined this way at all, and joining those needs the visual and semantic matching T1B-EMBEDDING and S2-UNDERSTAND track |
| S11-INFER | 无 GPS 时可以利用相邻时间照片、地标等推断，但必须保存置信度 | L1:161 | PARTIAL | `pvm/infer.py::infer_places` reads the photographs either side of an asset in time and claims the most specific thing they support: a city when both anchors agree on one, a country when they agree only on that, nothing when they disagree or are more than 25 km apart. 必须保存置信度 is a field on `pvm/infer.py::InferredPlace`, and the classifier records it under the signal name `geo:inferred`, never as an asset's primary category, and never at more than 0.80. On the 10k library it reaches 429 assets at mean confidence 0.53. `tests/test_infer.py` (27 tests) is mostly about the refusals. PARTIAL because 地标 — the other signal §11 names — needs vision and is not built, and because an inferred place does not yet join an asset to a Trip, so a photo without GPS taken during a trip is filed under the city and not the trip. That last one was measured before it was deferred rather than after: on the 10k library only 16 of the 429 inferred assets fall inside a trip window at all, and this corpus derives its Travel labels from GPS too, so all 16 would score as false positives and Travel precision would fall from 1.000 to 0.982. A small, unmeasurable gain against a measurable cost is not a trade worth taking blind |
| S11-EVENT | 时间 + 地点 + 人物 + 内容可以自动形成 Event / Trip 候选 | L1:162 | PARTIAL | 时间 + 地点 gives Trip (`pvm/context.py::_find_trips`) and Day Out (`pvm/context.py::find_days_out`); 时间 + 人物 gives Gathering (`pvm/context.py::find_gatherings`). All three reach the memory graph and none mints a browse folder, because Travel is a run of days and a Saturday afternoon on that shelf makes the shelf mean less. The bars are deliberately high — six photos for a day out, four photos and two named people for a gathering — for the reason `MIN_TRIP_ASSETS` exists: the first trip detector produced 53 trips of two photos each. On the 10k library this derives 1 trip, 0 days out and 3 gatherings. PARTIAL because 内容 is not yet a factor: the engine cannot say a session was a meal or a concert, which needs the scene understanding S2-UNDERSTAND tracks. `tests/test_events.py` (12 tests) |
| S12-INDEXALL | 扫描全库并建立多维索引 | L1:166 | DONE | `pvm/pipeline.py::run` |
| S12-CANDIDATES | 建立 Exact / Near Duplicate / Same Moment / Same Entity 候选 | L1:168 | DONE | `pvm/dedup.py::analyse` |
| S12-SMALLQUEUE | 真正需要用户决定的内容进入极小 Review Queue | L1:170 | DONE | measured, not asserted: `pvm/kpi.py::human_review_burden` |
| S13-HYGIENE | 每一张新拍摄、下载、截图或视频都自动经过同一管线 | PARTIAL | new stills re-enter automatically (`tests/test_catalog.py::Incrementality`) and video now enters too (`pvm/pipeline.py::_video_pass`, B4-RECORD) — this row said otherwise until 2026-09-07 and was stale. Still PARTIAL for the same reason as S2-MAINTAIN: nothing *schedules* a run when new photos arrive. On a device that is `BGProcessingTask`, which is C-4 and lives in the app |
| S14-PERSONAL | 用户的 Keep/Delete/Protect/Restore/Correction 逐渐形成 Personal Policy | L1:182 | PARTIAL | `pvm/personal.py` learns per-category preferences from a logged decision history (`pvm/catalog.py::record_decision`), and `pvm/risk.py::decide_action` now honours 系统以后可以更激进 below R4 while refusing it at R4+. `tests/test_personal.py` (19 tests) holds that line. PARTIAL because **no real user has ever fed it**: the mechanism and its limits are built and tested, the learning curve is not observed — that needs users, which is T0-B/Tier 2-G |

## L1 §16–§23 — boundaries, KPIs, validation, positioning

| id | verbatim clause | source | status | evidence |
|---|---|---|---|---|
| S15-DERIVED | Wardrobe / Clothing View | L1:189 | OUT-OF-SCOPE | Tier 2 §15 — an explicit later value layer that must derive from existing data, not skipped work. The data it has to derive from now exists: clothing and purchase entities with their sightings (`pvm/memory.py`) |
| S16-BOUNDARY | 对性格、健康、政治、宗教、亲密关系等敏感属性作推断 | L1:204 | DONE | `pvm/rules.py::MEDICAL_IS_DOCUMENT_ONLY`, `tests/test_engine.py::RiskRedLines` |
| S17-POSITION | 第一阶段不是 AI Photo Cleaner，而是 Autonomous Photo Organizer / Visual Library Manager | L1:206 | NOT-CODE | a positioning statement that shapes what gets built rather than a clause to implement; its executable consequence is that classification precedes cleanup, which is S9-ORDER |
| S18-KPI | 每 1,000 个资产需要用户人工判断多少 | L1:220 | PARTIAL | all eight are in `pvm/kpi.py::report` — Personalization Gain measured as review questions avoided rather than rules learned. PARTIAL because Retrieval Success cannot be self-reported: it needs real users on real tasks (T0-B) |
| S19-CONFUSION | Visual Asset Taxonomy：分类覆盖率、混淆矩阵 | L1:235 | DONE | `eval/evaluate.py` prints coverage and a confusion matrix over the scored roots — rows are the true root, columns what was filed, and an asset filed correctly *and* elsewhere appears in both cells so over-filing cannot hide |
| S19-RISKEVAL | Risk/Importance Classification：风险分级是否可靠 | L1:236 | PARTIAL | measured by `eval/evaluate.py::risk_evaluation`. The corpus carries no risk labels and does not need to: §6 grades risk *from the category* and the corpus labels categories, so ground truth is what `pvm/risk.py::classify_risk` returns for an asset's TRUE paths against what the engine returned for the paths it PREDICTED — the two differ exactly when a classification error propagates into a consequence error. Over the same scorable subset the classification uses: **99.7% exact (5,830 of 5,845), 15 graded too high, 0 graded too low, 0 crossing the never-delete floor.** And the claim that does not depend on those exclusions: of the 34 assets the engine proposed any action for, **0 have a true risk of R4 or above**. PARTIAL rather than DONE for one honest reason: only 17 scorable assets sit at R4+, because this corpus has few foreground documents — a perfect score over seventeen is evidence the mapping is wired correctly, not a rate, and the levels where being wrong is expensive are the ones this library is thinnest on |
| S19-FOURPATHS | Browse / Timeline-Places / Intent Search / Relations 四种找回路径 | L1:240 | PARTIAL | all four exist. PARTIAL because their success rates have not been measured — Tier 1-E wants 成功率、步骤数、耗时 on real tasks, which needs users |
| S20-PHILOSOPHY | 不要因为 AI 可能偶尔判断错，就把所有管理工作重新交还给用户 | L1:245 | NOT-CODE | the philosophy the KPIs operationalise; its measurable form is Automation Ratio against Human Review Burden, both of which are reported |
| S22-ENTRY | 核心指标新增 Retrieval Entry Share | L1:254 | OUT-OF-SCOPE | T0-B measures this with real users; nothing an engine can self-report |
| S23-STRUCTURE | 首页首先展示秩序和目录，而不是再次展示一条无限滚动的照片流 | L1:259 | PARTIAL | there is a home now: `40_APP/PVM/UI/HomeView.swift` opens on the tree and the counts — roots, review queue, search, memory — and there is no photo stream on it anywhere. This row said "there is no home, because there is no app" until 2026-09-07 and was stale. PARTIAL because §23's claim is about what a user experiences on first open, and nobody has opened it: the screen exists and is screenshotted by CI, the 首次全库自动编目与分类体验 §19 asks for has not been observed |

## L1 §24 — 四个生死关卡

| id | verbatim clause | source | status | evidence |
|---|---|---|---|---|
| G1-PACED | 采用分层信号、轻量模型、分块/分时、checkpoint、增量处理和后台机会执行 | L1:267 | DONE | `pvm/schedule.py`, `tests/test_schedule.py` |
| G2-CATEGORY | 禁止寻找一个万能 Same-Entity 模型 | L1:269 | DONE | `pvm/resolver.py` dispatches on category: 证件/文件 on OCR fields (identifier, holder, page), 截图 on the order reference, 物品 on appearance plus labels plus time, 普通照片 on 时间/地点/视觉相似. `pvm/dedup.py::_relate` no longer decides this itself — it delegates, and `tests/test_resolver.py::TheGateForbidsAUniversalModel` fails if one ladder ever answers every category again |
| G3-PROGRESSIVE | 首次使用必须 Progressive Indexing。先给 Quick Wins 和基本目录，再逐渐补全深度索引 | L1:271 | DONE | `pvm/schedule.py`, `tests/test_schedule.py::BreadthBeforeDepth` |
| G3-TTFUV | 新增 TTFUV（Time To First Useful View）作为 P0 指标 | L1:271 | DONE | `pvm/kpi.py::time_to_first_useful_view` |
| G4-NOTCLEANER | 商业定位禁止退化成 Cleaner | L1:273 | NOT-CODE | a commercial-positioning constraint; the engine's executable share of it is that cleanup is one action among seven in `pvm/risk.py::Action`, not the product |
| G5-MULTISIGNAL | 采用 Multi-Signal Classification：Metadata + Time/GPS + Hash + OCR + Vision + Embedding + Rules/Small Models；不能只问单一模型 | L1:275 | DONE | `pvm/signals.py`, `tests/test_engine.py::Cascade` |

## L1 §25 — Progressive Intelligence Pipeline

| id | layer | status | evidence |
|---|---|---|---|
| P25-L1 | Layer 1 Cheap Signals | DONE | `pvm/signals.py` |
| P25-L2 | Layer 2 Visual Understanding | PARTIAL | the engine consumes scene labels and embeddings; it produces none — see S2-UNDERSTAND |
| P25-L3 | Layer 3 Taxonomy | DONE | `pvm/classifier.py` |
| P25-L4 | Layer 4 Category-Specific Entity Resolution | PARTIAL | `pvm/resolver.py` decides 现实实体 / 版本 / 页面 / Same Moment as four distinct relations (`Relation.SAME_INSTANCE`, `OTHER_VERSION`, `OTHER_PAGE`, and the review case). PARTIAL only for objects, where no embedding exists — T1B-EMBEDDING |
| P25-L5 | Layer 5 Risk + Lifecycle：重要性、生命周期、可恢复性 | DONE | 重要性 `pvm/risk.py::Importance` — the scale sits beside the other §5 factor scales, and `pvm/importance.py` is where it is explained and assessed — 生命周期 `pvm/risk.py::lifecycle_of`, 可恢复性 `pvm/risk.py::recoverability_of` — three scales, three functions, all three read by `pvm/risk.py::decide_action` |
| P25-L6 | Layer 6 Policy Engine：Protect / Keep / Archive / Select Best / Auto-Clean / Review | DONE | `pvm/risk.py::Action`, `pvm/risk.py::policy_table` |
| P25-L7 | Layer 7 Visual Library | DONE | `pvm/catalog.py::counts_by_path`, `pvm/cli.py::cmd_tree` |
| P25-L8 | Layer 8 Personal Memory | OUT-OF-SCOPE | Tier 2. Its substrate now exists (S2-REMEMBER); what stays out of scope is the personal layer on top, which is S14-PERSONAL and separately tracked |

## L1-B — Information-Change-First / Minimum Necessary Inference

| id | verbatim clause | source | status | evidence |
|---|---|---|---|---|
| B1-ORDER | Cheap Signals → Candidate Reduction → Selective Intelligence → Structured Memory | L1B:13 | DONE | per-asset escalation is `pvm/classifier.py`; Candidate Reduction as a *retrieval* stage is `pvm/intent.py`, which narrows against stored rows and computes no new signal to answer a search. Its ceiling is what got indexed, which S10-INTENT tracks |
| B1-NOHEAVY | 任何“把所有照片、所有视频帧全部交给重型模型理解”的架构，原则上都应视为错误设计 | L1B:11 | DONE | `tests/test_engine.py::Cost`, `tests/test_deltas.py::ItSavesRealWork` |
| B2-CHANGE | 优先识别真正新增/变化的信息，只对有新信息价值的部分进行更深层推理 | L1B:9 | DONE | `pvm/catalog.py::signals_fingerprint`, `pvm/deltas.py` |
| B3-PHOTOS | 系统应先使用低成本信号识别重复、近重复、同场景和变化程度，再决定是否需要更深层的分类 | L1B:34 | DONE | `pvm/dedup.py` |
| B4-NOFRAMES | 禁止默认采用：Video → 每隔 N 帧抽图 → 每一帧跑完整视觉模型 | L1B:37 | DONE | `pvm/deltas.py::select_keyframes`, `tests/test_deltas.py` |
| B4-RECORD | PVME 最终需要保存的不是“一堆被 AI 分析过的视频帧”，而是这个视频对用户个人视觉记忆真正贡献的新信息 | L1B:40 | DONE | video enters `pvm/pipeline.py::_video_pass`, which gates frames through `pvm/deltas.py::select_keyframes` and writes one row per video — Date / Place / Person / Object / Event / segments / representative frames — via `pvm/catalog.py::write_video_record`. `pvm/cli.py::cmd_video` shows it. `tests/test_memory.py::VideoReachesThePipeline` measures it: 61 of 1,800 frames on a 60-second clip, 245 seconds of deep work skipped. Frames arrive through a caller-supplied callable because the engine has no decoder; without one a video is still catalogued from its metadata and the video counter stays at zero rather than implying it looked inside |
| B6-MINMODEL | 规则 / metadata 能解决 → 不用 AI。轻模型能解决 → 不用大模型。Apple Native 能解决 → 不增加额外模型 | L1B:71 | DONE | `pvm/classifier.py` escalation; the engine carries no third-party model |

## L2 Tier 1 — 核心能力可行性 (the tier this engine actually belongs to)

| id | requirement | status | evidence |
|---|---|---|---|
| T1A-TAXONOMY | Tier 1-A Visual Asset Taxonomy：Coverage、Precision/Recall、Confusion Matrix、Unknown 比例 | PARTIAL | coverage, precision, recall and the confusion matrix are all in `eval/evaluate.py`, over the 11-root navigational tree. The §4 scheme now exists and every asset carries a class (S4-CATEGORIES), and `eval/evaluate.py` reports the library's distribution across it — but **it is not scored**, because the 10k corpus carries no §4 labels to score against. Adding them means re-labelling the corpus along a second axis, which is a corpus job rather than an engine one |
| T1A-UNKNOWN | 允许 Unknown + confidence，不强迫每个资产进入错误类别 | DONE | `pvm/verdict.py::REVIEW_FLOOR`, `pvm/classifier.py::_unfiled` |
| T1B-RESOLVER | Tier 1-B Category-Specific Entity Resolver, per-category | DONE | `pvm/resolver.py`, `tests/test_resolver.py` (26 tests), measured by `eval/evaluate_entities.py` — 24 hand-built pairs, 9 hard negatives, 0 false merges, 0 false splits, 12.5% to review. Objects across occasions are deliberately downgraded to Review rather than guessed; see T1B-EMBEDDING |
| T1B-FALSEMERGE | Document 类别单独统计 False Merge / False Split | PARTIAL | measured and reported separately: **Document False Merge 0 of 6, False Split 0 of 5** (`20_TIER0/evidence/GATE2_ENTITY_RESOLVER_2026-09-06.md`), across four hard negatives — two passports on one template, two ID cards on one template, page 1 of two contracts sharing boilerplate, two receipts from one shop. PARTIAL because **the pairs are hand-built**: the 10k corpus has no same-entity labels, so this is evidence about the hard cases and not a population rate |
| T1B-EMBEDDING | Product/Object：同一设备、商品、家中物品的不同角度…视觉 embedding + attribute + temporal evidence | MISSING | there is no visual embedding, so two views of one chair cannot be joined and one chair on two days cannot be told from two identical chairs. `pvm/resolver.py::_resolve_object` answers UNCERTAIN in both cases rather than guessing — Tier 1's 「Review Queue 优先」 downgrade taken deliberately: object recall 33%, object false merges 0. **Blocked on evidence, not on effort**: wiring `VNGenerateImageFeaturePrintRequest` into `AssetSignals.embedding` is a day's work, and choosing the distance at which two feature prints are the same object is not, because there is nothing here to measure it against. `20_TIER0/study_assets/library` holds a manifest and PIL-drawn placeholder images, not photographs, and a threshold fitted to flat rendered rectangles would not survive contact with a real camera. Shipping an unmeasured threshold on the category where a false merge is expensive is the trade Tier 1-B exists to prevent, so this waits for real images — which is also what T0-A and T0-B need |
| T1C-LIFECYCLE | Tier 1-C Visual Lifecycle Engine，重点是 Suggest Delete 的 False Positive | PARTIAL | `pvm/risk.py::lifecycle_of` and the policy table exist, and the rate is now measured by `eval/evaluate.py::action_evaluation`: **0 false positives out of 21 removals offered, and 0 removals missed** on the 10k library. Derivable by the same argument as S19-RISKEVAL — the action is a function of the factors, the factors of the category, and the corpus labels categories — so the counterfactual is what `pvm/risk.py::decide_action` would propose given a perfect classification. PARTIAL because 21 offers out of 10,000 is a very conservative engine and 0% over 21 is evidence that the classifier and the policy table agree, not a rate to quote at scale. The first version of the counterfactual withheld the capture date and read 85.7%: `lifecycle_of` with no age returns TEMPORARY rather than EXPIRED, so every screenshot the engine correctly offered came back a false positive. A counterfactual that changes more than the one thing being tested is not a counterfactual |
| T1C-ZEROAUTO | 高风险类别自动删除率必须为 0 | DONE | `pvm/kpi.py::catastrophic_error_rate`, audited in `eval/evaluate.py` against written rows |
| T1D-MULTIINDEX | Tier 1-D 一个 Asset 同时挂载 Content / Time / Place / Person / Object / Event 索引 | DONE | six of six, from one asset, via `pvm/catalog.py::entities_for` — the clause is specifically about what hangs off a single asset, and Person, Object and Event were previously reachable only by starting from an entity and walking to its sightings, which answers "where have I seen this bicycle" and cannot answer "what is in this photograph". The index that makes it cheap already existed; nothing was asking. Counted rather than asserted by `pvm/catalog.py::index_coverage`, surfaced by `pvm/cli.py::cmd_why` and by the app's asset detail screen, and the §11 provenance travels with each row so a hedged place cannot render as a stated one |
| T1E-PATHS | Tier 1-E 四种找回路径各挑 2-3 个真实任务测试成功率 | MISSING | this row said 'two of the four paths do not exist' until 2026-09-07 and was stale — all four have existed since S10-INTENT and S10-BROWSE landed, and S2-RETRIEVE and S19-FOURPATHS both said so while this one did not. It is still MISSING, for the reason that was always underneath: 成功率、步骤数、耗时 on 真实任务 are measurements of people using the product, and no person has used it |

## L2 Tier 2 — 完整体验与规模化

| id | requirement | status | evidence |
|---|---|---|---|
| T2A-POLICY | Tier 2-A Policy Table：每个风险层在不同置信度/可恢复条件下的动作 | DONE | `pvm/risk.py::policy_table`, generated from the code it documents |
| T2A-PASS | 高风险类别（R4-R6）零自动删除，低风险类别（R0-R1）能大量自动处理 | DONE | `tests/test_engine.py::ThePolicyTable`, `pvm/kpi.py::catastrophic_error_rate` |
| T2B-SELECTBEST | Tier 2-B 代表照选择逻辑：清晰度、闭眼/表情、构图、曝光、运动模糊 | MISSING | `Action.SELECT_BEST` is issued but nothing selects — no image-quality assessment of any kind exists |
| T2B-VALUELOSS | Significant Value Loss Rate | MISSING | cannot be measured until T2B-SELECTBEST exists |
| T2C-TTFUV | 目标 <30 秒出现第一批价值、<2 分钟形成基本 Visual Library | DONE | measured 2.8 s at 10k and 28 s at 100k — `pvm/kpi.py::time_to_first_useful_view` |
| T2C-INGEST | 验证新增照片能否增量处理，不需要周期性全库重扫 | DONE | `tests/test_catalog.py::Incrementality`, `pvm/kpi.py::continuous_hygiene_rate` |
| T2D-HOME | Tier 2-D 完整 Structure First 首页原型 | OUT-OF-SCOPE | needs an app; the 82 hand-authored prototype pages in `20_TIER0/study_assets/prototype` have no engine behind them |
| T2E-ABLATION | 输出 ablation：只 OCR、只视觉、组合信号分别表现如何 | DONE | all three arms plus full, in `eval/evaluate.py::run_ablation`, with a per-root table because an averaged F1 hides the shape of the answer. Ablation by *budget* could only ever express "how far up the ladder did we climb" — the budget is a ceiling and TEXT sits above VISUAL — so the arms strip signals instead (`eval/evaluate.py::_stripped`). The finding: **the two expensive signals do not overlap.** People scores 0.995 with vision and 0.000 without; Documents and Purchases score 1.000 with OCR and 0.000 without; Places, Screenshots, Travel and Timeline come off the free metadata row at 0.94–1.00. Macro F1 is 0.997 full, 0.851 OCR-only, 0.708 vision-only, 0.563 metadata-only. Neither expensive signal can stand in for the other, so the question C-1 answers is not whether to run OCR but on which assets — and the cost of getting that gate wrong is a whole category, not a few percent |
| T2F-ECONOMICS | 规模化单位经济 10k / 100k / 1M | OUT-OF-SCOPE | Tier 2-F, commercial modelling rather than engine work |
| T2G-LEARNING | Global Policy + Personal Policy 反馈学习 | PARTIAL | the loop exists end to end: decisions are recorded, a policy is derived on read, it changes the action, and `pvm/kpi.py` reports the review questions it avoided. What cannot be shown here is Review volume falling **over time for a real user** — that is the Tier 2-G measurement and it needs people |

---

## Honest totals

**91 clauses audited — counted by `check_constraints.py`, and the table below is now
checked against that count rather than remembered.** It previously claimed to be
generated and was typed: it read 36 DONE and 11 MISSING when the register held 48 and
5 at the time, and its own numbered list of the MISSING skipped item 4. That is this project's
recurring failure — the thing that reports is never exercised by the thing it reports
on — so `check_constraints.py` now fails when any cell here disagrees with the rows.

| status | count | share |
|---|--:|--:|
| DONE | 52 | 57% |
| PARTIAL | 26 | 29% |
| MISSING | 4 | 4% |
| OUT-OF-SCOPE (tier named) | 6 | 7% |
| NOT-CODE (principle, explained) | 3 | 3% |

**57% of the audited clauses are fully satisfied, and that is by an engine that does
not ship.** The 29% PARTIAL is the number to look at hardest: a partial clause passes
its tests and still does not do what the document asks, which is a more comfortable
place to hide than a gap.

**The four MISSING, in the order they would hurt:**
1. **T1B-EMBEDDING** — a visual embedding for objects. The resolver separates
   documents, screenshots and photographs cleanly; objects are the one category where
   it can only refuse to answer, because nothing joins two views of one chair or
   separates one chair on two days from two identical chairs. It is the ceiling on
   S3-ENTITY, on Object Memory, and on the open-vocabulary index S10-INTENT needs to
   answer 找所有有气球的照片. Blocked on real photographs, not on effort.
2. **T2B-SELECTBEST** — nothing selects a representative frame, so `SELECT_BEST` is
   an action the engine can name and cannot perform. Sharpness, closed eyes, framing
   and motion blur all need real images to be assessed or calibrated against.
3. **T1E-PATHS** — success rates for the four retrieval paths on real tasks. All four
   paths exist now, so this is no longer blocked by missing code. It is blocked on
   people, and so is every other measurement in the same family.
4. **T2B-VALUELOSS** — Significant Value Loss Rate, blocked by item 2.

**What the remaining PARTIAL clauses are mostly waiting for** is one of two things,
and neither is engineering time:
- **Real photographs.** The study library is PIL-drawn placeholders with a manifest.
  A visual embedding threshold fitted to flat rendered rectangles would not survive
  contact with a camera, and shipping an unmeasured one on the category where a false
  merge is expensive is the trade Tier 1-B exists to prevent.
- **Real users.** Retrieval Success (§18), the four paths' success rates (Tier 1-E),
  and whether a Personal Policy actually reduces review volume over time (Tier 2-G).
  The mechanisms are built and tested; the curves cannot be invented.

**The two defects this audit found in code that was already written:**
- **S6-SCALE.** The previous `risk.py` used R0–R6 — the identifiers §6 and Tier 2-A
  define — with meanings I had invented. R6 meant "not understood" where the
  Constitution means "irreplaceable, highest protection"; receipts sat below their §6
  placement and people above it. Every row of the catalogue read wrong against the
  document that defines it. Fixed, and pinned by a test that compares the enum to §6
  clause by clause.
- **Byte identity behind a classification gate.** An exact duplicate the classifier
  could not identify was routed to Review, so the one action the system can genuinely
  automate was the one it refused to take — the trade §7 exists to forbid. Fixed.
