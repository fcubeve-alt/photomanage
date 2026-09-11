# 支持渠道

**状态：** 方案已定，**需要 Owner 做一件事**：确定并填写一个支持邮箱。

---

## 1. Apple 的硬性要求

App Store Connect 的 App 信息页有两个必填 URL：

| 字段 | 必填 | 现状 |
|---|---|---|
| Support URL | **是** | ❌ 待 Owner 提供 |
| Privacy Policy URL | **是** | ❌ 待 Owner 提供（内容已写好，见 `PRIVACY_POLICY.md`） |
| Marketing URL | 否 | 不需要 |

**这两个必须是可公开访问的网页 URL，不能是 App 内页面，也不能是 `mailto:`。** 这是唯一一处"没有网站就过不了"的地方。

## 2. 最省事的满足方式（推荐）

**用 GitHub Pages，零成本、零维护。**

1. 在 `fcubeve-alt` 下建一个公开仓库（例如 `visual-library-support`）——注意这必须是**另一个**仓库，当前仓库含产品文档与决策记录，不适合公开。
2. 放三个文件：`index.html`（支持页）、`privacy.html`、`terms.html`。内容就是本目录下三份 Markdown 转成的 HTML。
3. 在仓库设置里开启 Pages。得到：
   - Support URL：`https://fcubeve-alt.github.io/visual-library-support/`
   - Privacy Policy URL：`https://fcubeve-alt.github.io/visual-library-support/privacy.html`

`20_TIER0/landing/build_landing.py` 已经有一套"Markdown → 静态 HTML"的代码可以复用，不必从头写。

**备选：** 用 Notion / 语雀 的公开页面，或任何你已有的域名。Apple 只检查 URL 可访问且内容相关。

## 3. 支持邮箱

需要一个。**建议不要直接用 `fcubeve@gmail.com`**——它会出现在 App Store 页面和条款里，会收到垃圾邮件，而且把个人主邮箱和产品绑定之后很难换。

建议：Gmail 的 `+` 别名（`fcubeve+visuallibrary@gmail.com`，零成本、立即可用）或一个新建的产品专用邮箱。

> **这一项我没有替你决定，因为它是你的邮箱。** 填好后替换以下三处：
> `50_LAUNCH/PRIVACY_POLICY.md` 第 12 节、`50_LAUNCH/TERMS_OF_SERVICE.md` 第 10 节、
> 支持页 HTML。改完跑 `python3 40_APP/generate_legal.py` 让 App 内文案同步。

## 4. App 内的支持入口（已实现）

`40_APP/PVM/UI/SupportView.swift`，从首页右上角进入。包含：

- **隐私**与**条款**全文（离线可读——App 不联网，不可能去网上取）。
- **诊断报告**：一屏可读的纯数字报告，用户看到全文后自行决定是否发送。内容清单见 `PRIVACY_POLICY.md` 第 5 节。
- **崩溃记录**：如果上次运行崩溃过，这里显示记录全文，用户可选择发送或删除。
- **恢复购买 / 管理订阅 / 申请退款**：三个入口在有商品可售之前隐藏（`Commerce.isCommerceConfigured == false`），不会出现点了没反应的按钮。

## 5. 支持流程（一个人能维持的版本）

不要承诺做不到的响应时间。建议在支持页上写：

> 这是一个由个人开发的 App。我会读每一封邮件，通常在几天内回复。
> 报告问题时，请附上 App 内《支持 → 诊断报告》生成的那段文字——它只包含版本号和计数，不含你的任何照片信息。

**归类与处理：**

| 类型 | 判断依据 | 动作 |
|---|---|---|
| 崩溃 | 邮件带崩溃记录 | 按符号定位；同一符号出现 ≥2 次即进入修复队列 |
| 分类错误 | 用户说"它把 X 当成了 Y" | 记入 §19 混淆矩阵的真实样本，这是目前**唯一**的真实数据来源 |
| 目录损坏 | 诊断报告 integrity ≠ ok | 指导用户在 App 内重建目录（目录是派生数据，重建无损失，见 `DATA_MIGRATION.md`） |
| 退款 | 任何退款请求 | 一律指向 App 内的退款入口，不劝阻、不设障碍 |

## 6. 还没有的东西

- 没有工单系统。邮箱在单人规模下够用，超出后再说。
- 没有 App 内聊天。那需要服务器，会和"不联网"直接冲突。
- 没有 FAQ 页。等有真实问题之后再写，现在写只能靠猜。
