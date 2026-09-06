import SwiftUI
import PVMCore

/// Drill-down. §23: 点击后进入第二级更细分类; §3: 同一 Asset 可以从多个入口到达，禁止为了
/// UI 分类而复制原始照片 — so this shows the *same* asset row under every entry that
/// reaches it, and never a copy.
struct CategoryView: View {
    let path: String
    @ObservedObject var coordinator: IngestionCoordinator

    private var children: [(path: String, count: Int)] {
        TaxonomyRuntime.children(of: path).compactMap { child in
            let n = coordinator.rolledCounts[child] ?? 0
            return n > 0 ? (path: child, count: n) : nil
        }
    }

    private var assets: [Catalog.AssetRow] {
        coordinator.catalog?.assets(under: path) ?? []
    }

    var body: some View {
        List {
            if !children.isEmpty {
                Section("Inside") {
                    ForEach(children, id: \.path) { child in
                        NavigationLink {
                            CategoryView(path: child.path, coordinator: coordinator)
                        } label: {
                            HStack {
                                Text(child.path.components(separatedBy: Taxonomy.separator).last ?? child.path)
                                Spacer()
                                Text("\(child.count)").foregroundStyle(.secondary).monospacedDigit()
                            }
                        }
                    }
                }
            }
            Section(children.isEmpty ? "Photos" : "Everything here") {
                if assets.isEmpty {
                    Text("Nothing filed here yet.").foregroundStyle(.secondary)
                }
                ForEach(assets, id: \.assetID) { row in
                    NavigationLink {
                        AssetDetailView(assetID: row.assetID, coordinator: coordinator)
                    } label: {
                        AssetRowLabel(row: row)
                    }
                }
            }
        }
        .navigationTitle(path.components(separatedBy: Taxonomy.separator).last ?? path)
        .navigationBarTitleDisplayMode(.inline)
    }
}

struct AssetRowLabel: View {
    let row: Catalog.AssetRow

    var body: some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(row.assetID)
                .font(.callout)
                .lineLimit(1)
                .truncationMode(.middle)
            HStack(spacing: 6) {
                Text(row.risk.displayName)
                    .font(.caption2)
                    .padding(.horizontal, 6).padding(.vertical, 2)
                    .background(Color.secondary.opacity(0.15))
                    .clipShape(Capsule())
                if row.needsReview {
                    Text("needs your eye").font(.caption2).foregroundStyle(.orange)
                } else {
                    Text("\(Int(row.confidence * 100))% sure")
                        .font(.caption2).foregroundStyle(.secondary)
                }
            }
        }
    }
}
