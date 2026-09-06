import Foundation

/// A small, deterministic library used where a real photo library is not available: the
/// Simulator on CI (which has none) and the unit tests.
///
/// It is deliberately shaped like the hard cases rather than the easy ones — a passport,
/// a receipt cross-listed into two entries, an expired pickup code, a burst with one
/// genuinely different frame, a byte-identical re-download, and a Tokyo trip long enough
/// to be a trip. If a screenshot of the home screen looks right on this, it is because
/// the awkward assets landed correctly, not because everything was a holiday snap.
public enum FixtureLibrary {

    private static let london = GeoFix(lat: 51.5074, lon: -0.1278)
    private static let tokyo = GeoFix(lat: 35.6762, lon: 139.6503)
    private static let uk = PlaceName(country: "United Kingdom", city: "London", confidence: 0.9)
    private static let japan = PlaceName(country: "Japan", city: "Tokyo", confidence: 0.9)

    private static func date(_ y: Int, _ m: Int, _ d: Int, _ h: Int = 12) -> Date {
        var c = DateComponents()
        c.year = y; c.month = m; c.day = d; c.hour = h
        return Calendar(identifier: .gregorian).date(from: c) ?? Date()
    }

    public static func make() -> [AssetSignals] {
        var out: [AssetSignals] = []

        func add(_ id: String, _ build: (inout AssetSignals) -> Void) {
            var s = AssetSignals(assetID: id)
            s.pixelW = 4032; s.pixelH = 3024; s.byteSize = 520_000
            s.contentHash = "sha::\(id)"
            s.dhash = UInt64(abs(id.hashValue)) | 1
            build(&s)
            out.append(s)
        }

        // Documents — the class where being wrong is most expensive (§6 R5).
        add("doc-passport") { s in
            s.createdAt = date(2025, 6, 18); s.geo = london; s.place = uk
            s.source = "camera"; s.ocrRan = true; s.ocrText = "PASSPORT"
        }
        add("doc-id-front") { s in
            s.createdAt = date(2025, 6, 18, 14); s.geo = london; s.place = uk
            s.source = "camera"; s.ocrRan = true; s.ocrText = "ID CARD — FRONT"
        }
        // Contract pages: near-identical to look at, unrelated in content. The false
        // merge that Tier 1 calls make-or-break.
        for page in 1...4 {
            add("doc-contract-\(page)") { s in
                s.createdAt = date(2025, 3, 2, 9 + page); s.source = "camera"
                s.ocrRan = true; s.ocrText = "CONTRACT — PAGE \(page) OF 4"
                s.dhash = 0x99AA_BBCC_DDEE_FF00 | UInt64(page)
            }
        }

        // Purchases — cross-listed into Documents by the tree, one asset, two entries.
        add("buy-receipt") { s in
            s.createdAt = date(2026, 3, 15); s.source = "camera"
            s.ocrRan = true; s.ocrText = "RECEIPT — HEADPHONES £129.00"
        }
        add("buy-order") { s in
            s.createdAt = date(2026, 3, 14); s.isScreenshot = true; s.source = "screenshot"
            s.pixelW = 1170; s.pixelH = 2532
            s.ocrRan = true; s.ocrText = "ORDER CONFIRMATION — HEADPHONES"
        }

        // Screenshots, including one that has expired and one that has not.
        add("shot-pickup-old") { s in
            s.createdAt = date(2025, 1, 6); s.isScreenshot = true; s.source = "screenshot"
            s.pixelW = 1170; s.pixelH = 2532
            s.ocrRan = true; s.ocrText = "PICKUP CODE 4417 — LOCKER B12"
        }
        add("shot-chat") { s in
            s.createdAt = date(2026, 2, 2); s.isScreenshot = true; s.source = "screenshot"
            s.pixelW = 1170; s.pixelH = 2532
            s.ocrRan = true; s.ocrText = "delivered  read 14:02  whatsapp"
        }
        add("shot-plain") { s in
            s.createdAt = date(2026, 2, 3); s.isScreenshot = true; s.source = "screenshot"
            s.pixelW = 1170; s.pixelH = 2532
            s.ocrRan = true; s.ocrText = "SCREENSHOT"
        }

        // People. §6 puts these at R3 Personal — conservative, never auto-removed.
        for i in 0..<6 {
            add("person-anna-\(i)") { s in
                s.createdAt = date(2025, 8, 3 + i); s.source = "camera"
                s.geo = london; s.place = uk
                s.faceClusters = [FaceCluster(clusterID: "c-anna", name: "Anna", areaFraction: 0.3)]
            }
        }
        add("person-group") { s in
            s.createdAt = date(2025, 9, 9); s.source = "camera"
            s.faceClusters = [FaceCluster(clusterID: "c-anna", name: "Anna"),
                              FaceCluster(clusterID: "c-ben", name: "Ben")]
        }

        // Home: enough evening captures in London for it to be learned as home.
        for i in 0..<40 {
            add("home-\(i)") { s in
                s.createdAt = date(2025, 1, 1 + i, 21); s.source = "camera"
                s.geo = london; s.place = uk
            }
        }
        // ...and a run of days in Tokyo long enough to be a trip rather than a day out.
        for i in 0..<12 {
            add("tokyo-\(i)") { s in
                s.createdAt = date(2025, 4, 11 + i / 2, 10 + i % 8); s.source = "camera"
                s.geo = tokyo; s.place = japan
            }
        }

        // A burst where frame 4 is genuinely different (§8) — it must survive.
        for i in 0..<5 {
            add("burst-\(i)") { s in
                s.createdAt = date(2026, 4, 24, 16); s.source = "camera"
                s.geo = london; s.place = uk
                s.burstID = "burst-A"
                s.dhash = i == 4 ? 0x0F0F_0F0F_0F0F_0F0F : (0xF0F0_F0F0_F0F0_F0F0 | UInt64(i))
            }
        }

        // A byte-identical re-download. §6 R0 — the one case that may be tidied
        // automatically, because an identical copy demonstrably remains.
        add("meme-original") { s in
            s.createdAt = date(2025, 10, 16); s.source = "downloaded"
            s.contentHash = "sha::meme"
            s.sceneLabels = [SceneLabel(identifier: "meme", confidence: 0.9)]
        }
        add("meme-copy") { s in
            s.createdAt = date(2025, 11, 20); s.source = "downloaded"
            s.contentHash = "sha::meme"
            s.sceneLabels = [SceneLabel(identifier: "meme", confidence: 0.9)]
        }

        // An asset nothing can place. The engine must say so rather than invent a home.
        add("mystery") { s in
            s.createdAt = date(2026, 5, 5)
        }
        return out
    }
}
