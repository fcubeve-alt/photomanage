import SwiftUI

/// §23 STRUCTURE FIRST, PHOTOS SECOND.
///
/// "首页首先展示秩序和目录，而不是再次展示一条无限滚动的照片流。用户应该像进入图书馆目录
/// 一样，一眼看到自己的视觉资产已经被组织。"
///
/// So: no grid of thumbnails on the first screen. Categories, counts, and what the
/// system has already done — which is also §12's first value moment, *"原来我的照片可以
/// 这么整齐，而且我不用自己整理"*.
struct HomeView: View {
    @ObservedObject var coordinator: IngestionCoordinator
    @State private var showingPlan = false

    var body: some View {
        NavigationStack {
            List {
                switch coordinator.phase {
                case .needsPermission:
                    permissionSection
                case .failed(let message):
                    Section { Text(message).foregroundStyle(.secondary) }
                case .breadth:
                    Section { ProgressView("Reading your library…") }
                default:
                    statusSection
                    categoriesSection
                    maintenanceSection
                }
            }
            .navigationTitle("Library")
            .task { if coordinator.phase == .idle { coordinator.start() } }
            .sheet(isPresented: $showingPlan) {
                if let plan = coordinator.plan { PlanView(plan: plan, coordinator: coordinator) }
            }
        }
    }

    private var permissionSection: some View {
        Section {
            Text("This app catalogues the photos already on your phone. Nothing is uploaded.")
                .font(.callout)
            Button("Allow access to photos") { coordinator.requestPermission() }
        }
    }

    /// The first thing the user sees is what the system has already done for them, not
    /// a set of buttons asking them to start something.
    private var statusSection: some View {
        Section {
            if let ttfuv = coordinator.ttfuvSeconds {
                Label {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("\(coordinator.libraryCount) photos, already sorted")
                            .font(.headline)
                        Text("Shelves ready in \(String(format: "%.1f", ttfuv)) seconds — "
                             + "dates, places, trips and screenshots.")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                } icon: {
                    Image(systemName: "checkmark.circle.fill").foregroundStyle(.green)
                }
            }
            if case .depth(let done, let total) = coordinator.phase {
                VStack(alignment: .leading, spacing: 4) {
                    ProgressView(value: Double(done), total: Double(max(1, total)))
                    Text(IngestionPlanner.progressReport(done: done, total: total))
                        .font(.caption).foregroundStyle(.secondary)
                }
            } else if coordinator.plan != nil {
                Button("Look inside the photos too…") { showingPlan = true }
                    .font(.callout)
            }
        }
    }

    private var categoriesSection: some View {
        Section("Browse") {
            ForEach(coordinator.topLevel, id: \.path) { entry in
                NavigationLink {
                    CategoryView(path: entry.path, coordinator: coordinator)
                } label: {
                    HStack {
                        Image(systemName: HomeView.icon(for: entry.path))
                            .frame(width: 28)
                            .foregroundStyle(.tint)
                        Text(entry.path)
                        Spacer()
                        Text("\(entry.count)")
                            .foregroundStyle(.secondary)
                            .monospacedDigit()
                    }
                }
            }
        }
    }

    private var maintenanceSection: some View {
        Section("Needs you") {
            NavigationLink {
                ReviewQueueView(coordinator: coordinator)
            } label: {
                HStack {
                    Image(systemName: "questionmark.circle").frame(width: 28)
                    Text("Review queue")
                    Spacer()
                    Text("\(coordinator.reviewCount)").foregroundStyle(.secondary).monospacedDigit()
                }
            }
        } footer: {
            Text("Only what the system could not decide on its own. §12 says this queue "
                 + "should stay very small — if it is large, that is a defect, not a to-do list.")
        }
    }

    static func icon(for root: String) -> String {
        switch root {
        case "Documents": return "doc.text"
        case "People": return "person.2"
        case "Screenshots": return "iphone"
        case "Places": return "mappin.and.ellipse"
        case "Travel": return "airplane"
        case "Objects": return "bicycle"
        case "Purchases": return "receipt"
        case "Clothing": return "tshirt"
        case "Work": return "briefcase"
        case "Downloads": return "arrow.down.circle"
        case "Timeline": return "calendar"
        default: return "folder"
        }
    }
}
