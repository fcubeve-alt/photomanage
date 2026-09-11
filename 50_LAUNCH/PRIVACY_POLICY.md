# 隐私政策 · Privacy Policy

**产品：** Visual Library（bundle id `com.pvm.app`）
**生效日期：** 待定（随首个 App Store 版本发布之日生效）
**版本：** 草案 v1 · 2026-09-11

> 本文件同时是 App 内《隐私》页面的正文来源。`40_APP/generate_legal.py` 由本文件生成
> `LegalText.generated.swift`，`verify.sh` 会检查两者一致——App 里显示的字和这里写的字
> 不可能不同步。

---

## 一句话

**这个 App 不收集你的任何数据，因为它不联网。**

---

## 1. 我们收集什么

**没有。** 不收集、不上传、不共享、不出售任何信息——包括照片、照片的缩略图、照片中被识别出的文字、位置、设备标识、使用统计、崩溃数据。

这不是承诺书上的一句话，而是代码的结构性事实：

- App 中**不存在任何网络代码**。没有 `URLSession`，没有 `Network.framework`，没有任何第三方 SDK（无 Firebase / Crashlytics / Sentry / Adjust / Facebook / 任何广告或归因库）。
- `40_APP/check_no_network.py` 在每次验证时扫描全部源码，一旦出现联网调用或分析 SDK，构建即失败。
- App 的全部依赖是：Apple 的 Photos、Vision、BackgroundTasks、StoreKit 与 SQLite。没有一个第三方包。

## 2. App 用你的照片做什么

- 请求**照片读取权限**，读取你手机上已有的照片与视频。
- 在**设备本地**用 Apple 的 Vision 框架分析它们：场景、文字（OCR）、重复画面、质量。
- 把分析结论写入一个**只存在于你手机上**的本地数据库（目录），供你搜索和浏览。
- 原始照片**从不被复制、上传或导出**。目录中保存的是结论（类别、时间、置信度、理由），以及为了搜索而保留的文字片段。

**这个版本从不删除或修改你的任何一张照片。** 这不是设置项，是编译期约束（`LibrarySafety.mode == .readOnly`，`40_APP/check_no_photo_writes.py` 保证 App 中不存在任何 PhotoKit 写入调用）。

## 3. 目录数据库里有什么，存在哪里

目录中可能包含**从你照片里 OCR 出来的文字**——这可能包括证件号、银行信息、合同内容。因此：

- 它存放在 App 的私有容器内，其他 App 无法读取。
- 启用 iOS 数据保护等级 `completeUntilFirstUserAuthentication`：设备重启后未解锁前无法读取。
- **排除在 iCloud 与 iTunes 备份之外**（`isExcludedFromBackup`）——它可以从你的照片重新生成，不值得让它离开这台设备。
- 删除 App 即删除目录，不留残余。

## 4. 崩溃报告

- 崩溃信息写在**你设备上的一个本地文件**里。
- 我们**不会**自动收到它。
- 下次启动时 App 会告诉你有一份崩溃记录，你可以看到它的**全部内容**，然后决定是否用你自己的邮件 App 发给我们。
- 发送前会对可能的标识符、路径与长数字串做遮蔽处理。

## 5. 支持与诊断报告

如果你联系支持，App 可以生成一份诊断报告。它**只**包含：App 版本、系统版本、机型代号、数据库结构版本与完整性、各项计数（已编目数量、待复核数量、实体数量、你做过的决定数量）、各大类的数量。

它**不**包含任何照片、任何照片标识符、任何文件路径、任何 OCR 文字。发送前完整内容显示在屏幕上，你看到什么就发送什么。

## 6. 账号

**没有账号。** 不需要注册，不需要邮箱，不需要 Sign in with Apple。

## 7. 购买

如果将来加入付费功能，交易由 Apple 处理。我们收不到你的姓名、邮箱或支付信息——只能通过 Apple 在设备上验证的凭据知道"这台设备上的这个 Apple ID 拥有某项权益"。我们不运行任何服务器，也不保存收据。

## 8. 儿童

本 App 不面向 13 岁以下儿童，也不收集任何人的数据，因此不存在儿童数据的收集问题。

## 9. 第三方

**没有第三方。** 没有分析、没有广告、没有归因、没有崩溃上报服务、没有 A/B 测试平台。

## 10. 你的权利

因为我们没有你的任何数据，所以没有可供查询、更正或删除的记录。删除 App 即删除本地的一切。

## 11. 变更

本政策如有变更，会随新版本更新，并在 App 的《隐私》页面中显示新的版本日期。如果未来任何版本开始联网，我们会在更新说明中显式说明，而不是只改这份文件。

## 12. 联系方式

**支持邮箱：** 待 Owner 填写（见 `50_LAUNCH/SUPPORT.md`）

---

# Privacy Policy (English)

**Product:** Visual Library (`com.pvm.app`) · **Effective:** on first App Store release · **Draft v1, 2026-09-11**

**This app collects nothing, because it has no network code.**

- **No data collection of any kind.** No photos, no thumbnails, no recognised text, no location, no device identifiers, no usage analytics, no crash telemetry.
- **Structural, not promised.** The app contains no `URLSession`, no `Network.framework` and no third-party SDK. `check_no_network.py` fails the build if one appears. Its only dependencies are Apple's Photos, Vision, BackgroundTasks and StoreKit, plus SQLite.
- **Photos are read, never changed.** Analysis runs on-device with Apple's Vision framework. This version cannot delete or modify a photo: the app links no PhotoKit mutation API at all, and `check_no_photo_writes.py` enforces it.
- **The catalogue stays on the device.** It may contain text read out of your photographs by OCR, so it is stored in the app's private container under iOS Data Protection (`completeUntilFirstUserAuthentication`) and excluded from iCloud and iTunes backups. Deleting the app deletes it.
- **Crash reports are local.** Written to a file on your device, shown to you in full, and sent only if you choose to mail them yourself.
- **No account.** No sign-up, no email address, no Sign in with Apple.
- **Purchases** are handled entirely by Apple. We run no server and receive no personal or payment information.
- **No third parties.** No analytics, ads, attribution, crash service or experimentation platform.
- **Your rights.** We hold no data about you, so there is nothing to access, correct or delete. Removing the app removes everything.

**Contact:** to be filled in by the owner (see `50_LAUNCH/SUPPORT.md`).
