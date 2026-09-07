#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate the Swift side of everything that must not drift from the Python engine.

The engine in `30_ENGINE` is the reference implementation: its rules are argued about,
tested against 10,000 labelled assets, and audited clause by clause against L1. The app
is what ships. If those two are maintained by hand they diverge, and the divergence is
silent — the app files a passport somewhere the engine would not, and every measurement
taken on the engine stops describing the product.

So the taxonomy, the text rules, the scene map and the risk mapping are GENERATED here
from the Python source. `tools-check.yml` regenerates and fails on any diff, the same
guard this repo already uses for the prototype and the landing pages.

    python generate_shared.py            # write the Swift files
    python generate_shared.py --check    # exit 1 if they would change
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import sys
import tempfile

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, ".."))
ENGINE = os.path.join(REPO, "30_ENGINE")
OUT = os.path.join(HERE, "PVMCore", "Sources", "PVMCore")
RESOURCES = os.path.join(HERE, "PVMCore", "Tests", "PVMCoreTests", "Resources")

sys.path.insert(0, ENGINE)
from pvm import fixture as F                   # noqa: E402
from pvm import intent as I
from pvm import rules as R                     # noqa: E402
from pvm import taxonomy as T                  # noqa: E402
from pvm.risk import RISK_BY_PATH_PREFIX       # noqa: E402
from pvm.classifier import SETTLE_AT           # noqa: E402
from pvm.verdict import MAX_CONFIDENCE, REVIEW_FLOOR   # noqa: E402
from pvm.catalog import Catalog                # noqa: E402
from pvm import importance as IMP              # noqa: E402
from pvm import pipeline as P                  # noqa: E402
from pvm import taxonomy as TX                 # noqa: E402

BANNER = """// GENERATED — do not edit.
// Source: 30_ENGINE/pvm/{sources}
// Regenerate: python 40_APP/generate_shared.py
//
// The engine is the reference implementation and the app is what ships. Maintained by
// hand these two diverge silently: the app files a passport somewhere the engine would
// not, and every number measured on the engine stops describing the product. CI
// regenerates this and fails on any diff.
"""


def swift_string(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def gen_taxonomy() -> str:
    lines = [BANNER.format(sources="taxonomy.py"), "import Foundation", "",
             "public enum Taxonomy {", '    public static let separator = " > "', ""]
    lines.append("    public static let roots: [String] = [")
    for r in T.ROOTS:
        lines.append(f"        {swift_string(r)},")
    lines.append("    ]\n")

    lines.append("    /// Every node the tree ships with. A rule may not name anything else.")
    lines.append("    public static let allNodes: Set<String> = [")
    for p in T.ALL_PATHS:
        lines.append(f"        {swift_string(p)},")
    lines.append("    ]\n")

    lines.append("    public static let leaves: Set<String> = [")
    for p in T.LEAF_PATHS:
        lines.append(f"        {swift_string(p)},")
    lines.append("    ]\n")

    lines.append("    /// Branches grown from the user's own library — a named face, a")
    lines.append("    /// country nobody predicted, a year that had not happened yet.")
    lines.append("    public static let extensibleRoots: Set<String> = [")
    for r in sorted(T.EXTENSIBLE_ROOTS):
        lines.append(f"        {swift_string(r)},")
    lines.append("    ]\n")

    lines.append("    /// Branches that may grow where their root may not, with the")
    lines.append("    /// depth each allows. §10's Documents → IDs → Person → ID Card is")
    lines.append("    /// why this exists — see `taxonomy.py`.")
    lines.append("    public static let extensibleBranches: [String: Int] = [")
    for prefix, limit in sorted(T._EXTENSIBLE_BRANCHES.items()):
        lines.append(f"        {swift_string(prefix)}: {limit},")
    lines.append("    ]\n")

    lines.append("    /// `_also_in`: the same asset under two entries, one original (§3).")
    lines.append("    public static let crossListing: [String: String] = [")
    for p in T.ALL_PATHS:
        also = T.cross_listing(p)
        if also:
            lines.append(f"        {swift_string(p)}: {swift_string(also)},")
    lines.append("    ]")
    lines.append("}")
    return "\n".join(lines) + "\n"


def gen_rules() -> str:
    lines = [BANNER.format(sources="rules.py, risk.py, classifier.py, verdict.py"),
             "import Foundation", "",
             "public struct TextRule {",
             "    public let pattern: String",
             "    public let path: String",
             "    public let weight: Double",
             "    public let reason: String",
             "    /// Fires only when the asset already sits under this root, if set.",
             "    public let requiresRoot: String?",
             "}", "",
             "public enum Rules {", ""]

    for name, group in [("documentRules", R.DOCUMENT_RULES),
                        ("purchaseRules", R.PURCHASE_RULES),
                        ("screenshotRules", R.SCREENSHOT_RULES),
                        ("workTextRules", R.WORK_TEXT_RULES)]:
        lines.append(f"    public static let {name}: [TextRule] = [")
        for rule in group:
            root = swift_string(rule.requires_root) if rule.requires_root else "nil"
            lines.append(f"        TextRule(pattern: {swift_string(rule.pattern.pattern)}, "
                         f"path: {swift_string(rule.path)}, weight: {rule.weight}, "
                         f"reason: {swift_string(rule.reason)}, requiresRoot: {root}),")
        lines.append("    ]\n")

    lines.append("    public static let sceneMap: [String: String] = [")
    for k in sorted(R.SCENE_MAP):
        lines.append(f"        {swift_string(k)}: {swift_string(R.SCENE_MAP[k])},")
    lines.append("    ]\n")
    lines.append(f"    public static let sceneFloor: Double = {R.SCENE_FLOOR}")
    lines.append("")
    lines.append("    // §10 Intent Search vocabulary. Generated for the same reason the")
    lines.append("    // scene map is: a search that recognises 身份证 on one side and not")
    lines.append("    // the other is two products, and nobody would notice until a user")
    lines.append("    // typed it into the wrong one.")
    lines.append("    public static let categoryWords: [String: String] = [")
    for k in sorted(I.CATEGORY_WORDS):
        lines.append(f"        {swift_string(k)}: {swift_string(I.CATEGORY_WORDS[k])},")
    lines.append("    ]\n")
    lines.append("    public static let multiSideWords: [String] = [")
    for w in sorted(I.MULTI_SIDE_WORDS, key=lambda x: (-len(x), x)):
        lines.append(f"        {swift_string(w)},")
    lines.append("    ]\n")
    lines.append("    public static let mediaWords: [String: String] = [")
    for k in sorted(I.MEDIA_WORDS):
        lines.append(f"        {swift_string(k)}: {swift_string(I.MEDIA_WORDS[k])},")
    lines.append("    ]\n")
    lines.append("    public static let searchFiller: [String] = [")
    for w in sorted(I._FILLER):
        lines.append(f"        {swift_string(w)},")
    lines.append("    ]\n")
    lines.append("    /// Stripped as substrings, longest first: Chinese is not space-separated.")
    lines.append("    public static let searchFillerCJK: [String] = [")
    for w in I._FILLER_CJK:
        lines.append(f"        {swift_string(w)},")
    lines.append("    ]\n")
    lines.append("")
    lines.append("    /// §6 category → risk, in order: the first prefix that matches wins,")
    lines.append("    /// and the highest match across all of an asset's paths is taken.")
    lines.append("    public static let riskByPathPrefix: [(String, Int)] = [")
    for prefix, risk in RISK_BY_PATH_PREFIX:
        lines.append(f"        ({swift_string(prefix)}, {int(risk)}),")
    lines.append("    ]\n")
    lines.append(f"    public static let reviewFloor: Double = {REVIEW_FLOOR}")
    lines.append(f"    public static let maxConfidence: Double = {MAX_CONFIDENCE}")
    lines.append(f"    public static let settleAt: Double = {SETTLE_AT}")
    lines.append("}")
    return "\n".join(lines) + "\n"


def gen_fixture() -> str:
    """The shared library, as data both implementations read."""
    return json.dumps(F.to_json(), indent=1, ensure_ascii=False, sort_keys=True) + "\n"


def gen_expected() -> str:
    """What the reference implementation makes of that library.

    This is the conformance contract. Both sides having tests does not prove they
    agree, and disagreement is the failure that matters: the app files a passport
    somewhere the engine would not, both suites stay green, and every number measured
    on the engine stops describing the product. The Swift test replays this and
    compares; whichever side moved is the one that fails.

    Only the decisions are recorded — paths, risk, importance, §4 class, action — not
    confidences, which are floating point and would turn a real conformance check into a
    flaky one.

    Importance is in here for the same reason risk is: §5 makes it a factor in the
    action, §18 weights every error by it, and two implementations could agree on every
    path and every action while disagreeing about what a photograph is worth. That
    disagreement would be invisible in both test suites and visible only in a KPI
    nobody could reproduce.
    """
    TX.reset_minted()
    assets = F.build()
    tmp = tempfile.mkdtemp()
    catalog = Catalog(os.path.join(tmp, "conformance.sqlite"))
    try:
        P.run(assets, catalog, reconcile_deletions=False)
        rows = {}
        for asset_id, path in catalog.db.execute(
                "SELECT asset_id, path FROM assignments ORDER BY asset_id, path"):
            rows.setdefault(asset_id, {"paths": [], "risk": None, "importance": None,
                                       "asset_class": None, "action": None})
            rows[asset_id]["paths"].append(path)
        for asset_id, risk, imp, cls in catalog.db.execute(
                "SELECT asset_id, risk, importance, asset_class FROM assets"):
            if asset_id in rows:
                rows[asset_id]["risk"] = risk
                rows[asset_id]["importance"] = imp
                rows[asset_id]["asset_class"] = cls
        for asset_id, action in catalog.db.execute("SELECT asset_id, action FROM proposals"):
            if asset_id in rows:
                rows[asset_id]["action"] = action
    finally:
        catalog.close()
        shutil.rmtree(tmp, ignore_errors=True)
    return json.dumps(rows, indent=1, ensure_ascii=False, sort_keys=True) + "\n"




def gen_importance() -> str:
    """§4's thirteen 大类 and the constants `assess` reads.

    Generated for the same reason the scene map is: a §4 table maintained by hand on
    two sides is two products. The difference would show up as an app that prices a
    family photograph differently from the engine that was measured — and §18 weights
    every error by exactly that number, so the divergence would be invisible in both
    test suites and visible only in the KPI nobody could reproduce.
    """
    lines = [BANNER.format(sources="importance.py, risk.py"), "import Foundation", "",
             "/// One of §4's 大类. `prefixes` is empty for the two classes that are not",
             "/// branches of the navigational tree — see `Importance.swift`.",
             "public struct AssetClass: Equatable {",
             "    public let key: String",
             "    public let name: String",
             "    public let examples: String",
             "    public let defaultRiskLow: Int",
             "    public let defaultRiskHigh: Int",
             "    public let baselineImportance: Importance",
             "    public let prefixes: [String]",
             "}", "",
             "public enum AssetClasses {", ""]

    def emit(name: str, cls) -> None:
        lo, hi = cls.default_risk
        prefixes = ", ".join(swift_string(p) for p in cls.prefixes)
        lines.append(f"    public static let {name} = AssetClass(")
        lines.append(f"        key: {swift_string(cls.key)},")
        lines.append(f"        name: {swift_string(cls.name)},")
        lines.append(f"        examples: {swift_string(cls.examples)},")
        lines.append(f"        defaultRiskLow: {int(lo)}, defaultRiskHigh: {int(hi)},")
        lines.append(f"        baselineImportance: .{_imp_case(cls.baseline_importance)},")
        lines.append(f"        prefixes: [{prefixes}])")
        lines.append("")

    for cls in IMP.ASSET_CLASSES:
        emit(_swift_ident(cls.key), cls)
    emit("undescribed", IMP.UNDESCRIBED)

    lines.append("    /// §4's table, in §4's order. Scanned in order, longest prefix wins.")
    lines.append("    public static let all: [AssetClass] = [")
    for cls in IMP.ASSET_CLASSES:
        lines.append(f"        {_swift_ident(cls.key)},")
    lines.append("    ]\n")
    lines.append(f"    /// How many other assets a named person must appear in before they")
    lines.append(f"    /// read as somebody in this user's life rather than a passer-by.")
    lines.append(f"    public static let recurringPerson = {IMP.RECURRING_PERSON}")
    lines.append(f"    /// Where a considered set of shots becomes a held shutter.")
    lines.append(f"    public static let burstSize = {IMP.BURST_SIZE}")
    lines.append("}")
    return "\n".join(lines) + "\n"


def _swift_ident(key: str) -> str:
    head, *rest = key.split("_")
    return head + "".join(w.capitalize() for w in rest)


def _imp_case(level) -> str:
    return _swift_ident(level.name.lower())


FILES = {"Taxonomy.generated.swift": gen_taxonomy, "Rules.generated.swift": gen_rules,
         "Importance.generated.swift": gen_importance}
RESOURCE_FILES = {"fixture.json": gen_fixture, "expected.json": gen_expected}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if the generated files would change")
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    os.makedirs(RESOURCES, exist_ok=True)
    stale = []
    targets = [(OUT, FILES), (RESOURCES, RESOURCE_FILES)]
    for directory, group in targets:
      for name, fn in group.items():
        path = os.path.join(directory, name)
        new = fn()
        old = None
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as fh:
                old = fh.read()
        if args.check:
            if old != new:
                stale.append(name)
            continue
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(new)
        print(f"wrote {name}  ({len(new.splitlines())} lines)")

    if args.check:
        for name in stale:
            print(f"STALE: {name} — the Swift copy no longer matches the Python source")
        print(f"\n{len(stale)} stale file(s)")
        return 1 if stale else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
