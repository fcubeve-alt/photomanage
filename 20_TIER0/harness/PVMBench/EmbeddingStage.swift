import Foundation
import Vision
import UIKit

/// Constitution §25 Layer 2 — lightweight visual understanding.
///
/// P-04 compliance: this uses Apple-native `VNGenerateImageFeaturePrintRequest`,
/// which bundles NO model and adds ZERO bytes to the binary. That is the route the
/// Constitution says to test first. A third-party embedding model may only be
/// introduced if this one demonstrably fails a specific requirement — and it would
/// now have to beat a shipped 262 MB baseline (OPERATING_RULES P-04).
enum EmbeddingStage {

    static func featurePrint(_ image: UIImage) -> Data? {
        guard let cg = image.cgImage else { return nil }
        let req = VNGenerateImageFeaturePrintRequest()
        let handler = VNImageRequestHandler(cgImage: cg, options: [:])
        do {
            try handler.perform([req])
            guard let obs = req.results?.first as? VNFeaturePrintObservation else { return nil }
            return obs.data
        } catch {
            return nil
        }
    }

    /// Available for later similarity work; unused during the throughput run so it
    /// does not contaminate timing.
    static func distance(_ a: VNFeaturePrintObservation, _ b: VNFeaturePrintObservation) -> Float? {
        var d = Float(0)
        do { try a.computeDistance(&d, to: b); return d } catch { return nil }
    }
}
