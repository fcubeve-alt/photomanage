import Foundation
#if canImport(StoreKit)
import StoreKit
#endif
#if canImport(UIKit)
import UIKit
#endif

/// STOREKIT 2, WIRED BUT NOT SELLING ANYTHING.
///
/// Everything here works against `PVM.storekit`, a local StoreKit configuration file,
/// which is the part worth knowing: **purchases, restores, cancellations and refunds
/// can be exercised in the Simulator with no Apple Developer account and no App Store
/// Connect record.** That is why this could be built before the account exists, and it
/// is also the limit of what has been proven — a local configuration file tests our
/// code, not Apple's servers. Nothing here has run against a real product.
///
/// Three things this deliberately does not do:
///
///  * **No receipt sent to a server.** There is no server. StoreKit 2 verifies the
///    transaction signature on-device (`VerificationResult`), which is Apple's own
///    recommended path and the only one compatible with the privacy claim.
///  * **No user account.** Purchases are tied to the Apple ID that made them; restore
///    is `AppStore.sync()`. Adding an account to a product that stores nothing off the
///    device would mean collecting an email address in order to sell something that
///    does not need one.
///  * **No entitlement cached to disk.** `Transaction.currentEntitlements` is the
///    source of truth on every launch. A cached "isPro = true" file is the standard
///    way an expired subscription keeps working, and the standard way a refund does
///    not take effect.
@MainActor
final class Entitlements: ObservableObject {

    /// `nonisolated` so a SwiftUI view can name it in a property initialiser, which
    /// is not a main-actor context even though the view's `body` is.
    nonisolated static let shared = Entitlements()

    private nonisolated init() {}

    @Published private(set) var owned: Set<String> = []
    @Published private(set) var lastError: String?

    /// The one question the rest of the app asks.
    func isUnlocked(_ feature: Feature) -> Bool {
        guard Commerce.paywall.contains(feature) else { return true }
        return !owned.isEmpty
    }

    #if canImport(StoreKit)
    private var updates: Task<Void, Never>?

    /// Starts listening before anything else, because a transaction can arrive from
    /// outside the app — a family-sharing grant, an Ask-to-Buy approval, a purchase
    /// made on another device — and one that is never finished is re-delivered forever.
    func start() {
        guard updates == nil else { return }
        updates = Task { [weak self] in
            for await update in Transaction.updates {
                guard let transaction = try? Self.verified(update) else { continue }
                await transaction.finish()
                await self?.refresh()
            }
        }
        Task { await refresh() }
    }

    func refresh() async {
        var found: Set<String> = []
        for await entitlement in Transaction.currentEntitlements {
            guard let transaction = try? Self.verified(entitlement) else { continue }
            // A refunded or revoked purchase keeps appearing here with a revocation
            // date set. Treating "present" as "owned" is how refunds silently fail.
            if transaction.revocationDate == nil {
                found.insert(transaction.productID)
            }
        }
        owned = found
    }

    func products() async -> [Product] {
        (try? await Product.products(for: Commerce.ProductID.all)) ?? []
    }

    @discardableResult
    func purchase(_ product: Product) async -> Bool {
        do {
            switch try await product.purchase() {
            case .success(let result):
                let transaction = try Self.verified(result)
                await transaction.finish()
                await refresh()
                return true
            case .userCancelled:
                return false
            case .pending:
                // Ask-to-Buy. Nothing is owed yet and nothing unlocks; the grant will
                // arrive through `Transaction.updates` if a parent approves.
                lastError = nil
                return false
            @unknown default:
                return false
            }
        } catch {
            lastError = error.localizedDescription
            return false
        }
    }

    /// "Restore Purchases". Apple requires this control to exist for any app selling a
    /// non-consumable or a subscription, and it has to be reachable without buying
    /// anything first — which is why it lives in Support rather than behind a paywall.
    func restore() async {
        do { try await AppStore.sync() } catch { lastError = error.localizedDescription }
        await refresh()
    }

    /// Apple's own cancellation sheet. Sending the user to a web page instead is the
    /// documented cause of the complaint in the competitor file — users who deleted
    /// the app believing that cancelled the subscription.
    func showManageSubscriptions() async {
        #if canImport(UIKit)
        guard let scene = Self.scene else { return }
        do { try await AppStore.showManageSubscriptions(in: scene) }
        catch { lastError = error.localizedDescription }
        #endif
    }

    /// In-app refund request, straight to Apple's sheet. The alternative — telling the
    /// user to write to Apple Support — is what the same file records as "refusal of
    /// refunds by both developer and Apple". This costs us nothing to offer and is the
    /// difference between a refund policy and a refund.
    func requestRefund() async {
        #if canImport(UIKit)
        guard let scene = Self.scene else { return }
        for await entitlement in Transaction.currentEntitlements {
            guard let transaction = try? Self.verified(entitlement) else { continue }
            _ = try? await transaction.beginRefundRequest(in: scene)
            break
        }
        await refresh()
        #endif
    }

    /// StoreKit 2 signs every transaction. An unverified one is not a purchase, and
    /// the failure mode of ignoring this is the jailbreak receipt-forging that the
    /// old receipt-validation APIs were routinely defeated by.
    private static func verified<T>(_ result: VerificationResult<T>) throws -> T {
        switch result {
        case .verified(let value): return value
        case .unverified(_, let error): throw error
        }
    }

    #if canImport(UIKit)
    private static var scene: UIWindowScene? {
        UIApplication.shared.connectedScenes.first as? UIWindowScene
    }
    #endif

    #else
    func start() {}
    func refresh() async {}
    func restore() async {}
    func showManageSubscriptions() async {}
    func requestRefund() async {}
    #endif
}
