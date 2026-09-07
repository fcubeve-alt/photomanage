import SwiftUI
import PVMCore

/// The safety red line made visible: **every suggestion must be able to explain why.**
///
/// This screen is that promise kept. It shows every entry the asset is filed under and,
/// under each, the actual reasons the engine used — read back from the catalogue, not
/// recomputed, so a newer rule set cannot quietly rewrite what the user was told.
struct AssetDetailView: View {
    let assetID: String
    @ObservedObject var coordinator: IngestionCoordinator

    private var explanation: [(path: String, reasons: [String])] {
        coordinator.catalog?.why(assetID) ?? []
    }

    /// Tier 1-D's other three indexes. The sections above render Content, Time and
    /// Place, which come off `assignments`; Person, Object and Event hang off the
    /// memory graph and were reachable only by starting from an entity.
    private var indexedUnder: [Catalog.IndexedEntity] {
        coordinator.catalog?.entities(for: assetID) ?? []
    }

    private func describe(_ entity: Catalog.IndexedEntity) -> String {
        var line = entity.name
        if let place = entity.place {
            // §11: a hedged place must not render as a stated one.
            line += entity.placeIsInferred ? " — probably \(place)" : " — \(place)"
        }
        if entity.isInferred { line += " (inferred)" }
        return line
    }

    var body: some View {
        List {
            Section {
                Text(assetID).font(.caption).textSelection(.enabled)
            } header: {
                Text("Asset")
            }

            ForEach(explanation, id: \.path) { entry in
                Section(entry.path) {
                    ForEach(entry.reasons, id: \.self) { reason in
                        Label(reason, systemImage: "checkmark.circle")
                            .font(.callout)
                            .labelStyle(.titleAndIcon)
                    }
                }
            }

            if !indexedUnder.isEmpty {
                Section("Also indexed under") {
                    ForEach(indexedUnder, id: \.entityID) { entity in
                        VStack(alignment: .leading, spacing: 2) {
                            Text(describe(entity)).font(.callout)
                            Text("\(entity.kind) · \(entity.reason)")
                                .font(.caption).foregroundStyle(.secondary)
                        }
                        .accessibilityIdentifier("indexed-\(entity.entityID)")
                    }
                }
            }

            if explanation.isEmpty {
                Section {
                    Text("No explanation was recorded for this asset. That is a defect — "
                         + "an assignment without evidence should not have been written.")
                        .foregroundStyle(.red)
                }
            }
        }
        .navigationTitle("Why is this here?")
        .navigationBarTitleDisplayMode(.inline)
    }
}
