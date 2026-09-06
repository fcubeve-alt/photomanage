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
                NavigationLink {
                    AssetDetailView(assetID: item.assetID, coordinator: coordinator)
                } label: {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(item.note).font(.callout)
                        Text(item.why).font(.caption).foregroundStyle(.secondary)
                    }
                }
            }
        }
        .navigationTitle("Review queue")
        .navigationBarTitleDisplayMode(.inline)
    }
}
