import Foundation
import Vision
import UIKit

/// C-1 — OCR must be GATED, not universal.
/// Running text recognition over 100k assets is the single most likely cause of an
/// A1 failure. The gate ratio, not raw OCR speed, is expected to decide A1 — and
/// that expectation is itself a benchmark output, not an assumption to hide.
enum OCRGate {

    struct Decision { let run: Bool; let reason: String }

    /// Cheap signals only. Must never itself decode a full-resolution image.
    static func decide(record: AssetRecord, textLikelihood: Double) -> Decision {
        if record.isScreenshot { return Decision(run: true, reason: "screenshot-subtype") }

        // Screen-shaped aspect ratios (portrait phone screens, shared screenshots).
        if record.pxW > 0 && record.pxH > 0 {
            let ar = Double(record.pxH) / Double(record.pxW)
            if ar > 1.6 && ar < 2.4 { return Decision(run: true, reason: "screen-aspect") }
        }
        if textLikelihood > 0.55 { return Decision(run: true, reason: "text-likelihood") }
        return Decision(run: false, reason: "gated-out")
    }

    /// .fast is deliberate: Tier 0-A measures throughput feasibility, not OCR quality.
    /// Accuracy of recognised text is a Tier 1 concern.
    static func recognise(_ image: UIImage) -> String {
        guard let cg = image.cgImage else { return "" }
        let req = VNRecognizeTextRequest()
        req.recognitionLevel = .fast
        req.usesLanguageCorrection = false
        let handler = VNImageRequestHandler(cgImage: cg, options: [:])
        do {
            try handler.perform([req])
            guard let obs = req.results else { return "" }
            return obs.compactMap { $0.topCandidates(1).first?.string }.joined(separator: " ")
        } catch {
            return ""
        }
    }
}
