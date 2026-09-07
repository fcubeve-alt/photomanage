import SwiftUI
import PVMCore

/// §12: 真正需要用户决定的内容进入**极小** Review Queue.
///
/// The word that matters is 极小. A long queue is not a feature — it means the engine
/// handed the work back, which is exactly what §7 says not to do. The screen says so
/// rather than presenting a large queue as normal.
struct ReviewQueueView: View {
    @ObservedObject var coordinator: IngestionCoordinator

    private var items: [Catalog.ReviewItem] {
        coordinator.catalog?.reviewQueue() ?? []
    }

    private var burdenPerThousand: Double {
        guard coordinator.libraryCount > 0 else { return 0 }
        return Double(coordinator.reviewCount) / Double(coordinator.libraryCount) * 1000
    }

    /// §14's five verbs, offered where the decision is actually made.
    ///
    /// Recorded at the moment the user answers rather than inferred later from the
    /// catalogue's state: "this asset is gone" and "the user chose to remove it" are
    /// different facts, and only the second one is feedback.
    ///
    /// Delete is `suggest_delete`-shaped — it is an answer to a question, not an
    /// erasure. Nothing on this screen removes anything; §7 and §6 keep the acting to
    /// the proposal flow, where it stays reversible and confirmed.
    @ViewBuilder
    private func answers(for item: Catalog.ReviewItem) -> some View {
        HStack(spacing: 12) {
            ForEach(Self.offered, id: \.0) { verb, label, icon in
                Button {
                    coordinator.record(verb, assetID: item.assetID, path: item.path)
                } label: {
                    Label(label, systemImage: icon).font(.caption)
                }
                .buttonStyle(.bordered)
                .accessibilityIdentifier("answer-\(verb.rawValue)-\(item.assetID)")
            }
        }
    }

    private static let offered: [(UserDecision.Verb, String, String)] = [
        (.keep, "Keep", "tray.and.arrow.down"),
        (.protectAsset, "Protect", "lock"),
        (.delete, "Remove", "trash"),
    ]

    /// What the system has concluded, shown to the person it is about.
    ///
    /// §14's goal is 系统越来越懂这个用户, and a policy the user cannot see is one they
    /// cannot disagree with. Each row states the evidence under it in the user's own
    /// history, not a confidence score.
    private var learnedSection: some View {
        Section {
            ForEach(coordinator.personalPolicy.preferences.values.sorted {
                $0.observations > $1.observations
            }, id: \.path) { preference in
                VStack(alignment: .leading, spacing: 2) {
                    Text(preference.action.label).font(.callout)
                    Text(preference.why).font(.caption).foregroundStyle(.secondary)
                }
            }
        } header: {
            Text("What I have learned from you")
        } footer: {
            Text("These change what happens by default for those categories — never for "
                 + "anything important or irreplaceable, whatever the pattern.")
        }
    }

    var body: some View {
        List {
            Section {
                HStack {
                    Text("Human Review Burden")
                    Spacer()
                    Text("\(Int(burdenPerThousand.rounded())) per 1,000")
                        .monospacedDigit()
                        .foregroundStyle(burdenPerThousand > 100 ? .orange : .secondary)
                }
                .font(.callout)
            } footer: {
                Text("A Constitution §18 KPI. If this climbs, the engine is giving you back "
                     + "work it was supposed to take away.")
            }

            if items.isEmpty {
                Section { Text("Nothing waiting. The library is looking after itself.") }
            }

            ForEach(items, id: \.assetID) { item in
                VStack(alignment: .leading, spacing: 8) {
                    NavigationLink {
                        AssetDetailView(assetID: item.assetID, coordinator: coordinator)
                    } label: {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(item.note).font(.callout)
                            Text(item.why).font(.caption).foregroundStyle(.secondary)
                        }
                    }
                    answers(for: item)
                }
                .accessibilityIdentifier("review-\(item.assetID)")
            }

            if !coordinator.personalPolicy.preferences.isEmpty {
                learnedSection
            }
        }
        .navigationTitle("Review queue")
        .navigationBarTitleDisplayMode(.inline)
    }
}
