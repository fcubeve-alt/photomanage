# 不用开发者账号，把 App 装到自己的 iPhone 上

**结论先行：可以，$0，不需要那 $99，也不需要 Mac。**

Apple 的 **free provisioning（免费预置）**允许任何免费 Apple ID 把自己编译的 App 装到
**自己名下的设备**上。官方路线要 Xcode（要 Mac）；这份文档走的是 Windows 路线——
CI 编译出未签名的 `.ipa`，你在 Windows 上用工具重新签名并安装。

```
GitHub Actions (macOS runner)  →  PVM-unsigned.ipa      ← 本仓库 app-ipa.yml 干的
        ↓ 下载
Windows + Sideloadly           →  用你的免费 Apple ID 签名
        ↓ USB
你的 iPhone                    →  装上，能跑，能读你的真实相册
```

---

## 先决定用哪一台手机

**用你手上最旧的、还能跑 iOS 17 的那台。不要用最新的那台。**

这不是随口说的。整个 Tier 0 生死判定里，A3「能不能活下来」是**唯一一条失败即致命**的
——热节流、内存被 jetsam 杀掉、后台被系统收回。新手机会把这些问题全部掩盖过去，
而旧手机才是真实用户里占多数的那一台。**最新的 iPhone 只能证明它在最好的情况下能跑。**

App 的部署目标是 **iOS 17.0**，所以：

| 你的手机 | 能不能用 |
|---|---|
| iPhone 7 / 8 | ❌ 最高只到 iOS 15/16 |
| iPhone XS / XR | ✅ **最理想的测试机**——iOS 17 支持的最旧一档 |
| iPhone 11 / 12 | ✅ 次选 |
| iPhone 13 及以后 | ⚠️ 能跑，但对 A3 几乎没有信息量 |

> 想在 iPhone 7 上测的话，要把部署目标降到 iOS 15 并改掉几处 API，是一笔真实的工作量。
> 先别做；等 XS/XR 上的数字出来再判断值不值得。

---

## ⚠️ 先读这一段：把 Apple ID 交给第三方工具是有代价的

第三方审计（2026-09-11）把这一条单独列为 P1，理由很直接：**一个主打照片隐私的产品，
让用户把 Apple ID 输进一个来源不明的 Windows 程序，这两件事是矛盾的。**这个批评是对的，
所以把代价写在你做之前，而不是写在出事之后。

Sideloadly / AltStore 会拿到你的 Apple ID 和密码（或 App 专用密码），用它向 Apple 申请
一张免费开发者证书。这是 free provisioning 的正常工作方式——但**这些工具不是 Apple 出的，
也没有经过 Apple 审核**，你是在信任它们的作者。

所以：

1. **一定用一个专门的次要 Apple ID**，不要用你主力那个（有 iCloud 照片、通讯录、支付的那个）。
   免费证书只需要一个能登录的 Apple ID，不需要它有任何数据。
2. **开两步验证，用 App 专用密码**，在 [account.apple.com](https://account.apple.com) 生成。
   这样你给出去的不是主密码，而且可以随时单独撤销。
3. **只从官方站点下载**（sideloadly.io / altstore.io），装完先核对一下文件签名或哈希。
   搜索结果里的镜像站是这类工具最常见的投毒渠道。
4. **用完就撤销**：account.apple.com →「登录与安全」→ App 专用密码 → 撤销那一条。
5. 这条路**只适用于你自己的设备做内部开发验证**。给别人测试请走 TestFlight
   ——那需要 $99，但不需要任何人把 Apple ID 交给第三方。

如果你觉得这个代价不值，那是完全合理的判断，**那就等 $99 走 TestFlight**。
这条路的存在是为了让真机验证不被 $99 卡住，不是为了省那 $99。

---

## Windows 这边需要什么

1. **Sideloadly**（推荐）或 **AltStore**。两者都用 free provisioning 签名，都有 Windows 版。
2. **iTunes 和 iCloud**——要 **Apple 官网**下载的版本，**不是 Microsoft Store 版**。
   Store 版被沙箱隔离，工具读不到它需要的驱动。
3. 一根**能传数据**的 USB 线（很多充电线只有电，没有数据）。
4. 你的 **Apple ID**。建议用次要的那个，不要用主力——理由见下面「代价」。

---

## 步骤

1. 在 GitHub 上手动触发 **`Unsigned .ipa for sideloading`** 这个 workflow
   （Actions → 选它 → Run workflow → 选分支）。
2. 跑完后从这次 run 的 **Artifacts** 下载 `PVM-unsigned-ipa`，解压得到 `PVM-unsigned.ipa`。
3. 手机 USB 连上 Windows，**在手机上点「信任这台电脑」**。
4. 打开 Sideloadly，把 `.ipa` 拖进去，填 Apple ID，点 Start。
   - 开了两步验证会要 **App 专用密码**——在 [account.apple.com](https://account.apple.com)
     的「登录与安全」里生成。
5. 装完 App 还打不开，因为证书没被信任。在手机上：
   **设置 → 通用 → VPN与设备管理 → 找到你的 Apple ID → 「信任」。**
6. 打开 App。它会请求相册权限——**给「所有照片」**，否则它只能看到你选中的那几张，
   测出来的规模数字没有意义。

---

## 代价（free provisioning 的固有限制，不是本项目的问题）

| 限制 | 影响 |
|---|---|
| **证书 7 天过期** | 一周后 App 打不开，要重签重装。Sideloadly/AltStore 有自动刷新 |
| 同一设备最多 3 个自签 App | 基本不影响 |
| 每 7 天最多 10 个 App ID | 反复重装同一个 App 不消耗额度 |
| 不能用 TestFlight | **T0-B 那 15 个外部参与者这条路走不通**——那个仍然需要 $99 |
| 拿不到 Xcode 调试器 | 见下面「测不到什么」 |

---

## 这一趟能测到什么

最重要的部分——**它直接解掉目前最大的两个卡点。**

| 问题 | 现在的状态 | 装上手机后 |
|---|---|---|
| **A1 规模** | 只有模拟器上的区间（预测真机 7k–26k） | ✅ 真实硬件上的真实数字 |
| **A2 热节流** | 无数据，模拟器没有热状态 | ✅ 能测 |
| **A3 存活**（失败即致命） | 无数据，模拟器不会 jetsam | ✅ 能测——包括断点续跑在被系统杀掉后到底管不管用 |
| **T1B-EMBEDDING 阈值** | 卡住，素材库是 PIL 画的方块 | ✅ **你的真实照片就是素材**，这是最大的解锁 |
| **首次全库编目体验**（§12/§19） | 从来没人经历过 | ✅ 你就是第一个用户 |

## 测不到什么

诚实写清楚，免得把这次结果当成比它更强的证据：

- **BGProcessingTask（C-4 后台调度）测不全。** iOS 只在设备充电且闲置时才调度它；
  强制触发需要 Xcode 调试器的 `_simulateLaunchForTaskWithIdentifier`，侧载的 App
  连不上调试器。前台跑完整管线可以测，后台自动跑只能靠等。
- **不是多设备验证。** 一台手机的数字是一台手机的数字，不是设备带宽。
- **不是 T0-B。** 外部参与者研究仍需 TestFlight，仍需 $99。
- **`UIBackgroundModes: processing` 在免费预置下是否完全正常，我没有验证过。**
  我判断可以——它是 Info.plist 声明，不是需要付费团队签发的 entitlement——
  但这是判断不是事实，第一次跑就知道。

---

## ⚠️ 隐私：这一步之后，引擎会看到你的真实照片

不是套话，是这个项目自己的 §16/§17 要求写在这里的：

- **所有处理都在设备本地。**引擎没有任何网络代码，没有一张照片会离开手机。
- **但目录数据库里会存 OCR 出来的文字。**身份证、护照、银行卡、合同只要被拍过，
  号码就在 `pvm_catalogue.sqlite` 里。这是 App 正常工作的方式，不是缺陷。
- **所以：不要把整个目录数据库发出来。**要分析结果就用 App 里导出的**纯数字报告**——
  只有计数、速率、耗时，没有 asset ID、没有 OCR 文本、没有人名地名。
  这条路做成默认且唯一的导出方式，让它安全是因为结构上做不到别的，
  而不是因为每次都记得。
- 想清理：把 App 删掉即可，沙箱里的数据库跟着一起走。

---

## 出问题时

| 症状 | 多半是 |
|---|---|
| Sideloadly 报 `Could not find iTunes` | 装的是 Microsoft Store 版，换 Apple 官网版 |
| 装上了但图标发灰、点不开 | 第 5 步的「信任」没做 |
| `Unable to install... application-identifier entitlement` | Bundle ID 冲突，在 Sideloadly 里换一个 |
| App 一开就闪退 | 大概率 CI 出了 simulator 架构的包——看那次 run 的 `WHAT IS IN THIS .ipa` 段，架构必须是 **arm64** 而不是 x86_64 |
| 一周后打不开 | 正常，证书过期，重签一次 |
