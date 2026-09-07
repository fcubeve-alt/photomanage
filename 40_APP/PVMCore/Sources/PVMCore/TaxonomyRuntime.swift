import Foundation

/// The parts of the taxonomy that depend on the user's own library.
///
/// `Taxonomy.generated.swift` carries the tree the product ships with.
/// `People > Anna` is not a category we shipped — it is a face cluster the user named.
/// Same for a country nobody predicted, a year that had not happened yet, and a trip
/// label minted from a run of days abroad. Those branches grow at runtime, under the
/// roots the tree declares extensible, and nowhere else: a rule that invents
/// `Documents > Crypto` is a bug, and this is where it is caught rather than
/// discovered in the browse UI.
public final class TaxonomyRuntime {

    private static let lock = NSLock()
    private static var minted: Set<String> = []
    /// How deep each extensible root may grow, taken from what §3 actually names
    /// rather than from one number for all of them.
    ///
    ///   Time：Year → Month → Day → Moment          — four levels, so depth 5
    ///   GPS：Country → City → Place                — three, so depth 4
    ///
    /// A single cap of 3 was not a safety property, it was an accident: it silently
    /// made §3's fourth level of time impossible to build. The cap still stops a rule
    /// inventing an eighth level of anything; it is now calibrated to the tree the
    /// Constitution describes.
    private static let maxDepthByRoot = ["Timeline": 5, "Places": 4]
    private static let maxDepth = 3

    public static func isKnown(_ path: String) -> Bool {
        if Taxonomy.allNodes.contains(path) { return true }
        lock.lock(); defer { lock.unlock() }
        return minted.contains(path)
    }

    /// Register a data-derived node. Returns nil when the path is not something the
    /// tree allows to grow.
    @discardableResult
    public static func ensure(_ path: String) -> String? {
        if isKnown(path) { return path }
        let parts = path.components(separatedBy: Taxonomy.separator)
        guard let root = parts.first, Taxonomy.extensibleRoots.contains(root) else { return nil }
        guard parts.count >= 2, parts.count <= (maxDepthByRoot[root] ?? maxDepth)
        else { return nil }
        // Every ancestor is registered too, so a browse view can render the path it
        // was given without discovering a gap halfway down it.
        for depth in 2..<parts.count {
            guard ensure(parts[0..<depth].joined(separator: Taxonomy.separator)) != nil
            else { return nil }
        }
        lock.lock(); minted.insert(path); lock.unlock()
        return path
    }

    public static func mintedNodes() -> [String] {
        lock.lock(); defer { lock.unlock() }
        return minted.sorted()
    }

    public static func resetMinted() {
        lock.lock(); minted.removeAll(); lock.unlock()
    }

    // MARK: - path arithmetic

    public static func root(of path: String) -> String {
        path.components(separatedBy: Taxonomy.separator).first ?? path
    }

    public static func depth(_ path: String) -> Int {
        path.components(separatedBy: Taxonomy.separator).count
    }

    public static func ancestors(of path: String) -> [String] {
        let parts = path.components(separatedBy: Taxonomy.separator)
        guard parts.count > 1 else { return [] }
        return (1..<parts.count).map { parts[0..<$0].joined(separator: Taxonomy.separator) }
    }

    public static func isLeaf(_ path: String) -> Bool { Taxonomy.leaves.contains(path) }

    public static func crossListing(of path: String) -> String? { Taxonomy.crossListing[path] }

    public static func children(of path: String) -> [String] {
        let prefix = path + Taxonomy.separator
        let want = depth(path) + 1
        var out = Set<String>()
        for p in Taxonomy.allNodes where p.hasPrefix(prefix) && depth(p) == want { out.insert(p) }
        for p in mintedNodes() where p.hasPrefix(prefix) && depth(p) == want { out.insert(p) }
        return out.sorted()
    }
}
