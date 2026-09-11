# App Store 提交清单

**状态：** 除需要开发者账号的部分外，全部已准备好。下表中 ✅ 的字段可以直接复制粘贴。

> **前提：** 没有 Apple Developer Program 账号（$99/年）就没有 App Store Connect，
> 没有 App Store Connect 就没有 App 记录、没有 Bundle ID 注册、没有商品、没有
> TestFlight。本文件把**不需要账号就能定下来的部分**全部定好，账号到位后只剩填写。

---

## 1. App 信息

| 字段 | 值 | 状态 |
|---|---|---|
| Bundle ID | `com.pvm.app` | ✅（需在账号下注册，名称可改） |
| App 名称（30 字符内） | `Visual Library` | ✅ 需在 App Store Connect 查重 |
| 副标题（30 字符内） | `Find any photo you own` | ✅ |
| 主类别 | Photo & Video | ✅ |
| 次类别 | Utilities | ✅ |
| 年龄分级 | 4+ | ✅（无用户生成内容、无网络、无广告） |
| 版权 | 待 Owner 填写（个人名或公司名） | ❌ |
| Support URL | 见 `SUPPORT.md` | ❌ Owner |
| Privacy Policy URL | 见 `SUPPORT.md` | ❌ Owner |

## 2. 描述文案（English，App Store 正文）

```
Your photo library is not disorganised. It is unindexed.

Visual Library reads the photos already on your iPhone and builds a catalogue of
them — by what they are, not just when they were taken. Documents, screenshots,
receipts, tickets, travel, people, things you own. You open it and see shelves,
not another infinite scroll.

Everything happens on your iPhone. There is no account, no sign-up, and no
network code in this app at all — not for analytics, not for crash reports, not
for anything. Your photos are never uploaded, because there is nowhere to upload
them to.

This version never deletes or changes a photo. It cannot: the app links no photo
library write API whatsoever, and an automated check fails the build if one is
ever added.

• Shelves, not a stream — categories and counts on the first screen
• Search by what a photo contains, including text read from it
• Find every copy of the same thing, and which one to keep
• Works fully offline, on aeroplane mode, forever
• No account, no ads, no tracking, no subscription required
```

**中文描述（简体，用于中国区）：** 同义改写，Owner 在提交时可直接沿用上文语气；本文件不预写中文商店文案，因为中国区上架还需要额外资质（见第 8 节），在决定是否上架中国区之前写它没有意义。

**关键词（100 字符内，逗号分隔，无空格）：**
```
photo,search,organize,duplicate,screenshot,receipt,document,offline,privacy,library,index,cleaner
```

**促销文本（170 字符内，可随时改，不需重新审核）：**
```
Everything on-device. No account, no network, no tracking. This version never deletes a photo.
```

## 3. 隐私"营养标签"（App Privacy 问卷）

在 App Store Connect 的 App Privacy 一节，逐项回答：

| 问题 | 答案 |
|---|---|
| Do you or your third-party partners collect data from this app? | **No** |

选 No 之后不再有后续问题。标签显示为 **Data Not Collected**。

**这个答案必须是真的，而它是真的**——依据：App 中不存在任何网络代码，`40_APP/check_no_network.py` 在每次验证时强制这一点。**如果将来加入了任何联网功能，这一页必须先改。** 竞品分析（`20_TIER0/evidence/COMPETITOR_PRICING_MATRIX.md`）记录了这一栏被填成"not linked to me"而实际负载携带用户 ID 的案例——那是本项目最不该重复的事。

## 4. 导出合规

| 问题 | 答案 |
|---|---|
| Does your app use encryption? | **No** |

Info.plist 中可加 `ITSAppUsesNonExemptEncryption = false`，避免每次上传都被问一次。
App 只使用 iOS 的数据保护（Apple 提供的平台能力，属豁免），不自行实现加密。

> **动作项：** 账号到位后在 `40_APP/project.yml` 的 `info.properties` 中加入
> `ITSAppUsesNonExemptEncryption: false`。现在不加是因为它和审核流程绑定，
> 提前加会在没有账号的本地构建里变成一句没人验证过的声明。

## 5. 审核备注（App Review Information → Notes）

```
This app works entirely offline and requires no account, so no demo credentials
are needed.

To review it, please add a few photos to the simulator or device library first —
with an empty photo library the app correctly shows an empty catalogue.

Photo library permission: the app requests read/write access because iOS provides
no read-only photo permission (PHAccessLevel offers only .addOnly, which is
write-only, and .readWrite). The app performs no writes: it links no
PHAssetChangeRequest, PHAssetCreationRequest or deleteAssets call anywhere in its
binary.

Background processing (BGTaskSchedulerPermittedIdentifiers: com.pvm.app.catalogue)
is used to finish indexing a large library while the device charges. It performs
no network activity.
```

> 第三段很重要。请求 `.readWrite` 却从不写入，是审核最可能提问的一点，**主动说明比被问后再解释好。**

## 6. 截图

需要 6.7" 与 6.5"（或当年 Apple 要求的尺寸集）各 3–10 张。

**已有素材：** CI 的 `PVMUITests` 每次运行都会产出真实截图（最近一次全绿运行见
`PROJECT_STATE.md`）。这些是模拟器截图，内容是确定性 fixture，**不是真实照片**——
可以直接用作商店截图（Apple 允许），但更好的做法是装到真机之后用你自己的照片库截图，
因为 fixture 的类目分布不像真实生活。

## 7. 商品（IAP）

**账号到位前无法创建。** 标识符已经定好并写进代码（`40_APP/PVM/Store/Commerce.swift`）：

| 标识符 | 类型 | 建议价 | 备注 |
|---|---|---|---|
| `com.pvm.app.lifetime` | Non-Consumable | 见 `PRICING_PROPOSAL.md` | 家庭共享：开 |
| `com.pvm.app.pro.yearly` | Auto-Renewable（组 `PVM Pro`） | 见 `PRICING_PROPOSAL.md` | 家庭共享：开 |

**当前这两个商品在 App 里是不可见的。** `Commerce.paywall` 为空集，意味着所有功能免费、
所有购买入口隐藏。这是刻意的：价格未定之前（`PRICING_PROPOSAL.md` 待裁决），
显示一个买不了的按钮比没有按钮更糟。

购买、恢复、取消、退款的全部代码路径可以用 `40_APP/PVM.storekit` 在**模拟器里、
没有开发者账号的情况下**测试（Xcode → Edit Scheme → Run → Options → StoreKit Configuration）。

> ⚠️ `PVM.storekit` 的 JSON 格式**尚未在 Xcode 里打开验证过**（本仓库无 Mac）。
> 首次使用时若 Xcode 报格式错误，用 Xcode 的 File → New → StoreKit Configuration File
> 重建一份，把上表的标识符填进去即可。

## 8. 中国区（如果要上）

额外要求，与技术无关但不可跳过：

- **ICP 备案**：在中国大陆区上架的 App 需提供 ICP 备案号。个人可申请，但需要一个已备案的域名，周期通常数周。
- **软件著作权登记**：部分类目需要。
- 若最终决定不上中国区，在 App Store Connect 的 Pricing and Availability 中取消勾选中国大陆即可，其余区域不受影响。

> **建议：** 首发不上中国区。备案周期会把上线时间从"几天"拖成"几周"，而验证产品
> 是否成立不需要中国区。

## 9. 提交顺序（账号到位后）

1. 注册 Bundle ID `com.pvm.app`（Certificates, Identifiers & Profiles）。
2. App Store Connect 建 App 记录，填第 1 节的字段。
3. 填 App Privacy（第 3 节）与导出合规（第 4 节）。
4. Xcode Archive → 上传构建版本（需要 Mac；`.github/workflows/app-ipa.yml` 产出的是未签名包，不能直接上传）。
5. **先发 TestFlight 内部测试**，装到真机，跑 `20_TIER0/TIER0_GO_NO_GO.md` 的 A1/A2/A3。
6. **A3 通过之后**再提交审核。A3 不过，上架的是一个会在大图库上被系统杀掉的 App。
