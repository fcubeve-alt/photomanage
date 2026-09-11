#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P0-2: no PhotoKit mutation reaches the photo library except through `LibrarySafety`.

**Why a grep is the right tool here.** The property being defended is "this code does
not exist yet". Until a third-party audit pointed it out on 2026-09-11, the statement
"this app never deletes a photo" was true by ABSENCE — nobody had written the code.
That is not a safety property: the day someone finishes `Action.suggestDelete` end to
end, it silently stops holding and not one of the several hundred existing tests fails.

`LibrarySafety.permitWrite` is the runtime gate. This is the check that notices a write
which never went through it — including one added by someone who had not read
`LibrarySafety.swift`, which is the realistic way it would happen.

    python check_no_photo_writes.py            # fail if a mutation API appears
    python check_no_photo_writes.py --selftest # prove the check can still fail
"""

from __future__ import annotations

import argparse
import os
import re
import sys

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOTS = [os.path.join(HERE, "PVM"), os.path.join(HERE, "PVMCore", "Sources")]

#: Every PhotoKit call that can change the user's library.
MUTATION = re.compile(
    r"\b(performChanges|performChangesAndWait|PHAssetChangeRequest|"
    r"PHAssetCreationRequest|PHAssetCollectionChangeRequest|deleteAssets)\b")

#: The one file allowed to name them — it is the gate, and it has to describe what it
#: is gating.
ALLOWED = {"LibrarySafety.swift"}

#: A line that is only a comment is documentation, not a call. The first version of
#: this check flagged its own docstring, which is the right failure for a new guard to
#: have and the wrong one to leave in: a checker that cries wolf gets muted.
COMMENT = re.compile(r"^\s*(//|/\*|\*)")


def offences(roots=None):
    found = []
    for root in roots or ROOTS:
        for base, _, files in os.walk(root):
            for name in files:
                if not name.endswith(".swift") or name in ALLOWED:
                    continue
                path = os.path.join(base, name)
                with open(path, "r", encoding="utf-8") as fh:
                    for number, line in enumerate(fh, 1):
                        if COMMENT.match(line):
                            continue
                        if MUTATION.search(line):
                            rel = os.path.relpath(path, os.path.dirname(HERE))
                            found.append((rel, number, line.strip()))
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true",
                    help="prove the check still reports a mutation when one exists")
    args = ap.parse_args()

    if args.selftest:
        import tempfile
        fails = []
        with tempfile.TemporaryDirectory() as tmp:
            clean = os.path.join(tmp, "Clean.swift")
            with open(clean, "w", encoding="utf-8") as fh:
                fh.write("func read() { _ = PHAsset.fetchAssets(with: nil) }\n")
            if offences([tmp]):
                fails.append("a file with no mutation was reported as one")

            with open(os.path.join(tmp, "Bad.swift"), "w", encoding="utf-8") as fh:
                fh.write("func remove() {\n")
                fh.write("    PHPhotoLibrary.shared().performChanges({ })\n")
                fh.write("}\n")
            if not offences([tmp]):
                fails.append("a real performChanges call was NOT reported")

            with open(os.path.join(tmp, "Doc.swift"), "w", encoding="utf-8") as fh:
                fh.write("// mentions PHAssetChangeRequest in prose only\n")
            only_real = [f for f in offences([tmp]) if "Doc.swift" in f[0]]
            if only_real:
                fails.append("a comment-only mention was reported as a call")

        for f in fails:
            print("FAIL:", f)
        print(f"\nselftest: {len(fails)} failure(s)")
        return 1 if fails else 0

    found = offences()
    for rel, number, line in found:
        print(f"{rel}:{number}: {line}")
    if found:
        print(f"\n{len(found)} PhotoKit mutation(s) outside LibrarySafety.\n")
        print("Every write must go through LibrarySafety.permitWrite, and in this build")
        print("that function refuses. 40_APP/PVM/Ingest/LibrarySafety.swift lists the")
        print("five things that have to be observed on a PHYSICAL DEVICE before the")
        print("mode may change — starting with the one §7's entire tolerance argument")
        print("rests on: that a deletion really does land in Recently Deleted and is")
        print("really restorable for 30 days. That has never been observed here.")
        return 1
    print("no PhotoKit mutation API in the shipping sources")
    return 0


if __name__ == "__main__":
    sys.exit(main())
