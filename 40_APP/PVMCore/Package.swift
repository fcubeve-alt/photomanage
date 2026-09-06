// swift-tools-version:5.9
import PackageDescription

/// The platform-independent half of the product, as its own package.
///
/// This exists for one practical reason: macOS CI minutes are billed at ten times the
/// Linux rate on a private repository, and they ran out. Everything in `PVMCore`
/// depends only on Foundation and SQLite — no UIKit, no PhotoKit, no Vision — so it
/// compiles and its tests run on Linux, where verification is roughly a tenth of the
/// cost and considerably faster.
///
/// The split is worth having on its own merits too. The classification logic, the risk
/// policy and the duplicate guards are the parts where being wrong is expensive, and
/// they now have no way to depend on a UI framework by accident.
let package = Package(
    name: "PVMCore",
    platforms: [.iOS(.v17), .macOS(.v13)],
    products: [
        .library(name: "PVMCore", targets: ["PVMCore"]),
    ],
    targets: [
        // Apple platforms ship SQLite3 as a module already; Linux needs it declared.
        .systemLibrary(name: "CSQLite", path: "Sources/CSQLite"),
        .target(
            name: "PVMCore",
            dependencies: [
                .target(name: "CSQLite", condition: .when(platforms: [.linux])),
            ],
            path: "Sources/PVMCore"
        ),
        .testTarget(name: "PVMCoreTests", dependencies: ["PVMCore"], path: "Tests/PVMCoreTests"),
    ]
)
