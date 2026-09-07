import SwiftUI
import PVMCore

/// §10 Intent Search, on screen.
///
/// The design rule for this screen is one sentence: **it must never let a result list
/// stand in for an answer it did not give.** So what the search understood, and what it
/// could not, sits above the results rather than under them — and when the query names
/// something the library cannot search, the results are not shown at all, because
/// showing the whole library would look like an answer.
struct SearchView: View {
    @ObservedObject var coordinator: IngestionCoordinator
    @State private var text = ""
    @State private var results: SearchResults?

    var body: some View {
        List {
            Section {
                TextField("What are you looking for?", text: $text)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                    .submitLabel(.search)
                    .onSubmit(run)
                    .accessibilityIdentifier("search-field")
                Button("Search", action: run)
                    .disabled(text.trimmingCharacters(in: .whitespaces).isEmpty)
                    .accessibilityIdentifier("search-run")
            } footer: {
                Text("In your own words — “找我的身份证正反面”, “receipts from 2026”, "
                     + "“Anna in Tokyo”.")
            }

            if let results {
                // Always first. A result list without this is a claim the search cannot
                // back, and an empty list without it is a false statement about the
                // user's photos.
                Section("What I did") {
                    Text(results.summary)
                        .font(.callout)
                        .foregroundStyle(results.hits.isEmpty ? .secondary : .primary)
                        .accessibilityIdentifier("search-summary")
                }

                if !results.query.unresolved.isEmpty {
                    Section {
                        ForEach(results.query.unresolved, id: \.self) { term in
                            Label(term, systemImage: "questionmark.circle")
                                .foregroundStyle(.orange)
                        }
                    } header: {
                        Text("Not something this library is indexed by")
                    } footer: {
                        Text("Searching for these needs an index the app does not build "
                             + "yet. It is a limit of the search, not of your library.")
                    }
                }

                if !results.hits.isEmpty {
                    Section("Found") {
                        ForEach(results.hits, id: \.assetID) { hit in
                            NavigationLink {
                                AssetDetailView(assetID: hit.assetID, coordinator: coordinator)
                            } label: {
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(hit.assetID).font(.callout)
                                    Text(hit.why).font(.caption2).foregroundStyle(.secondary)
                                }
                            }
                            .accessibilityIdentifier("result-\(hit.assetID)")
                        }
                    }
                }

                if !results.sides.isEmpty {
                    Section {
                        ForEach(results.sides, id: \.self) { group in
                            Text(group.joined(separator: "  ·  ")).font(.callout)
                        }
                    } header: {
                        Text("Sides or pages of the same document")
                    } footer: {
                        Text("Read from what the entity resolver decided, not worked out "
                             + "again here.")
                    }
                }
            }
        }
        .navigationTitle("Search")
    }

    private func run() {
        guard let catalog = coordinator.catalog else { return }
        results = Intent.search(catalog, text)
    }
}
