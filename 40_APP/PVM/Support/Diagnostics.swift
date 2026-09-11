import Foundation
import PVMCore
#if canImport(UIKit)
import UIKit
#endif

/// THE SUPPORT REPORT — and the rule that makes it safe to send.
///
/// A user with a broken catalogue needs to be able to tell us something useful, and the
/// usual way to arrange that is a "send diagnostics" button that attaches a log the
/// user never sees. That is not available here. The catalogue holds text read out of
/// photographs by OCR — passport numbers, bank statements, contracts — so any log built
/// by concatenating whatever was to hand is a data breach waiting for one careless
/// `\(assetID)`.
///
/// The rule this file implements: **the report is numbers, versions and enumerated
/// names only, and the user reads the whole of it before it goes anywhere.** There is
/// no field they cannot see. `LaunchReadinessTests` asserts the shape — no identifiers,
/// no file paths, no free text taken from the library — so a future edit that adds one
/// fails the build rather than shipping.
enum Diagnostics {

    /// Version and OS. Written into every crash report, so it must be free of anything
    /// about the user or their library.
    static var buildSummary: String {
        let info = Bundle.main.infoDictionary ?? [:]
        let version = info["CFBundleShortVersionString"] as? String ?? "?"
        let build = info["CFBundleVersion"] as? String ?? "?"
        #if canImport(UIKit)
        let os = UIDevice.current.systemVersion
        #else
        let os = ProcessInfo.processInfo.operatingSystemVersionString
        #endif
        return "app \(version) (\(build)) · iOS \(os) · \(hardwareModel) · engine \(Catalog.defaultFingerprint) · schema \(Catalog.schemaVersion)"
    }

    /// `iPhone11,8` rather than a marketing name: it is what a crash needs and it does
    /// not become more identifying the more precisely it is stated.
    static var hardwareModel: String {
        var info = utsname()
        uname(&info)
        let machine = withUnsafeBytes(of: &info.machine) { raw -> String in
            let bytes = raw.prefix(while: { $0 != 0 })
            return String(decoding: bytes, as: UTF8.self)
        }
        return machine.isEmpty ? "unknown" : machine
    }

    /// The whole report, exactly as the user will see it and exactly as it is sent.
    static func report(catalog: Catalog?, phase: String) -> String {
        var lines: [String] = []
        lines.append("PVM support report")
        lines.append(buildSummary)
        lines.append("library access: \(LibrarySafety.mode.rawValue)")
        // Empty is the expected value. Printed either way, because a security control
        // that quietly did not take effect is precisely the thing a support report
        // exists to surface.
        lines.append("catalogue protection: "
                     + (protectionFailures.isEmpty ? "applied"
                        : "INCOMPLETE — " + protectionFailures.joined(separator: ", ")))
        lines.append("phase: \(phase)")

        guard let catalog else {
            lines.append("catalogue: not open")
            return lines.joined(separator: "\n")
        }

        let plan: String
        switch catalog.migrationPlan {
        case .fresh: plan = "fresh"
        case .current: plan = "current"
        case .rebuildDerived(let from): plan = "rebuilt from schema \(from)"
        case .unversionedLegacy: plan = "rebuilt from an unversioned file"
        case .newerThanThisBuild(let found): plan = "file is schema \(found), newer than this build"
        }
        lines.append("catalogue schema: opened \(catalog.openedSchemaVersion) → \(plan)")

        lines.append("integrity: \(catalog.integrityCheck())")
        lines.append("size on disk: \(catalog.sizeOnDisk()) bytes")
        lines.append("indexed assets: \(catalog.scalar("SELECT COUNT(*) FROM assets;"))")
        lines.append("awaiting review: \(catalog.scalar("SELECT COUNT(*) FROM assets WHERE needs_review = 1;"))")
        lines.append("entities: \(catalog.scalar("SELECT COUNT(*) FROM entities;"))")
        lines.append("user decisions: \(catalog.scalar("SELECT COUNT(*) FROM decisions;"))")

        // Counts per §4 大类. The names come from the shipped taxonomy, not from the
        // library — every possible value is in the binary already — so this reveals
        // how many of each class exist and nothing about any one of them.
        let byClass = catalog.classCounts()
        // The file's own answer about its shape, not the version stamp's claim about
        // it. Non-empty here means a migration reported success and did not work.
        let gaps = catalog.missingColumns()
        if !gaps.isEmpty {
            lines.append("SCHEMA GAPS: " + gaps.joined(separator: " "))
        }
        if !byClass.isEmpty {
            lines.append("by class: " + byClass.sorted { $0.key < $1.key }
                .map { "\($0.key)=\($0.value)" }.joined(separator: " "))
        }
        return lines.joined(separator: "\n")
    }

    /// Everything the report can contain, spelled out for the screen that offers to
    /// send it. Kept next to the builder so the two cannot drift apart silently.
    static let contentsExplanation = """
    这份报告只包含：App 版本、系统版本、机型代号、目录数据库的结构版本与完整性、\
    各计数（已编入目录的数量、待复核数量、实体数量、你做过的决定数量）、以及每个大类的数量。

    它不包含：任何照片、任何照片的标识符、任何文件路径、任何由 OCR 从照片中读出的文字。\
    发送前完整内容会显示在上面，你看到什么就发送什么。
    """
}
