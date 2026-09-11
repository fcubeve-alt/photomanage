import Foundation
import Photos

/// **The product may not write to the photo library. This is where that is enforced.**
///
/// Before 2026-09-11 it was true that this app never deleted or modified a photo — but
/// it was true *by absence*. Nobody had written the code yet. A third-party audit made
/// the point that a safety property which holds because a feature is unfinished is not
/// a safety property at all, and it is right: the moment someone implements
/// `Action.suggestDelete` end to end, the guarantee silently stops holding and no test
/// fails.
///
/// So it is a gate now. Every route to `PHPhotoLibrary.shared().performChanges` has to
/// come through `LibrarySafety.permitWrite`, and in the only mode this build ships,
/// that function returns a refusal. Turning it off is a deliberate edit with a test
/// that fails, not an omission anybody can make by accident.
///
/// **What has to be true before the mode changes** — this is the Tier 0 A3 list, and
/// none of it has been done on a physical device:
///
/// 1. A real deletion lands in Recently Deleted and is restorable for 30 days (§7's
///    tolerance argument rests entirely on this and it has never been observed).
/// 2. The catalogue and the library stay consistent when the app is killed mid-apply.
/// 3. Re-running an apply that was interrupted does not act twice.
/// 4. Revoking photo permission mid-apply fails safely.
/// 5. Low storage and an iCloud-optimised library both behave.
///
/// Simulator runs, synthetic corpora and policy unit tests cannot establish any of
/// these. Photographs and identity documents are not recoverable from a correct
/// argument.
public enum LibrarySafety {

    public enum Mode: String {
        /// Ships. Reads and catalogues; proposals are shown and never applied.
        case readOnly
        /// Writes confined to assets this app itself created. For the device campaign.
        case ownAssetsOnly
        /// Unrestricted. Not reachable until the five checks above are evidence.
        case full
    }

    /// The one place the mode is decided.
    public static let mode: Mode = .readOnly

    public struct Refusal: Error, CustomStringConvertible {
        public let reason: String
        public var description: String { reason }
    }

    /// Ask permission to modify the user's library. In `readOnly` this always throws.
    ///
    /// Call it at the point of the write, not at the point of the decision — a
    /// proposal is allowed to exist, be stored, be shown and be confirmed by the user.
    /// What is refused is the change itself.
    public static func permitWrite(_ what: String) throws {
        switch mode {
        case .readOnly:
            throw Refusal(reason:
                "This build does not modify your photo library. \(what) was recorded "
                + "as a suggestion and nothing was changed. Acting on suggestions is "
                + "switched off until deletion and restore have been verified on a "
                + "physical device.")
        case .ownAssetsOnly, .full:
            return
        }
    }

    /// What the app needs from PhotoKit.
    ///
    /// `.readWrite` was requested until 2026-09-11, and there has never been a single
    /// `PHAssetChangeRequest` in the app — so the most alarming permission iOS can
    /// show for photographs was being asked for, on first launch, by a product whose
    /// entire pitch is that it does not touch anything. That is a privacy claim and a
    /// conversion cost paid for nothing.
    ///
    /// It follows the mode rather than being hard-coded, so that raising the mode also
    /// raises the request and the two cannot drift apart.
    public static var requiredAccessLevel: PHAccessLevel {
        mode == .readOnly ? .read : .readWrite
    }

    /// Shown wherever the UI would otherwise imply something will be removed.
    public static var userFacingNote: String {
        switch mode {
        case .readOnly:
            return "Nothing here deletes or changes a photo. Suggestions are recorded "
                 + "so you can see them; acting on them is switched off until it has "
                 + "been proven safe on a real device."
        case .ownAssetsOnly:
            return "Only photos this app created itself can be changed."
        case .full:
            return "Removals go to Recently Deleted and stay undoable for 30 days."
        }
    }
}
