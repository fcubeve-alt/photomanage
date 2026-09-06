import SwiftUI
import PVMCore

/// §2 "Remember", on screen.
///
/// The Browse tab answers *which shelf is this photo on*. This answers a different
/// question — *what does my library know exists, and where did it last see it* — and
/// the two are not the same thing. §15 builds Wardrobe, Travel, Purchase & Warranty and
/// Object Memory on top of what this shows.
///
/// The whole screen is built around one rule: nothing here may claim more than it can
/// justify. Every entity shows why it is believed to exist, every sighting shows the
/// date and place it came from, and an inferred place says that it was inferred (§11).
struct MemoryView: View {
    @ObservedObject var coordinator: IngestionCoordinator
    @State private var kind: String?

    private static let kinds = [
        ("person", "People", "person.2"),
        ("place", "Places", "mappin.and.ellipse"),
        ("object", "Things", "shippingbox"),
        ("document", "Papers", "doc.text"),
        ("purchase", "Purchases", "receipt"),
        ("event", "Events", "airplane"),
    ]

    var body: some View {
        List {
            if coordinator.memoryEntities.isEmpty {
                Section {
                    Text("Nothing yet. The library remembers people, places, things, "
                         + "documents, purchases and trips once it has looked inside "
                         + "your photos.")
                        .font(.callout)
                        .foregroundStyle(.secondary)
                }
            } else {
                filterSection
                ForEach(Self.kinds, id: \.0) { key, title, icon in
                    let rows = coordinator.memoryEntities.filter {
                        $0.kind == key && (kind == nil || kind == key)
                    }
                    if !rows.isEmpty {
                        Section {
                            ForEach(rows, id: \.entityID) { entity in
                                NavigationLink {
                                    EntityView(entity: entity, coordinator: coordinator)
                                } label: {
                                    row(entity, icon: icon)
                                }
                                .accessibilityIdentifier("memory-\(entity.entityID)")
                            }
                        } header: {
                            Text(title)
                        }
                    }
                }
            }
        }
        .navigationTitle("Memory")
    }

    private var filterSection: some View {
        Section {
            Picker("Show", selection: $kind) {
                Text("Everything").tag(String?.none)
                ForEach(Self.kinds, id: \.0) { key, title, _ in
                    Text(title).tag(String?.some(key))
                }
            }
        }
    }

    private func row(_ entity: Catalog.EntityRow, icon: String) -> some View {
        HStack(alignment: .top) {
            Image(systemName: icon).frame(width: 28).foregroundStyle(.tint)
            VStack(alignment: .leading, spacing: 2) {
                Text(entity.name)
                // The shelf, when it is coarser than the thing. `Objects` has no leaf
                // for a suitcase, so a suitcase files under `Objects > Other` — and
                // showing both is what stops the catalogue looking finer than it is.
                if let path = entity.categoryPath, !path.hasSuffix(entity.name) {
                    Text("filed under \(path)")
                        .font(.caption2).foregroundStyle(.secondary)
                }
            }
            Spacer()
            Text("\(coordinator.sightingCount(of: entity.entityID))")
                .foregroundStyle(.secondary).monospacedDigit()
        }
    }
}

/// One thing, and every time the library saw it.
struct EntityView: View {
    let entity: Catalog.EntityRow
    @ObservedObject var coordinator: IngestionCoordinator

    var body: some View {
        List {
            Section {
                Text(entity.why).font(.callout)
                if let path = entity.categoryPath {
                    // The honest limit, said where it matters rather than in a footnote.
                    // Telling one suitcase from another is per-category entity
                    // resolution (§24 Gate 2), and for objects this build cannot do it.
                    Text("The library recognises \(entity.name.lowercased())s and files "
                         + "them under \(path). It cannot yet tell one from another, so "
                         + "these may not all be the same one.")
                        .font(.caption).foregroundStyle(.secondary)
                }
            } header: {
                Text("Why the library thinks this exists")
            }

            Section("Seen") {
                ForEach(coordinator.sightings(of: entity.entityID), id: \.assetID) { s in
                    VStack(alignment: .leading, spacing: 2) {
                        HStack {
                            Text(EntityView.day(s.seenAt))
                            Spacer()
                            Text(s.place ?? "no recorded location")
                                .foregroundStyle(.secondary)
                        }
                        .font(.callout)
                        // §11: an inference must never be shown as a measurement.
                        if s.placeIsInferred {
                            Text("place worked out from nearby photos, not recorded by "
                                 + "the camera")
                                .font(.caption2).foregroundStyle(.orange)
                        }
                        Text(s.reason).font(.caption).foregroundStyle(.secondary)
                        if s.repeatsAsset != nil {
                            Text("another shot from the same moment")
                                .font(.caption2).foregroundStyle(.secondary)
                        }
                    }
                }
            }
        }
        .navigationTitle(entity.name)
        .navigationBarTitleDisplayMode(.inline)
    }

    static func day(_ iso: String?) -> String {
        guard let iso else { return "no date" }
        return String(iso.prefix(10))
    }
}
