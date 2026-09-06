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
        guard parts.count >= 2, parts.count <= maxDepth else { return nil }
        if parts.count == 3 {
            guard ensure(parts[0...1].joined(separator: Taxonomy.separator)) != nil else { return nil }
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
