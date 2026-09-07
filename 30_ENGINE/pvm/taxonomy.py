# -*- coding: utf-8 -*-
"""
Taxonomy bridge — the engine classifies INTO the tree that already exists.

`20_TIER0/study_assets/taxonomy.py` is the canonical tree and stays canonical. It is
loaded from its real path rather than copied, so the engine and the browse prototype
can never drift apart: an invalid path fails here at classification time instead of
producing a catalogue entry that points at a folder nobody can open.

DEC-017 scoped that file as a NAVIGATIONAL SKELETON with deliberately no
classification rules attached. This module is where the rules attach to it, from the
outside, without editing it.
"""

from __future__ import annotations

import importlib.util
import os
from typing import Dict, List, Optional, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
_CANONICAL = os.path.normpath(os.path.join(_HERE, "..", "..", "20_TIER0", "study_assets", "taxonomy.py"))


def _load_canonical():
    if not os.path.exists(_CANONICAL):
        raise FileNotFoundError(
            f"canonical taxonomy not found at {_CANONICAL}. The engine deliberately "
            "does not carry its own copy — one tree, many consumers, no drift."
        )
    spec = importlib.util.spec_from_file_location("_pvm_canonical_taxonomy", _CANONICAL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_canon = _load_canonical()

TREE = _canon.TREE
SEP = _canon.SEP
ROOTS: Tuple[str, ...] = tuple(TREE.keys())
ALL_PATHS: Tuple[str, ...] = tuple(SEP.join(p) for p, _ in _canon.all_nodes())
LEAF_PATHS: Tuple[str, ...] = tuple(_canon.leaf_paths())

_ALL = set(ALL_PATHS)
_LEAVES = set(LEAF_PATHS)

# Some branches are grown from the user's own library rather than authored in
# advance. `People > Anna` is not a category we shipped; it is a face cluster the user
# named. Same for a country nobody predicted, a year that had not happened yet, and a
# trip label minted from a run of days abroad. The canonical tree lists examples of
# these; the engine may mint siblings for them and may NOT mint anything anywhere
# else — a rule that invents `Documents > Crypto` is a bug, and this is where it is
# caught rather than discovered in the browse UI.
EXTENSIBLE_ROOTS = frozenset({"People", "Places", "Travel", "Timeline"})

# How deep each extensible root may grow, taken from what §3 actually names rather than
# from one number for all of them.
#
#   Time：Year → Month → Day → Moment          — four levels, so depth 5 with the root
#   GPS：Country → City → Place                — three, so depth 4
#
# A single cap of 3 was not a safety property, it was an accident: it silently made
# §3's fourth level of time impossible to build, and the first attempt at Month/Day
# died on it. The cap still exists, and still stops a rule inventing an eighth level of
# anything — it is now just calibrated to the tree the Constitution describes.
_MAX_DEPTH_BY_ROOT = {"Timeline": 5, "Places": 4}
_MAX_DEPTH = 3

# Some branches are extensible where their root is not, and `Documents` is the case
# that forced the distinction. §10's first retrieval path is spelled out as
#
#     Browse：用户知道类别，直接 Documents → IDs → Person → ID Card
#
# — a person level *inside* Documents, between the category and the document type.
# Adding `Documents` to `EXTENSIBLE_ROOTS` would have bought that at the cost of the
# guard: the whole point of that frozenset is that a rule inventing `Documents > Crypto`
# is a bug caught here rather than discovered in the browse UI, and opening the root
# would have made every such invention legal.
#
# So extensibility is per branch as well as per root. Only the named branch may grow,
# only to the named depth, and `Documents > Crypto` still raises.
_EXTENSIBLE_BRANCHES = {"Documents > Identity": 4}
_MINTED: set = set()


def max_depth(root: str) -> int:
    return _MAX_DEPTH_BY_ROOT.get(root, _MAX_DEPTH)


def extensible_branch(path: str):
    """The branch prefix that permits this path, and the depth it allows — or None.

    Longest prefix wins, so a future narrower branch inside a wider one behaves the
    way every other prefix rule in this engine does.
    """
    best = None
    for prefix, limit in _EXTENSIBLE_BRANCHES.items():
        if path == prefix or path.startswith(prefix + SEP):
            if best is None or len(prefix) > len(best[0]):
                best = (prefix, limit)
    return best


def ensure_node(path: str) -> str:
    """Register a data-derived node, or raise. Returns the path for chaining."""
    if path in _ALL or path in _MINTED:
        return path
    parts = path.split(SEP)
    branch = extensible_branch(path)
    if parts[0] in EXTENSIBLE_ROOTS:
        limit = max_depth(parts[0])
        floor = 2
        where = parts[0]
    elif branch is not None:
        prefix, limit = branch
        # A branch may only grow BELOW itself. `Documents > Identity` is canonical and
        # nothing is being minted at that depth; the person level is the one after it.
        floor = len(prefix.split(SEP)) + 1
        where = prefix
    else:
        raise InvalidPath(
            f"{path!r} does not exist and {parts[0]!r} is not an extensible root. "
            "A classification rule may not invent a category."
        )
    if not floor <= len(parts) <= limit:
        raise InvalidPath(
            f"{path!r} is at depth {len(parts)}; {where} allows {floor}..{limit}")
    # Every ancestor is registered too, so a browse view can render the path it was
    # given without discovering a gap halfway down it.
    for depth in range(2, len(parts)):
        ensure_node(SEP.join(parts[:depth]))
    _MINTED.add(path)
    return path


def minted_nodes():
    """Everything the engine grew from this library, for the catalogue to render."""
    return sorted(_MINTED)


def reset_minted():
    _MINTED.clear()


class InvalidPath(ValueError):
    pass


def is_node(path: str) -> bool:
    return path in _ALL


def is_leaf(path: str) -> bool:
    return path in _LEAVES


def require_node(path: str) -> str:
    """Assignments are validated, not trusted. A typo in a rule would otherwise
    produce a confident catalogue entry pointing at a folder that does not exist."""
    if path not in _ALL and path not in _MINTED:
        raise InvalidPath(
            f"{path!r} is not a node in the canonical taxonomy and was not minted "
            "under an extensible root"
        )
    return path


def root_of(path: str) -> str:
    return path.split(SEP, 1)[0]


def depth(path: str) -> int:
    return len(path.split(SEP))


def parent(path: str) -> Optional[str]:
    parts = path.split(SEP)
    return SEP.join(parts[:-1]) if len(parts) > 1 else None


def ancestors(path: str) -> List[str]:
    parts = path.split(SEP)
    return [SEP.join(parts[: i + 1]) for i in range(len(parts) - 1)]


def children_of(path: str) -> List[str]:
    prefix = path + SEP
    n = depth(path) + 1
    known = [p for p in ALL_PATHS if p.startswith(prefix) and depth(p) == n]
    grown = [p for p in _MINTED if p.startswith(prefix) and depth(p) == n]
    return sorted(set(known + grown))


def cross_listing(path: str) -> Optional[str]:
    """`_also_in` in the canonical tree: the SAME asset appears under two entries,
    with one original and no copy (Constitution §3). Receipts and Warranty are the
    two the tree declares."""
    meta = _canon.node_meta(path.split(SEP))
    also = meta.get("_also_in") if isinstance(meta, dict) else None
    return also if also in _ALL else None
