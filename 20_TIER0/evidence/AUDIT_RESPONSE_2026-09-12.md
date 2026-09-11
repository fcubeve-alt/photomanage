# 第二次独立复核（2026-09-12）逐条回应

**被复核的 HEAD：** `4eea7e6` · **回应的 HEAD：** 本次提交
**复核方式：** 只读 · **本次回应：** 修改了代码、测试、CI 与文档

---

## 先说结论：这次审计基本全对

上一轮我把 24 条审计意见分成"落实"和"审计写错了"两类，并在这里记了两条审计的错误。
**这一轮我没有找到任何一条审计写错的地方。** 时点差异（分支领先 74 而不是 67）也如它自己
所说不是造假，是我写下那句话之后又提交了。

而且它指出的最要命的一条，是我上一轮的总结本身：

> "整改报告继续存在项目此前反复出现的同类问题：声明比可验证事实走得更远。"

这是对的，而且具体。下面按它的清单逐条对照。

---

## 我说过而当时不成立的话

这些是我上一轮写下的、经不起检查的句子。列在最前面，因为它们才是这次审计真正的发现。

| 我说的 | 实际 |
|---|---|
| "CI 全绿" | **假。** 同一个 HEAD 上 `Tooling check` 是失败的。我列了 4 个工作流的表格，漏掉了第 5 个——而漏掉的那个恰好是红的 |
| "82 个 prototype 页面已加 noindex" | **假。** 生成器加了，**82 个已提交文件一个都没有**。我改了生成器却没重新生成 |
| "所有照片写入都被结构性强制经过 `permitWrite`" | **过强。** 扫描器把 `LibrarySafety.swift` 整个排除了，在那个文件里直接写 `performChanges` 可以通过 |
| "`nonisolated` 让从主 Actor 调用变成编译错误" | **错。** `nonisolated` 只表示不受 Actor 隔离，可以从任何线程调用 |
| "出现联网代码就会构建失败" | **过强。** 那个检查只在本地 `verify.sh` 里，GitHub CI 根本没跑它 |
| "这个 App 不联网" | **不准确。** StoreKit 会与 Apple 通信 |
| "购买/恢复/取消/退款全流程可在模拟器跑通" | **把"能跑"写成了"跑过"。** 一次都没跑过 |
| "CI 工具版本已固定" | **假。** 工作流注释写着 Pinned，下一行是 `brew install xcodegen` |
| "数据迁移已实现并有测试" | **一半。** 有测试，但测的是改了版本号的当前结构，证明不了真实迁移 |

---

## P1-1 · 数据库迁移（审计称"非常接近 P0"）—— 三个缺陷全部确认，已重写

这是本次最实质的修改。

**缺陷一：无版本记录的旧库被当成新库。** 确认。`createSchema()` 会把 `meta` 表造出来，
所以在它之后读版本，"没记录过"和"刚建的"都读出 0。而 **Swift 端直到 2026-09-11 才开始
写 `schema_version`**——在那之前每个 Swift 写出的目录都是无版本且列是旧的，全部会被判为
新文件、盖上当前版本、永不迁移。

修法：在 `createSchema()` **之前**查 `sqlite_master`（唯一不需创建就存在的表）与 `meta`。
`有表 && 无版本` → 新增的 `Plan.unversionedLegacy`，按比一切都旧处理。

**缺陷二：只删行不改结构。** 确认，而且这一条让整个第一版迁移等于没写。`DELETE FROM assets`
不会给表加一列。修法：把派生表 **DROP 掉**，让 `createSchema()` 按当前形状重建——这在这个
产品里可行，因为派生表没有任何不能重算的东西。用户写的两张表改为
`RENAME → createSchema() → INSERT…SELECT → DROP` 逐列搬运，旧表缺的列用字面量兜底。

搬运带出一个新问题，一并修了：重命名表会带走它的索引，所以第一次 `createSchema()` 时
`idx_decisions_path` 的名字还被旧表占着而被跳过，旧表丢弃后索引就没了。搬运完成后**再调
一次 `createSchema()`** 补索引，`testTheRebuiltTablesKeepTheirIndexes` 钉住。

**缺陷三：测试不是真实旧 schema 测试。** 确认。新 fixture 把当前结构拆掉——`DROP TABLE
assets` 后用旧 DDL 重建（无 `media_type` / `importance` / `asset_class` /
`importance_why`），最坏情况再 `DROP TABLE meta`。核心断言不再是版本号：

```swift
INSERT INTO assets(asset_id, signals_fp, engine_fp, asset_class, media_type, importance)
```

**迁移前必须失败，迁移后必须成功。** 那条 INSERT 失败就是真实的崩溃现场。

**另外按审计建议加的：** `missingColumns()` 用 `PRAGMA table_info` 核对本次构建要写的列
与文件实际有的列，`Outcome.succeeded` 要求差集为空——**声称成功的迁移现在由文件作证，
不再由它自己盖的版本戳作证**。这一行也出现在 App 内诊断报告里（`SCHEMA GAPS:`）。

`50_LAUNCH/DATA_MIGRATION.md` 已按新设计重写。

## P1-2 · CI 不是全绿 —— 确认，已修

`Tooling check` 的 `Generators are deterministic` 失败，原因就是 P1-3：生成器改了、产物
没重新生成。已重新生成全部 82 个文件（唯一的差异就是那 5 行 noindex，别无其他），并双跑
校验产物逐字节一致。

**我不会再用"CI 全绿"概括一个我只看了 4 个工作流的 HEAD。**

## P1-3 · noindex 没进入生成产物 —— 确认，已修

82 个文件现在全部带 `<meta name="robots" content="noindex,nofollow">`。

## P1-4 · 守卫没接入 GitHub CI —— 确认，已修

新增 `.github/workflows/guards.yml`，**无路径过滤**，每次 push 和 PR 都跑：
`check_no_photo_writes` / `check_no_network` / `generate_legal --check` /
`check_repo_reality --ci` / `check_schema` / `generate_shared --check`，且每个先跑自检
再跑正式检查——否则"0 个问题"和"扫描器坏了"长得一模一样。

审计对 `LibrarySafety.swift` 被整体豁免的批评也确认了，而且**豁免根本没必要**：那个文件
只在一条文档注释里提到 `performChanges`，而注释行本来就被跳过。允许列表现在是空集。

`check_repo_reality` 新增 `--ci`：在 CI 里网络失败 = 检查没跑 = 失败，而不是降级为
"未验证"后顶着绿勾过去。自检覆盖了这条新路径。

## P1-5 · StoreKit 全流程没有跑通证据 —— 确认，已把措辞改回事实

代码存在且编译通过，**流程一次没跑过**。`.storekit` 文件格式本身也没在 Xcode 里打开验证过。
`50_LAUNCH/README.md` 第 6、7 项已从 ✅ 改为 ⏸，并写明需要一台 Mac 手动走一遍。
我没有去补一套我无法在本地验证的 StoreKitTest——那会是同一个错误再犯一次。

## P1-6 · 真机四项仍是零数据 —— 确认，没有变化

A3 生存性、删除→恢复、真实照片准确率、A1 规模。这一批修改一项都没有推进它们。

## P2 逐条

| 条目 | 处理 |
|---|---|
| 文件保护用 `try?` 静默吞掉失败 | `protectOnDisk` 改为返回失败列表；并**读回**保护等级核对（写入成功 ≠ 等级生效，无密码设备上 iOS 会降级）；结果进诊断报告。另外在迁移之后**再应用一次**——首次调用时 SQLite 还没写过，`-wal`/`-shm` 根本不存在 |
| `nonisolated` 注释与语义不符 | 注释改正。它保证的是反方向（不能被挪回主 Actor，否则测试编译失败），不保证调用方不在主线程 |
| 缺少生产入口的线程测试 | 新增 `testTheProductionDepthPassRunsItsWorkOffTheMainThread`：驱动 `runDepthPass`（`PlanView` 按钮调的那个入口），读回 `offMain` 实际把工作放在哪个线程 |
| 取消旧任务后进度交错 | 加了 generation 计数；`await` 回来后不是当前代就不写 `stats`/`phase` |
| "不联网"需要写明 StoreKit 例外 | 隐私政策新增"唯一的例外：StoreKit"一节（中英双语），条款、支持页、定价提案、DECISIONS 的相关措辞一并改为"不向开发者或任何第三方传输" |
| `check_repo_reality` 应 fail closed | 见 P1-4 |
| XcodeGen 实际没固定 | 注释里的 "Pinned" 是假话，已改为说明它没固定、为什么（需要可验证的校验和）、以及把解析到的版本记进 run summary。**五个工作流都改了** |
| CodeQL 没覆盖 Swift | 保持 Python 范围，不改描述为"已完整覆盖" |
| 崩溃处理器需要真实崩溃测试 | 未做，登记为开放项。回溯 API 的 async-signal-safe 程度这一条审计说得对：`backtrace_symbols_fd` 是这组里唯一不 malloc 的，但"不保证"比"保证"更准确 |

## 一个本次没有解决、也不打算叫它"环境问题"的东西

修完之后跑 `app-build`，`testDrillDownReachesADocumentAndExplainsIt` 失败：找不到
`browse-Documents`——而同一次运行抓下来的首页文本里 Documents 就在那儿，计数 7。
重跑一次，全绿。

**按规则这算确认为抖动，但它不是没有代价的抖动。** `ScreenshotTests.swift` 里已经写过
一模一样的症状和诊断（`row()` 的滚动时序），日期是 2026-09-07；这是第二次。两个数据点
说明这条测试在这个 runner 镜像上是间歇性的，而一条间歇性的测试对它守护的属性只提供
间歇性的保障。

**所以这一项的准确说法是：截图套件在第二次运行时全绿，且这条测试已知会间歇失败。**
不是"CI 稳定全绿"。第三次再遇到同样症状就不再重跑，直接去修 `row()`。

## 需要 Owner 的事项（不变）

仓库公开/私有、是否合并 main、是否重写历史、LICENSE、Apple 开发者账号、支持邮箱、
两个公开 URL、定价、条款里的法律主体与管辖法律。

## 我接受的总体判定

> 主要 App 构建及测试通过，若干安全与上线能力已实现；工具一致性 CI 仍失败，数据库真实
> 迁移路径尚未证明，真机核心门槛仍为零数据。因此项目仍是内部 Alpha，不具备发布资格。

前两项本次已处理，第三项没有。**仍是内部 Alpha，不具备发布资格。**
