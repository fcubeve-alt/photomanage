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

    /// What the app needs from PhotoKit — and it is `.readWrite` in every mode,
    /// because **iOS does not offer a read-only photo permission.**
    ///
    /// A third-party audit on 2026-09-11 recommended narrowing this to read-only, and
    /// that recommendation cannot be implemented: `PHAccessLevel` has exactly two
    /// members, `.addOnly` and `.readWrite`, and `.addOnly` is *write*-only — it lets
    /// an app add photos and not see any. An app that reads the library has one
    /// choice. The first attempt at the fix used `.read`, which does not exist, and
    /// the compiler said so.
    ///
    /// The audit's underlying point still stands and is answered elsewhere, because it
    /// was never really about the enum:
    ///
    /// * **The app cannot write, structurally.** `permitWrite` refuses, and
    ///   `check_no_photo_writes.py` fails the build if a PhotoKit mutation appears
    ///   outside this file. The permission is wider than the behaviour because the
    ///   platform gives no narrower permission — not because the behaviour is wide.
    /// * **`NSPhotoLibraryAddUsageDescription` is gone.** That one was genuinely
    ///   unnecessary, and it carried a promise — "recoverable for 30 days" — about
    ///   behaviour nobody has observed on a device.
    /// * **The sheet says so.** `NSPhotoLibraryUsageDescription` now ends with "this
    ///   version never deletes or changes a photo", which is the only part of this a
    ///   user actually reads.
    ///
    /// Kept as a computed property rather than a constant so that the day the mode
    /// changes, this is where someone looks.
    public static var requiredAccessLevel: PHAccessLevel { .readWrite }

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
