import Foundation
import UIKit

/// Exactly the §4 schema. Column order is FIXED — analysis scripts depend on it.
/// PF-01: this file accepts MEASURED values only. Never write a prediction here.
struct BenchmarkRow {
    var device_model = MetricsCSV.deviceModel()
    var chip = ""                       // filled from a lookup or entered by the operator
    var ram_gb = MetricsCSV.ramGB()
    var ios_version = UIDevice.current.systemVersion
    var library_size = 0
    var storage_state = ""              // "all-local" | "icloud-optimised"
    var run_type = ""                   // "cold" | "resume" | "incremental" | "background"

    var wall_time_s: Double = 0
    var assets_indexed = 0
    var assets_failed = 0
    var throughput_assets_per_s: Double = 0

    var peak_mem_mb: Double = 0
    var mem_footprint_at_kill: Double = 0
    var avg_cpu_pct: Double = 0

    var thermal_nominal_s: Double = 0
    var thermal_fair_s: Double = 0
    var thermal_serious_s: Double = 0
    var thermal_critical_s: Double = 0

    var battery_start_pct: Double = 0
    var battery_end_pct: Double = 0
    var battery_drain_pct_per_10k: Double = 0

    var index_bytes_total: Int64 = 0
    var index_bytes_per_asset: Double = 0

    var interrupted_count = 0
    var resumed_ok = false
    var assets_reprocessed_after_resume = 0

    var ocr_attempted = 0
    var ocr_gated_out = 0
    var embed_attempted = 0

    var icloud_fetch_required_count = 0
    var icloud_fetch_skipped_count = 0

    // Extra columns beyond §4 — appended, never inserted, so the fixed prefix stays stable.
    var real_asset_count = 0            // DEC-009: real vs synthetic reported separately
    var synthetic_asset_count = 0
    var first_screen_stall_ms: Double = 0   // CD-2
    var cold_launch_to_first_asset_ms: Double = 0 // CD-1
    var index_state_recovered_after_kill = false  // CD-5
    var bg_expiration_events = 0
    var memory_warnings = 0
    var ocr_ms_per_asset: Double = 0
    var embed_ms_per_asset: Double = 0
    var notes = ""
}

enum MetricsCSV {

    static let header = [
        "device_model","chip","ram_gb","ios_version","library_size","storage_state","run_type",
        "wall_time_s","assets_indexed","assets_failed","throughput_assets_per_s",
        "peak_mem_mb","mem_footprint_at_kill","avg_cpu_pct",
        "thermal_nominal_s","thermal_fair_s","thermal_serious_s","thermal_critical_s",
        "battery_start_pct","battery_end_pct","battery_drain_pct_per_10k",
        "index_bytes_total","index_bytes_per_asset",
        "interrupted_count","resumed_ok","assets_reprocessed_after_resume",
        "ocr_attempted","ocr_gated_out","embed_attempted",
        "icloud_fetch_required_count","icloud_fetch_skipped_count",
        "real_asset_count","synthetic_asset_count",
        "first_screen_stall_ms","cold_launch_to_first_asset_ms","index_state_recovered_after_kill",
        "bg_expiration_events","memory_warnings","ocr_ms_per_asset","embed_ms_per_asset",
        "notes"
    ].joined(separator: ",")

    static func fields(_ r: BenchmarkRow) -> [String] {
        [ r.device_model, r.chip, String(r.ram_gb), r.ios_version, String(r.library_size),
          r.storage_state, r.run_type,
          f(r.wall_time_s), String(r.assets_indexed), String(r.assets_failed), f(r.throughput_assets_per_s),
          f(r.peak_mem_mb), f(r.mem_footprint_at_kill), f(r.avg_cpu_pct),
          f(r.thermal_nominal_s), f(r.thermal_fair_s), f(r.thermal_serious_s), f(r.thermal_critical_s),
          f(r.battery_start_pct), f(r.battery_end_pct), f(r.battery_drain_pct_per_10k),
          String(r.index_bytes_total), f(r.index_bytes_per_asset),
          String(r.interrupted_count), String(r.resumed_ok), String(r.assets_reprocessed_after_resume),
          String(r.ocr_attempted), String(r.ocr_gated_out), String(r.embed_attempted),
          String(r.icloud_fetch_required_count), String(r.icloud_fetch_skipped_count),
          String(r.real_asset_count), String(r.synthetic_asset_count),
          f(r.first_screen_stall_ms), f(r.cold_launch_to_first_asset_ms), String(r.index_state_recovered_after_kill),
          String(r.bg_expiration_events), String(r.memory_warnings), f(r.ocr_ms_per_asset), f(r.embed_ms_per_asset),
          r.notes ]
    }

    private static func f(_ d: Double) -> String { String(format: "%.3f", d) }

    private static func escape(_ s: String) -> String {
        if s.contains(",") || s.contains("\"") || s.contains("\n") {
            return "\"" + s.replacingOccurrences(of: "\"", with: "\"\"") + "\""
        }
        return s
    }

    static var url: URL {
        let dir = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        return dir.appendingPathComponent("DEVICE_BENCHMARK_TIER0.csv")
    }

    /// Append-only. Survives app death — a row written is a row kept (E-07).
    static func append(_ row: BenchmarkRow) {
        let line = fields(row).map(escape).joined(separator: ",") + "\n"
        let u = url
        if !FileManager.default.fileExists(atPath: u.path) {
            try? (header + "\n").write(to: u, atomically: true, encoding: .utf8)
        }
        if let h = try? FileHandle(forWritingTo: u) {
            h.seekToEndOfFile()
            h.write(Data(line.utf8))
            try? h.close()
        }
    }

    static func deviceModel() -> String {
        var sysinfo = utsname(); uname(&sysinfo)
        let raw = withUnsafePointer(to: &sysinfo.machine) {
            $0.withMemoryRebound(to: CChar.self, capacity: 1) { String(validatingUTF8: $0) ?? "" }
        }
        return raw
    }

    static func ramGB() -> Int {
        Int((Double(ProcessInfo.processInfo.physicalMemory) / 1_073_741_824.0).rounded())
    }
}
