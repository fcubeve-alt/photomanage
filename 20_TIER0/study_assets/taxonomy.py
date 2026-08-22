# -*- coding: utf-8 -*-
"""
CANONICAL LIBRARY TAXONOMY — single source of truth.

Imported by BOTH `generate_test_library.py` (which assigns every asset a leaf path)
and `build_prototype.py` (which builds the browse tree and rolls up real counts from
the manifest). Before this existed the two had drifted: the prototype showed
hand-written counts and fake tiles at the leaves, so a facilitator could not actually
complete a task inside the prototype. One tree, two consumers, no drift.

SCOPE BOUNDARY (DEC-017): this is a NAVIGATIONAL SKELETON — the folder tree a user
browses. It is NOT the Tier 1-A Visual Asset Taxonomy: no classification rules, no
confusion matrix, no risk or lifecycle defaults. Building those now would violate the
Execution Index (DEC-003, P-01).

Structure per Constitution §23: 11 top-level entries, drilling to 2nd and 3rd level
where depth actually helps a user form a spatial memory.
"""

# Nested dict. A node with no children is a leaf that holds assets.
# `_icon` is metadata for the top level only.
TREE = {
    "Documents": {"_icon": "📄", "children": {
        "Identity": {"children": {
            "ID Cards": {}, "Passports": {}, "Driver Licenses": {}, "Visas": {},
        }},
        "Contracts": {"children": {
            "Tenancy": {}, "Employment": {}, "Insurance": {}, "Other": {},
        }},
        "Financial": {"children": {
            "Bank": {}, "Tax": {}, "Statements": {},
        }},
        # Cross-listed: the SAME asset also appears under Purchases. One asset,
        # many entries, no duplicated original (Constitution §3).
        "Receipts": {"_also_in": "Purchases > Receipts"},
        "Warranty": {"_also_in": "Purchases > Warranty"},
        # OPEN-1: awaiting an Owner ruling against §16 (no unrequested health
        # inference). Rendered as "pending decision" and excluded from every task.
        "Medical": {"_pending": True},
        "Other Documents": {},
    }},

    "People": {"_icon": "🧑", "children": {
        "Anna": {}, "Ben": {}, "Chris": {}, "Dana": {}, "Groups": {},
    }},

    "Screenshots": {"_icon": "📱", "children": {
        "Chat": {}, "Shopping": {}, "Maps": {}, "Web": {}, "Work": {},
        "Temporary": {"children": {
            "Verification Codes": {}, "Pickup Codes": {}, "Tickets": {},
        }},
        "Errors": {},
    }},

    "Places": {"_icon": "📍", "children": {
        "United Kingdom": {"children": {"London": {}, "Brighton": {}}},
        "Japan": {"children": {"Tokyo": {}}},
    }},

    "Travel": {"_icon": "✈️", "children": {
        "Tokyo · Apr 2025": {}, "Brighton · Aug 2024": {}, "Lisbon · Sep 2023": {},
    }},

    "Objects": {"_icon": "🚲", "children": {
        "Bicycle": {}, "Appliances": {}, "Devices": {}, "Furniture": {}, "Other": {},
    }},

    "Purchases": {"_icon": "🧾", "children": {
        "Receipts": {"_also_in": "Documents > Receipts"},
        "Orders": {},
        "Warranty": {"_also_in": "Documents > Warranty"},
        "Delivery": {},
    }},

    "Clothing": {"_icon": "👕", "children": {
        "Tops": {}, "Outerwear": {}, "Shoes": {}, "Other": {},
    }},

    "Work": {"_icon": "💼", "children": {
        "Whiteboards": {}, "Meetings": {}, "Documents": {}, "Other": {},
    }},

    "Downloads": {"_icon": "⬇️", "children": {
        "Memes": {}, "Wallpapers": {}, "Social": {},
    }},

    "Timeline": {"_icon": "🗓", "children": {
        "2026": {}, "2025": {}, "2024": {}, "2023": {}, "2022": {},
    }},
}

SEP = " > "


def _walk(node, prefix, out):
    for name, child in node.items():
        if name.startswith("_"):
            continue
        path = prefix + [name]
        kids = child.get("children")
        if kids:
            out.append((path, False))
            _walk(kids, path, out)
        else:
            out.append((path, True))


def all_nodes():
    """[(path_list, is_leaf), ...] in declaration order."""
    out = []
    for top, node in TREE.items():
        path = [top]
        out.append((path, False))
        _walk(node.get("children", {}), path, out)
    return out


def leaf_paths():
    return [SEP.join(p) for p, leaf in all_nodes() if leaf]


def is_valid_leaf(path_str):
    return path_str in set(leaf_paths())


def node_meta(path_list):
    """Return the raw dict for a node, so callers can read _also_in / _pending."""
    node = TREE
    for i, part in enumerate(path_list):
        if i == 0:
            node = node.get(part, {})
        else:
            node = node.get("children", {}).get(part, {})
        if node is None:
            return {}
    return node


if __name__ == "__main__":
    leaves = leaf_paths()
    print(f"top-level entries: {len(TREE)}  (Constitution §23 expects 11)")
    print(f"total nodes: {len(all_nodes())}")
    print(f"leaves: {len(leaves)}")
    depth = max(len(p) for p, _ in all_nodes())
    print(f"max depth: {depth}")
    for p in leaves[:6]:
        print("  ", p)
