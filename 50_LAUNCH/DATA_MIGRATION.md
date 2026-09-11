# 数据迁移方案

**状态：** ✅ 已实现并有测试（`40_APP/PVMCore/Sources/PVMCore/Migration.swift`，
`40_APP/PVMCore/Tests/PVMCoreTests/MigrationTests.swift`）。

---

## 1. 这个产品的迁移问题和别的产品不一样

绝大多数 App 必须小心迁移数据库，因为数据库是用户数据的**唯一副本**。这里正相反：

- **目录里几乎每一行都是派生数据。** `assets`、`assignments`、`evidence`、`relations`、
  `proposals`、`entities`、`observations`、`video_records` 全部由同一个确定性引擎从照片库
  重新算出来。丢掉它们的代价是一次索引，没有别的。
- **有两张表不是。** `decisions` 是用户的 Keep/Delete/Protect/Restore 记录——§14 说
  Personal Policy 是**从它推导出来的**，所以这个日志才是耐久的东西，丢了就等于悄悄改写了
  系统对这个用户的认识。`entity_review` 是系统已经决定要问的问题（§24 Gate 2），丢了会
  把用户可能已经回答过的问题重新问一遍。
- **用户设置不是。** `meta` 表里 `pref.` 前缀的键是用户设的，不是引擎算的。

**因此迁移策略是：重建派生的那一半，保留用户说过的那一半，永不复制文件。**
在一个装着 10 万张照片目录的手机上复制一份数据库，是用用户可能没有的存储空间，
去保护一份可以免费重算的数据。

## 2. 真正会出事的地方

schema 代码只有 `CREATE TABLE IF NOT EXISTS`。它会加新表，**但永远不会给已有的表加一列。**
所以一个旧文件会干干净净地打开，然后在第一条引用新列的查询上失败——**更新之后、启动时崩溃、
没有退路。**

## 3. 两个被第二次审计打回的缺陷（2026-09-12）

第一版迁移是**错的**，审计说得准确。

### 缺陷一：没有版本记录的旧库被当成新库

`Catalog.init` 先跑 `createSchema()`（全是 `CREATE TABLE IF NOT EXISTS`），再读
`schema_version`。问题在于 `createSchema()` 会把 `meta` 表**造出来**——于是"这个文件没有
记录过版本"和"这是本次刚建的新文件"读出来一模一样，都是 0。

这不是假想情况：**Swift 端直到 2026-09-11 才开始写 `schema_version`。** 在那之前每一个由
Swift 构建写出的目录都是无版本的，且列是旧的。按旧逻辑它们全部被判为"新文件"、盖上当前
版本号、永不迁移，然后在第一条引用新列的查询上炸掉。

**修法：在 `createSchema()` 之前询问文件。** `sqlite_master` 是唯一不需要被创建就存在的表：

```
tablesBefore = SELECT COUNT(*) FROM sqlite_master WHERE type='table'
recorded     = meta 里的 schema_version（meta 不存在时读到 nil）
```

`tablesBefore > 0 && recorded == 0` 就是无版本旧库，`Plan.unversionedLegacy`。

### 缺陷二：只删行不改结构，等于什么都没做

第一版迁移做的是 `DELETE FROM <派生表>` 加上挪版本戳。**但 `DELETE` 不会给表加一列。**
迁移要挡的失败恰恰是结构变化——新增列、新增索引、改约束——清空行把这些原样留着。旧文件会
"迁移成功"、变空、并且依然是错的形状。

**修法：把派生表 DROP 掉，让 `createSchema()` 按本次构建的形状重建。** 这在多数 App 里
不可行，在这里可行，理由和本文第 1 节一样：派生表里没有任何不能重算的东西。

用户写的两张表不能 DROP，改为逐列搬运：`ALTER TABLE x RENAME TO x_migrating` →
`createSchema()` 建新表 → `INSERT INTO x(...) SELECT ... FROM x_migrating` → 丢掉旧表。
旧表没有的列用字面量兜底（这些列都是 `NOT NULL` 无默认值，直接 SELECT 会让整个迁移失败）。

**一个副作用值得记下**：重命名表会把它的索引一起带走，所以第一次 `createSchema()` 时
`idx_decisions_path` 这个名字还被旧表占着，`CREATE INDEX IF NOT EXISTS` 直接跳过，
新表就没有索引。旧表被丢弃后索引也随之消失。所以搬运完成后**再调用一次 `createSchema()`**，
由它补上。`testTheRebuiltTablesKeepTheirIndexes` 钉住这一条。

## 4. 五种情形

| 打开时的状态 | Plan | 行为 |
|---|---|---|
| 文件里一张表都没有 | `.fresh` | 写入当前版本，结束 |
| 版本 == 本次构建 | `.current` | 什么都不做 |
| **有表但没有版本记录** | `.unversionedLegacy` | **按比一切都旧处理**：DROP 派生表并按当前形状重建 + 搬运用户表 + 清 cursor → 写版本戳 → VACUUM |
| 版本 < 本次构建 | `.rebuildDerived(from:)` | 同上 |
| 版本 > 本次构建 | `.newerThanThisBuild` | **不碰它，也不改它的版本戳。** 本次构建不知道更新的结构是什么意思，猜是不可接受的 |

**cursor 必须一起清掉。** 它是索引的续跑点；清空了行却留着 cursor，下一次索引会从图库中段
继续，然后报告"已完成"——而它前半段一行都没有。

## 5. 迁移做完之后，检查文件而不是检查版本号

`missingColumns()` 用 `PRAGMA table_info` 把本次构建会写的列和文件里实际有的列对一遍，
返回差集。`Outcome.succeeded` 要求它为空。

这是第一版最缺的东西：**一个声称成功的迁移，唯一的证据是它自己盖的版本戳。** 现在版本戳
和文件形状不一致时，说话的是文件。这一行也出现在 App 内《支持 → 诊断报告》里
（`SCHEMA GAPS:`）。

## 6. 测试用的是真实的旧结构，不是改了版本号的新结构

第一版测试的做法是：用当前代码建当前结构 → 把版本号手动改旧 → 跑迁移。审计指出这只能证明
版本算术会运行——被迁移的表本来就有新构建要的每一列，"迁移成功"和"迁移什么都没做"结果
完全相同。这个批评是对的。

现在的 fixture 是把当前结构**拆掉**：`DROP TABLE assets` 后用旧 DDL 重建（没有
`media_type`、`importance`、`asset_class`、`importance_why`），最坏情况下再
`DROP TABLE meta` 让它完全没有版本记录。

而最关键的断言不是版本号，是：

```swift
INSERT INTO assets(asset_id, signals_fp, engine_fp, asset_class, media_type, importance)
```

**迁移前这条必须失败，迁移后必须成功。** 那条 INSERT 失败就是真实的崩溃现场。

## 7. 降级（`.newerThanThisBuild`）

发生在 TestFlight 回退、或从更新的备份恢复。`Catalog.quarantine(path:)` 把文件连同它的
`-wal`、`-shm` 一起改名挪走，然后在原路径开一个新的。

- **改名而不是删除**：那个文件属于用户可能会回去的更新版本，为了让旧版能启动而删掉新版的
  状态，是没人要求过的决定。
- **`-wal` / `-shm` 必须一起挪**：把一个更新版本的预写日志留在原地，会让它挂到新建的数据库上。

## 8. 用户看得到什么

App 内《支持 → 诊断报告》会显示：

```
catalogue schema: opened 5 → rebuilt from schema 5
integrity: ok
```

不是"正在优化…"这种无内容的措辞。目录被重建过是一个事实，用户有权知道。

## 9. 另一个方向的迁移：从 Python 引擎到 App

`30_ENGINE/pvm/catalog.py` 和 Swift 端写的是同一个 schema（`40_APP/check_schema.py`
逐列比对，`verify.sh` 每次跑）。所以参考实现产出的目录，App 可以直接打开——这在调试时有用，
在产品上没有路径，也不需要有。

## 10. 没有做、也不打算做的

- **不做 iCloud 同步。** 目录含 OCR 出来的证件与银行文字，同步意味着它离开这台设备。
  换设备的正确做法是重新索引：照片本来就在 iCloud 照片里，目录可以免费重算。
- **不做导出/导入目录文件。** 同上，一个可以被导出的目录文件就是一个可以被误发出去的文件。
  需要带走的只有"数字导出"（计数与耗时），那是另一件事。
