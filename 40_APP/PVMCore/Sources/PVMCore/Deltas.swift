import Foundation

/// CHANGE-DRIVEN PROCESSING — spend intelligence only where something changed.
///
/// Owner ruling (DEC-029): do not analyse every frame of a video or every shot in a
/// sequence. Compare frames; where almost nothing changed, do not pay again. This is
/// L1-B (Information-Change-First) applied to time, and the same idea as FC-1
/// generalised from duplicate stills to sequences.
///
/// THE CORRECTION THAT MATTERS, because the obvious version of this rule silently
/// destroys content. "Compare each frame with the one before it, skip if similar" fails
/// on a slow pan: every adjacent pair is similar, so nothing is ever processed, while
/// frame 1 and frame 500 are different scenes entirely. Drift is invisible pairwise and
/// obvious cumulatively.
///
/// So every comparison is against the **last frame actually processed** — the current
/// keyframe — never against the immediately preceding frame. A hard cap on consecutive
/// skips catches drift slower than the threshold forever.
///
/// THREE GUARDS, each one a way this rule loses data if left off:
///
/// * **FC-1a.** `dHash` returns 0 both for a whole class of ordinary images and for
///   every hash failure, so a failed hash is indistinguishable from a perfect match —
///   and "perfect match" is exactly what authorises a skip. An unusable hash always
///   processes. Skipping on a failure is the one bug here that would be invisible in
///   testing and unrecoverable in the field.
/// * **Documents.** Page 1 and page 2 of a contract are visually near-identical and
///   semantically unrelated. Visual similarity may never skip text extraction on
///   document-class content.
/// * **The first and last frame** are always processed. A sequence whose end was never
///   looked at is a sequence we cannot describe.
///
/// Mirrors `30_ENGINE/pvm/deltas.py`.

public struct Frame {
    public let index: Int
    public let dhash: UInt64?
    public let timestampSeconds: Double

    public init(index: Int, dhash: UInt64?, timestampSeconds: Double = 0) {
        self.index = index
        self.dhash = dhash
        self.timestampSeconds = timestampSeconds
    }

    public var hasUsableDHash: Bool { (dhash ?? 0) != 0 }
}

public struct FrameDecision {
    public let index: Int
    public let process: Bool
    public let reason: String
    public let distanceFromKeyframe: Int?
}

public struct SelectionResult {
    public var decisions: [FrameDecision] = []
    public var keyframes: [Int] = []

    public var total: Int { decisions.count }
    public var processed: Int { decisions.filter { $0.process }.count }
    public var skipped: Int { total - processed }
    public var processedFraction: Double {
        total > 0 ? Double(processed) / Double(total) : 0
    }

    /// The keyframes taken because something *changed*, as opposed to the periodic
    /// re-check the gate performs inside a static shot. The two mean opposite things to
    /// a segment, and this is the only place that knows which is which.
    public var newContentFrames: Set<Int> {
        Set(decisions.filter { $0.process && !$0.reason.hasPrefix(Deltas.samplingPrefix) }
            .map { $0.index })
    }
}

public struct CostEstimate {
    public let frames: Int
    public let processed: Int
    public let naiveMilliseconds: Double
    public let deltaMilliseconds: Double

    public var savedMilliseconds: Double { naiveMilliseconds - deltaMilliseconds }
    public var savedFraction: Double {
        naiveMilliseconds > 0 ? savedMilliseconds / naiveMilliseconds : 0
    }
}

public enum Deltas {
    /// Distance from the current keyframe that means "a new scene". Generous, because a
    /// cut is unambiguous in a 64-bit hash and a missed cut costs a whole scene.
    public static let cutBits = 18
    /// Distance that means "drifted far enough to be worth looking at again".
    public static let driftBits = 8
    /// Hard cap on consecutive skips, whatever the hashes say. Insurance against drift
    /// that stays under the threshold forever — a very slow pan, a gradual fade.
    public static let maxSkipRun = 30

    /// Measured stage costs, so the saving is arithmetic rather than a claim.
    /// `20_TIER0/evidence/T0A_SCALE_SIMULATOR_2026-09-06.md`, slower of the two runs.
    /// Not a device result (PF-01).
    public static let decodeMilliseconds = 12.42
    public static let hashMilliseconds = 0.66
    public static let deepMilliseconds = 131.08 + 9.62   // embedding + amortised OCR

    static let samplingPrefix = "\(maxSkipRun) frames skipped in a row"

    public static func selectKeyframes(_ frames: [Frame],
                                       isDocument: Bool = false) -> SelectionResult {
        var result = SelectionResult()
        guard !frames.isEmpty else { return result }

        var keyframe: Frame?
        var skipRun = 0
        let lastIndex = frames.count - 1

        func take(_ frame: Frame, _ reason: String, _ distance: Int? = nil) {
            result.decisions.append(FrameDecision(index: frame.index, process: true,
                                                  reason: reason,
                                                  distanceFromKeyframe: distance))
            result.keyframes.append(frame.index)
            keyframe = frame
            skipRun = 0
        }

        for (i, frame) in frames.enumerated() {
            if i == 0 { take(frame, "first frame"); continue }
            if i == lastIndex {
                take(frame, "last frame — where the sequence ends up"); continue
            }
            if isDocument {
                // Pages look alike and say different things. This is the Document-class
                // False Merge, one dimension over.
                take(frame, "document content — visual similarity may not skip text")
                continue
            }
            if !frame.hasUsableDHash {
                take(frame, "no usable hash — a failed hash is not a match (FC-1a)")
                continue
            }
            guard let current = keyframe, current.hasUsableDHash,
                  let a = frame.dhash, let b = current.dhash else {
                take(frame, "no usable keyframe to compare against")
                continue
            }

            let distance = hamming(a, b)
            if distance >= cutBits {
                take(frame, "scene change", distance)
            } else if distance >= driftBits {
                take(frame, "drifted far enough from the last frame we looked at", distance)
            } else if skipRun >= maxSkipRun {
                take(frame, "\(samplingPrefix) — sampling anyway", distance)
            } else {
                skipRun += 1
                result.decisions.append(FrameDecision(
                    index: frame.index, process: false,
                    reason: "unchanged since the last keyframe",
                    distanceFromKeyframe: distance))
            }
        }
        return result
    }

    /// Every frame still pays decode + hash — that is what the gate costs, and a gate
    /// whose own cost is hidden is not a measurement. Only the deep stages are skipped.
    public static func estimateCost(_ result: SelectionResult) -> CostEstimate {
        let n = Double(result.total)
        let gate = n * (decodeMilliseconds + hashMilliseconds)
        return CostEstimate(
            frames: result.total,
            processed: result.processed,
            naiveMilliseconds: n * (decodeMilliseconds + hashMilliseconds + deepMilliseconds),
            deltaMilliseconds: gate + Double(result.processed) * deepMilliseconds)
    }
}
