import Foundation

/// THE INPUT CONTRACT — everything the classifier is allowed to see.
///
/// A field may exist here only if a real iPhone can produce it for a real photo:
/// PhotoKit metadata, a Vision OCR string, Vision scene labels, Vision face clusters,
/// a hash we computed ourselves. Nothing else. That constraint is what stops a
/// classifier that scores beautifully in evaluation and cannot run on a phone.
///
/// Mirrors `30_ENGINE/pvm/signals.py`. The engine is the reference implementation;
/// this is what ships.

/// What a signal costs, ascending — and the order the engine escalates in.
/// OCR sits last because C-1 predicts it dominates per-asset cost. The T0-A scale
/// sweep measured the embedding dominating instead, on a host with no Neural Engine;
/// that finding is IN DOUBT rather than settled, so the order stands until a device
/// says otherwise.
public enum Tier: Int, Comparable, CaseIterable {
    case metadata = 0
    case hash = 1
    case visual = 2
    case faces = 3
    case text = 4

    public var label: String {
        switch self {
        case .metadata: return "metadata"
        case .hash: return "hash"
        case .visual: return "visual"
        case .faces: return "faces"
        case .text: return "ocr"
        }
    }

    public static func < (a: Tier, b: Tier) -> Bool { a.rawValue < b.rawValue }
}

/// A GPS fix carried by the asset itself. §11: an inferred location must declare lower
/// confidence than a measured one, and the two must never be conflated.
public struct GeoFix {
    public enum Source: String { case exif, inferred }

    public let lat: Double
    public let lon: Double
    public let source: Source

    public init(lat: Double, lon: Double, source: Source = .exif) {
        self.lat = lat
        self.lon = lon
        self.source = source
    }

    public var confidence: Double { source == .exif ? 1.0 : 0.6 }

    public func km(to other: GeoFix) -> Double {
        let r = 6371.0
        let p1 = lat * .pi / 180, p2 = other.lat * .pi / 180
        let dp = p2 - p1
        let dl = (other.lon - lon) * .pi / 180
        let a = sin(dp / 2) * sin(dp / 2) + cos(p1) * cos(p2) * sin(dl / 2) * sin(dl / 2)
        return 2 * r * asin(min(1.0, sqrt(a)))
    }
}

/// Reverse-geocoded names, separate from the fix because geocoding can fail while the
/// coordinates stay perfectly good.
public struct PlaceName {
    public let country: String?
    public let city: String?
    public let confidence: Double

    public init(country: String?, city: String?, confidence: Double) {
        self.country = country
        self.city = city
        self.confidence = confidence
    }
}

public struct SceneLabel {
    public let identifier: String
    public let confidence: Double
    public init(identifier: String, confidence: Double) {
        self.identifier = identifier
        self.confidence = confidence
    }
}

/// Vision gives a cluster; the user gives it a name. An unnamed cluster is still
/// evidence that a person is present, and that alone changes the risk class.
public struct FaceCluster {
    public let clusterID: String
    public let name: String?
    public let areaFraction: Double
    public init(clusterID: String, name: String? = nil, areaFraction: Double = 0) {
        self.clusterID = clusterID
        self.name = name
        self.areaFraction = areaFraction
    }
}

public struct AssetSignals {
    public var assetID: String

    // Tier.metadata — free, already in the PhotoKit row
    public var createdAt: Date?
    public var modifiedAt: Date?
    public var pixelW: Int = 0
    public var pixelH: Int = 0
    public var byteSize: Int64 = 0
    public var isVideo = false
    public var durationSeconds: Double = 0
    public var isScreenshot = false
    public var isScreenRecording = false
    public var burstID: String?
    /// Where the pixels came from — derived from PHAssetResource and the absence of
    /// camera EXIF, never guessed from a filename alone.
    public var source: String = "unknown"       // camera | screenshot | downloaded | shared | unknown
    public var geo: GeoFix?
    public var place: PlaceName?

    // Tier.hash
    public var contentHash: String?
    public var dhash: UInt64?

    // Tier.text
    public var ocrRan = false
    public var ocrText: String = ""

    // Tier.visual / .faces
    public var sceneLabels: [SceneLabel] = []
    public var faceClusters: [FaceCluster] = []

    public init(assetID: String) { self.assetID = assetID }

    public var aspectRatio: Double { pixelW > 0 ? Double(pixelH) / Double(pixelW) : 0 }

    public var namedPeople: [String] {
        Array(Set(faceClusters.compactMap { $0.name })).sorted()
    }

    /// FC-1a, and this is not pedantry: `dHash` returns 0 both for a whole class of
    /// ordinary images and for every hash failure. Treating 0 as a value would link
    /// unrelated photos as duplicates and make a failed hash indistinguishable from a
    /// confident match. Zero is a miss, not a hash.
    public var hasUsableDHash: Bool { (dhash ?? 0) != 0 }

    public var year: Int? {
        guard let d = createdAt else { return nil }
        return Calendar(identifier: .gregorian).component(.year, from: d)
    }
}

public func hamming(_ a: UInt64, _ b: UInt64) -> Int { (a ^ b).nonzeroBitCount }
