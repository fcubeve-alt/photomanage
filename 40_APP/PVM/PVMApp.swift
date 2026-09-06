import SwiftUI

@main
struct PVMApp: App {
    @StateObject private var coordinator = IngestionCoordinator()

    var body: some Scene {
        WindowGroup {
            HomeView(coordinator: coordinator)
                .task { LaunchFixture.applyIfRequested(to: coordinator) }
        }
    }
}

/// The Simulator on CI has no photo library, so there would be nothing to screenshot.
/// `-PVMFixture` seeds a small, deterministic library instead, which is also what makes
/// the screenshots stable enough to compare between runs.
///
/// Guarded by a launch argument rather than a build flag on purpose: the shipping build
/// contains this code and simply never runs it, so the screenshotted app is the same
/// binary as the real one.
enum LaunchFixture {
    static func applyIfRequested(to coordinator: IngestionCoordinator) {
        guard ProcessInfo.processInfo.arguments.contains("-PVMFixture") else { return }
        coordinator.loadFixture(FixtureLibrary.make())
    }
}
