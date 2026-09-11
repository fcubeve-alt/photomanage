import SwiftUI
import PVMCore

/// SUPPORT, PRIVACY, TERMS AND DIAGNOSTICS — all of it offline.
///
/// Every one of these screens is normally a web view pointing at a URL. This app has no
/// network code, so a web view is not available to it, and that turns out to be the
/// better arrangement: the privacy policy is readable on a plane, and it is readable
/// precisely when someone is checking whether the privacy claim is true.
///
/// The published documents at the two URLs App Store Connect requires are the *source*
/// of this text — `generate_legal.py` turns `50_LAUNCH/*.md` into `LegalText`, and
/// `verify.sh` fails if the two drift.
struct SupportView: View {
    @ObservedObject var coordinator: IngestionCoordinator
    @StateObject private var entitlements = Entitlements.shared
    @State private var crashReport: String? = CrashReporter.reportFromLastRun

    /// Built once when the screen appears, not in `body`.
    ///
    /// `body` runs on every redraw, and this report ends with `PRAGMA integrity_check`
    /// over the whole catalogue — seconds of main-thread work on a 100k-asset library,
    /// repeated on every scroll. Exactly the shape of the bug the third-party audit
    /// found in the depth pass, in a place nobody would think to look at.
    @State private var diagnostics = ""

    private func buildDiagnostics() -> String {
        var text = Diagnostics.report(catalog: coordinator.catalog,
                                      phase: String(describing: coordinator.phase))
        if let migration = lastMigration, migration.derivedRowsCleared > 0 {
            text += "\nmigration: cleared \(migration.derivedRowsCleared) derived rows, "
                + "kept \(migration.decisionsKept) decisions"
        }
        if lastQuarantine != nil {
            text += "\nmigration: a newer catalogue was set aside and a fresh one started"
        }
        return text
    }

    var body: some View {
        List {
            Section("关于") {
                Text(Diagnostics.buildSummary)
                    .font(.footnote.monospaced())
                    .foregroundStyle(.secondary)
                Label(LibrarySafety.userFacingNote, systemImage: "lock.shield")
                    .font(.footnote)
            }

            Section("条款与隐私") {
                NavigationLink("隐私政策") {
                    LegalDocumentView(title: "隐私政策", text: LegalText.privacyPolicy)
                }
                NavigationLink("服务条款") {
                    LegalDocumentView(title: "服务条款", text: LegalText.termsOfService)
                }
            }

            if let report = crashReport {
                Section("上次运行崩溃了") {
                    Text("下面是完整的崩溃记录。它已经过遮蔽处理，不含照片、标识符或 OCR 文字。"
                         + "你可以把它发给支持邮箱，也可以直接删掉。")
                        .font(.footnote)
                    Text(report)
                        .font(.caption2.monospaced())
                        .lineLimit(20)
                    ShareLink(item: report) { Label("发送这份崩溃记录", systemImage: "paperplane") }
                    Button("删除", role: .destructive) {
                        CrashReporter.clearPendingReport()
                        crashReport = nil
                    }
                }
            }

            Section("诊断报告") {
                Text(Diagnostics.contentsExplanation).font(.footnote)
                Text(diagnostics).font(.caption.monospaced())
                ShareLink(item: diagnostics) { Label("发送诊断报告", systemImage: "paperplane") }
            }

            // Hidden entirely while there is nothing to sell. A "Restore Purchases"
            // button in an app with no products is a button that can only disappoint.
            if Commerce.isCommerceConfigured {
                Section("购买") {
                    Button("恢复购买") { Task { await entitlements.restore() } }
                    Button("管理订阅") { Task { await entitlements.showManageSubscriptions() } }
                    Button("申请退款") { Task { await entitlements.requestRefund() } }
                    if let error = entitlements.lastError {
                        Text(error).font(.footnote).foregroundStyle(.secondary)
                    }
                }
            }
        }
        .navigationTitle("支持")
        .navigationBarTitleDisplayMode(.inline)
        .task { if diagnostics.isEmpty { diagnostics = buildDiagnostics() } }
    }
}

/// A document, rendered as plain text rather than as Markdown.
///
/// `Text(LocalizedStringKey(...))` would render the headings and bold, and would also
/// silently reinterpret anything in the document that happens to look like markup. A
/// legal text that the renderer is allowed to reformat is not the text that was
/// published, so this shows exactly the characters that `generate_legal.py` produced.
struct LegalDocumentView: View {
    let title: String
    /// Named `text`, not `body`: `body` is `View`'s own requirement.
    let text: String

    var body: some View {
        ScrollView {
            Text(text)
                .font(.footnote)
                .textSelection(.enabled)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding()
        }
        .navigationTitle(title)
        .navigationBarTitleDisplayMode(.inline)
    }
}
