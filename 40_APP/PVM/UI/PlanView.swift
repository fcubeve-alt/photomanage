import SwiftUI
import PVMCore

/// The paced depth pass, offered rather than imposed (L1 §24 Gate 1, DEC-029).
///
/// The user picks; the app does not decide for them how much of their evening their
/// phone spends on this.
struct PlanView: View {
    let plan: IngestionPlan
    @ObservedObject var coordinator: IngestionCoordinator
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            List {
                Section {
                    Text(plan.userMessage).font(.callout)
                }
                Section("How would you like this done?") {
                    ForEach(plan.options, id: \.key) { option in
                        Button {
                            dismiss()
                            coordinator.runDepthPass(limit: option.dailyAssets)
                        } label: {
                            VStack(alignment: .leading, spacing: 3) {
                                HStack {
                                    Text(option.label).font(.headline)
                                    if option.key == plan.recommended {
                                        Text("suggested")
                                            .font(.caption2)
                                            .padding(.horizontal, 6).padding(.vertical, 2)
                                            .background(Color.accentColor.opacity(0.15))
                                            .clipShape(Capsule())
                                    }
                                }
                                Text("\(option.dailyAssets) a day · about \(option.days) days")
                                    .font(.caption).foregroundStyle(.secondary)
                                Text(option.caveat).font(.caption2).foregroundStyle(.secondary)
                            }
                        }
                        .buttonStyle(.plain)
                    }
                }
                Section {
                    ForEach(plan.notes, id: \.self) { note in
                        Text(note).font(.caption2).foregroundStyle(.secondary)
                    }
                } header: {
                    Text("What we are assuming")
                }
            }
            .navigationTitle("Looking inside")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Not now") { dismiss() }
                }
            }
        }
    }
}
