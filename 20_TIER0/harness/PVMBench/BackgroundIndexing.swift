import Foundation
import BackgroundTasks

/// C-4 — foreground and background are different execution contexts with different
/// limits and must never be conflated into one throughput number.
///
/// Background scheduling is a privilege the system withdraws from apps that
/// misbehave: overrunning without handling expiration risks termination AND
/// throttled future scheduling. A1 and A3 are therefore coupled — sloppy expiration
/// handling degrades throughput permanently, not just once. Every expiration is logged.
enum BackgroundIndexing {

    static let taskID = "com.pvm.bench.index"

    static func register(runner: BenchmarkRunner) {
        BGTaskScheduler.shared.register(forTaskWithIdentifier: taskID, using: nil) { task in
            guard let t = task as? BGProcessingTask else { task.setTaskCompleted(success: false); return }
            handle(t, runner: runner)
        }
    }

    static func schedule() {
        let req = BGProcessingTaskRequest(identifier: taskID)
        req.requiresNetworkConnectivity = false
        req.requiresExternalPower = true          // bulk work belongs on the charger
        req.earliestBeginDate = Date(timeIntervalSinceNow: 60)
        do { try BGTaskScheduler.shared.submit(req) }
        catch { print("[BG] submit failed: \(error)") }
    }

    private static func handle(_ task: BGProcessingTask, runner: BenchmarkRunner) {
        schedule()   // always re-arm before doing work

        task.expirationHandler = {
            runner.telemetryRef.noteExpiration()
            runner.cancel()                       // checkpoint already durable (C-3)
            appendExpirationMarker()
            task.setTaskCompleted(success: false)
        }

        runner.storageState = runner.storageState
        runner.runCold(resume: true)              // background runs always resume

        // Poll for completion; the runner writes its own CSV row.
        DispatchQueue.global().async {
            while runner.isRunning { Thread.sleep(forTimeInterval: 1) }
            task.setTaskCompleted(success: true)
        }
    }

    private static func appendExpirationMarker() {
        var row = BenchmarkRow()
        row.run_type = "background"
        row.notes = "BGProcessingTask expired; work checkpointed and halted"
        MetricsCSV.append(row)
    }
}
