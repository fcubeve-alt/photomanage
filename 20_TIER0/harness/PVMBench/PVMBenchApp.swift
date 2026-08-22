import SwiftUI
import UIKit
import Photos

@main
struct PVMBenchApp: App {
    @StateObject private var runner = BenchmarkRunner()

    init() {
        // CD-1: PhotoKit initialisation timing is measured from app launch, so
        // registration happens as early as possible.
        UIApplication.shared.isIdleTimerDisabled = true   // long runs must not sleep
    }

    var body: some Scene {
        WindowGroup {
            ContentView(runner: runner)
                .onAppear { BackgroundIndexing.register(runner: runner) }
        }
    }
}
