import Foundation
import UIKit

/// §4 instrumentation. Thermal is measured as DWELL TIME, not spot readings —
/// a single sample is worthless; the question is how long we sit in each state.
final class Telemetry {

    struct Snapshot {
        var wallStart = Date()
        var thermalDwell: [ProcessInfo.ThermalState: TimeInterval] = [:]
        var peakFootprintMB: Double = 0
        var cpuSamples: [Double] = []
        var batteryStart: Float = -1
        var batteryEnd: Float = -1
        var expirationEvents: Int = 0      // C-4: BGProcessingTask expirations
        var memoryWarnings: Int = 0
    }

    private(set) var snap = Snapshot()
    private var timer: DispatchSourceTimer?
    private var lastSample = Date()
    private var lastThermal = ProcessInfo.processInfo.thermalState
    private let queue = DispatchQueue(label: "pvm.telemetry")

    func start() {
        UIDevice.current.isBatteryMonitoringEnabled = true
        snap = Snapshot()
        snap.batteryStart = UIDevice.current.batteryLevel
        lastSample = Date()
        lastThermal = ProcessInfo.processInfo.thermalState

        NotificationCenter.default.addObserver(
            self, selector: #selector(didReceiveMemoryWarning),
            name: UIApplication.didReceiveMemoryWarningNotification, object: nil)

        let t = DispatchSource.makeTimerSource(queue: queue)
        t.schedule(deadline: .now() + 5, repeating: 5)   // §4: 5s cadence
        t.setEventHandler { [weak self] in self?.sample() }
        t.resume()
        timer = t
    }

    func stop() {
        timer?.cancel(); timer = nil
        sample()                                  // close the final interval
        snap.batteryEnd = UIDevice.current.batteryLevel
        NotificationCenter.default.removeObserver(self)
    }

    func noteExpiration() { queue.sync { snap.expirationEvents += 1 } }

    @objc private func didReceiveMemoryWarning() { queue.sync { snap.memoryWarnings += 1 } }

    private func sample() {
        let now = Date()
        let dt = now.timeIntervalSince(lastSample)
        snap.thermalDwell[lastThermal, default: 0] += dt
        lastSample = now
        lastThermal = ProcessInfo.processInfo.thermalState

        let mb = Telemetry.footprintMB()
        if mb > snap.peakFootprintMB { snap.peakFootprintMB = mb }
        snap.cpuSamples.append(Telemetry.cpuPercent())
    }

    // Jetsam kills are footprint-driven, so measure footprint — not resident size,
    // and not the Xcode gauge (§4).
    static func footprintMB() -> Double {
        var info = task_vm_info_data_t()
        var count = mach_msg_type_number_t(MemoryLayout<task_vm_info_data_t>.size / MemoryLayout<integer_t>.size)
        let kr = withUnsafeMutablePointer(to: &info) {
            $0.withMemoryRebound(to: integer_t.self, capacity: Int(count)) {
                task_info(mach_task_self_, task_flavor_t(TASK_VM_INFO), $0, &count)
            }
        }
        guard kr == KERN_SUCCESS else { return 0 }
        return Double(info.phys_footprint) / 1_048_576.0
    }

    /// Headroom before Jetsam. Useful as an early-warning signal during long runs.
    static func availableMemoryMB() -> Double {
        return Double(os_proc_available_memory()) / 1_048_576.0
    }

    static func cpuPercent() -> Double {
        var threadList: thread_act_array_t?
        var threadCount: mach_msg_type_number_t = 0
        guard task_threads(mach_task_self_, &threadList, &threadCount) == KERN_SUCCESS,
              let threads = threadList else { return 0 }
        defer {
            vm_deallocate(mach_task_self_, vm_address_t(UInt(bitPattern: threads)),
                          vm_size_t(Int(threadCount) * MemoryLayout<thread_t>.stride))
        }
        var total: Double = 0
        for i in 0..<Int(threadCount) {
            var info = thread_basic_info()
            var c = mach_msg_type_number_t(THREAD_INFO_MAX)
            let kr = withUnsafeMutablePointer(to: &info) {
                $0.withMemoryRebound(to: integer_t.self, capacity: Int(c)) {
                    thread_info(threads[i], thread_flavor_t(THREAD_BASIC_INFO), $0, &c)
                }
            }
            if kr == KERN_SUCCESS, info.flags & TH_FLAGS_IDLE == 0 {
                total += Double(info.cpu_usage) / Double(TH_USAGE_SCALE) * 100.0
            }
        }
        return total
    }

    var avgCPU: Double { snap.cpuSamples.isEmpty ? 0 : snap.cpuSamples.reduce(0,+) / Double(snap.cpuSamples.count) }
    func dwell(_ s: ProcessInfo.ThermalState) -> TimeInterval { snap.thermalDwell[s] ?? 0 }
}

extension ProcessInfo.ThermalState {
    var label: String {
        switch self {
        case .nominal: return "nominal"
        case .fair: return "fair"
        case .serious: return "serious"
        case .critical: return "critical"
        @unknown default: return "unknown"
        }
    }
}
