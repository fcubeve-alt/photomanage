import Foundation

/// THE PAYWALL BOUNDARY — one place, currently empty.
///
/// There is no price yet, and that is a recorded state rather than an oversight.
/// DEC-026 cancelled T0-C2, the fake-door payment test, so nothing in this project has
/// ever measured what anyone would pay. Picking a number now would be inventing the
/// evidence the cancelled test was supposed to buy.
///
/// What *can* be built without that answer is the boundary itself: a single enumeration
/// of what could be charged for, a single set saying which of those are gated, and one
/// function every feature asks. `paywall` is empty, so today every feature is free and
/// the app behaves exactly as it did before this file existed. When the Owner rules on
/// pricing, the change is this set and the product identifiers below — not a hunt
/// through the UI for `if isPro` scattered across a dozen views.
///
/// The reason to build it now rather than later is the competitor evidence in
/// `COMPETITOR_PRICING_MATRIX.md`: in this category the paywall is normally retrofitted
/// over a finished app, which is how you get the documented pattern of *everything*
/// behind a $7.99/week subscription. A boundary that is drawn before there is a price
/// is a boundary drawn on what the feature costs us, not on what the user can be
/// squeezed for.
enum Feature: String, CaseIterable {
    /// Reading the library and building the catalogue. §23's first value moment.
    case catalogue
    /// The four retrieval paths (§10).
    case search
    /// The visual memory graph (§2 Remember).
    case memory
    /// The maintenance plan — the part that proposes acting on the library (§6).
    case maintenancePlan
    /// Exporting the catalogue's numbers.
    case export
}

enum Commerce {

    /// Features that require a purchase. **Empty until a pricing decision exists.**
    ///
    /// Two of these must never be added to it, whatever the price turns out to be:
    /// `catalogue` and `search` are the promise the permission sheet makes — "reads the
    /// photos already on your phone so they can be catalogued and found again". An app
    /// that asks for the whole photo library and then charges to show you the result
    /// has taken the permission under false pretences.
    static let paywall: Set<Feature> = []

    /// Features that stay free regardless of any future ruling. Asserted in tests so a
    /// later edit to `paywall` cannot quietly swallow them.
    static let alwaysFree: Set<Feature> = [.catalogue, .search]

    /// Product identifiers, in one place. These do not exist in App Store Connect yet —
    /// they cannot, without the developer account — so nothing may assume a purchase
    /// can succeed. `PVM.storekit` defines the same identifiers for local testing.
    enum ProductID {
        static let lifetime = "com.pvm.app.lifetime"
        static let yearly = "com.pvm.app.pro.yearly"
        static let all = [lifetime, yearly]
    }

    static let subscriptionGroupName = "PVM Pro"

    /// True while no product exists to sell. Every purchase surface is hidden in this
    /// state rather than shown and failing — a "Buy" button that cannot work is worse
    /// than no button.
    static var isCommerceConfigured: Bool { !paywall.isEmpty }
}
