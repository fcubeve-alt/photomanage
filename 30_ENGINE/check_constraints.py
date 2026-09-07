#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verify CONSTRAINTS.md against the source documents and against the code.

The failure this exists to prevent (PF-12): building the product's core engine without
reading the documents that specify it, and then presenting the specification's own
requirements as discoveries. An instruction to "read the docs" does not prevent that.
A build that fails does.

Three checks, and each one blocks a different way of drifting:

1. **The quote is really in the source.** Every clause cites a source document and
   quotes it verbatim. Whitespace is normalised, nothing else is. You cannot soften a
   constraint by paraphrasing it into this file — the paraphrase will not be found.
2. **DONE means something executable exists.** A clause marked DONE must name a file,
   and where it names `path::symbol` that symbol must exist. "Implemented" backed by an
   intention fails here.
3. **MISSING and PARTIAL must say what is absent.** A gap with no explanation is
   indistinguishable from a gap nobody noticed, which is the whole problem.

    python check_constraints.py
    python check_constraints.py --selftest
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
REPO = os.path.normpath(os.path.join(HERE, ".."))
EXTRACTED = os.path.join(REPO, "10_SOURCE_DOCS", "_extracted_text")

SOURCES = {
    "L1": "L1_PRODUCT_CONSTITUTION_v1.3.txt",
    "L1B": "L1B_INFORMATION_CHANGE_FIRST_METHODOLOGY_v1.0.txt",
    "L0": "L0_LAUNCH_INSTRUCTION_v1.0.txt",
    "L3": "L3_ENGINEERING_PLAYBOOK_v1.1.txt",
    "T0": "L2_TIER0_v1.1.txt",
    "T1": "L2_TIER1_v1.1.txt",
    "T2": "L2_TIER2_v1.1.txt",
}
# NOT-CODE is for a clause that genuinely shapes decisions but has no single
# implementation to point at — a philosophy or a positioning statement. It still needs
# an explanation, so it cannot be used as a place to hide work that was skipped.
VALID_STATUS = {"DONE", "PARTIAL", "MISSING", "OUT-OF-SCOPE", "NOT-CODE"}
SOURCE_RE = re.compile(r"^(L0|L1B|L1|L3|T0|T1|T2):(\d+)$")


def squash(text: str) -> str:
    """Normalise whitespace only. Everything else must match exactly, because the
    point of a verbatim quote is that it cannot be softened."""
    return re.sub(r"\s+", "", text)


def parse_rows(path: str):
    """Read every markdown table row that has an id in the first column."""
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line.startswith("|") or line.startswith("|---") or line.startswith("|--:"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 3 or cells[0] in ("id", ""):
                continue
            if not re.match(r"^[A-Z][A-Z0-9]*-[A-Z0-9-]+$|^[A-Z]\d+-L\d+$", cells[0]):
                continue
            rows.append({"lineno": lineno, "cells": cells})
    return rows


def load_source(key: str) -> str:
    path = os.path.join(EXTRACTED, SOURCES[key])
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def check(constraints_path: str, root: str, verbose: bool = True):
    failures, checked = [], 0
    tally = {s: 0 for s in VALID_STATUS}
    rows = parse_rows(constraints_path)
    if not rows:
        return ["CONSTRAINTS.md contains no constraint rows — the register is empty"], 0

    cache = {}
    for row in rows:
        cells, cid, ln = row["cells"], row["cells"][0], row["lineno"]

        # Two table shapes: with a verbatim quote (id | quote | source | status | ev)
        # and without (id | layer | status | ev). Both must carry a status.
        status = next((c for c in cells if c in VALID_STATUS), None)
        if status is None:
            failures.append(f"{cid} (line {ln}): no valid status among {VALID_STATUS}")
            continue
        checked += 1
        tally[status] = tally.get(status, 0) + 1

        # ---- 1. the quote must really be in the source --------------------
        source_cell = next((c for c in cells if SOURCE_RE.match(c)), None)
        if source_cell:
            key, cited_line = SOURCE_RE.match(source_cell).groups()
            quote = cells[1]
            if key not in cache:
                cache[key] = load_source(key)
            body = cache[key]
            if squash(quote) not in squash(body):
                failures.append(
                    f"{cid} (line {ln}): the quoted clause is NOT in {SOURCES[key]}. "
                    "A constraint cannot be paraphrased into something easier to satisfy.\n"
                    f"    quoted: {quote[:90]}")
            else:
                lines = body.splitlines()
                actual = next((i for i, l in enumerate(lines, 1)
                               if squash(quote)[:40] in squash(l)), None)
                if actual and abs(actual - int(cited_line)) > 2:
                    failures.append(
                        f"{cid} (line {ln}): cited as {key}:{cited_line} but found at "
                        f"{key}:{actual} — fix the citation")

        evidence = cells[-1]

        # ---- 2. DONE must name something that exists -----------------------
        if status == "DONE":
            refs = re.findall(r"`([^`]+)`", evidence)
            if not refs:
                failures.append(
                    f"{cid} (line {ln}): marked DONE with no file or test named. "
                    "DONE backed by an intention is what this check exists to stop.")
            for ref in refs:
                path_part, _, symbol = ref.partition("::")
                full = os.path.join(root, path_part)
                if not os.path.exists(full) and not os.path.exists(os.path.join(REPO, path_part)):
                    failures.append(f"{cid} (line {ln}): DONE cites `{ref}` which does not exist")
                    continue
                if symbol:
                    target = full if os.path.exists(full) else os.path.join(REPO, path_part)
                    with open(target, "r", encoding="utf-8") as fh:
                        body = fh.read()
                    # A module-level constant is legitimate evidence — MEDICAL_IS_
                    # DOCUMENT_ONLY and REVIEW_FLOOR are load-bearing policy, not
                    # decoration — so an assignment counts as a definition.
                    defined = re.search(rf"^\s*(def|class)\s+{re.escape(symbol)}\b", body, re.M) \
                        or re.search(rf"^{re.escape(symbol)}\s*[:=]", body, re.M)
                    if not defined:
                        failures.append(
                            f"{cid} (line {ln}): DONE cites `{ref}` but {symbol} is not "
                            f"defined in {path_part}")

        # ---- 3. a gap must say what is absent ------------------------------
        if status in ("PARTIAL", "MISSING", "NOT-CODE", "OUT-OF-SCOPE") and len(evidence) < 20:
            failures.append(
                f"{cid} (line {ln}): {status} with no explanation. An unexplained gap "
                "is indistinguishable from one nobody noticed, and an unexplained "
                "out-of-scope is where skipped work hides.")

    # ---- 4. the rollup table must be the tally, not a memory of it ---------
    #
    # The summary at the foot of CONSTRAINTS.md said "counted by
    # `check_constraints.py`, not by hand" and was neither: it was typed once and then
    # drifted, reporting eleven MISSING when there were five. Its own numbered list
    # skipped item 4. This is the same failure this repository keeps finding — the
    # thing that reports is never exercised by the thing it reports on — so the claim
    # is now enforced rather than made.
    failures.extend(_check_rollup(constraints_path, tally, checked))

    if verbose:
        for f in failures:
            print("FAIL:", f)
        print(f"\n{checked} constraints checked · {len(failures)} failure(s)")
    return failures, checked


ROLLUP_HEADER = "| status | count | share |"


def _check_rollup(constraints_path: str, tally, checked: int):
    """Compare the register's own summary table against what was actually counted."""
    with open(constraints_path, "r", encoding="utf-8") as fh:
        text = fh.read()
    if ROLLUP_HEADER not in text:
        # A register with no rollup is fine; one that has a wrong rollup is not.
        return []

    failures = []
    total_claim = re.search(r"\*\*(\d+) clauses audited", text)
    if total_claim and int(total_claim.group(1)) != checked:
        failures.append(
            f"the rollup says {total_claim.group(1)} clauses audited; {checked} rows "
            "were actually counted")

    rows = re.findall(r"^\| (DONE|PARTIAL|MISSING|OUT-OF-SCOPE[^|]*|NOT-CODE[^|]*) "
                      r"\| (\d+) \| +(\d+)% \|$", text, re.M)
    if not rows:
        failures.append("the rollup table is present but no status row could be parsed")
        return failures
    seen = set()
    for label, count, share in rows:
        status = label.split(" (")[0].strip()
        seen.add(status)
        actual = tally.get(status, 0)
        if int(count) != actual:
            failures.append(
                f"the rollup says {status} = {count}; {actual} rows carry that status")
        want_share = round(actual / checked * 100) if checked else 0
        if abs(int(share) - want_share) > 1:
            failures.append(
                f"the rollup says {status} is {share}%; {actual} of {checked} is "
                f"{want_share}%")
    for status, actual in sorted(tally.items()):
        if actual and status not in seen:
            failures.append(
                f"{actual} rows carry status {status} and the rollup does not list it")
    return failures


def selftest() -> int:
    """Prove the checker catches each thing it claims to catch, using a temporary
    register whose answers are known by construction."""
    import tempfile
    fails = []

    good = """
| id | verbatim clause | source | status | evidence |
|---|---|---|---|---|
| B4-NOFRAMES | 禁止默认采用：Video → 每隔 N 帧抽图 → 每一帧跑完整视觉模型 | L1B:37 | DONE | `check_constraints.py` |
"""
    paraphrased = good.replace(
        "禁止默认采用：Video → 每隔 N 帧抽图 → 每一帧跑完整视觉模型",
        "视频最好不要每帧都跑模型")
    no_evidence = good.replace("`check_constraints.py`", "yes it is done")
    bad_symbol = good.replace("`check_constraints.py`", "`check_constraints.py::no_such_function`")
    silent_gap = good.replace("DONE | `check_constraints.py`", "MISSING | todo")

    # The rollup check, exercised on a register whose true tally is one DONE. Without
    # these three cases the check would only ever run against a register that already
    # agrees with itself, which is no test at all.
    rollup = """

**1 clauses audited — counted by `check_constraints.py`:**

| status | count | share |
|---|--:|--:|
| DONE | 1 | 100% |
"""
    right_rollup = good + rollup
    wrong_count = good + rollup.replace("| DONE | 1 | 100% |", "| DONE | 7 | 100% |")
    wrong_share = good + rollup.replace("| DONE | 1 | 100% |", "| DONE | 1 | 40% |")
    wrong_total = good + rollup.replace("**1 clauses audited", "**90 clauses audited")

    cases = [("a correct row passes", good, 0),
             ("a paraphrased quote is caught", paraphrased, 1),
             ("DONE with no file named is caught", no_evidence, 1),
             ("DONE citing a missing symbol is caught", bad_symbol, 1),
             ("an unexplained gap is caught", silent_gap, 1),
             ("a rollup that matches the rows passes", right_rollup, 0),
             ("a rollup with the wrong count is caught", wrong_count, 1),
             ("a rollup with the wrong share is caught", wrong_share, 1),
             ("a rollup with the wrong total is caught", wrong_total, 1)]

    for name, body, expect in cases:
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False,
                                         encoding="utf-8") as fh:
            fh.write(body)
            tmp = fh.name
        try:
            found, checked = check(tmp, HERE, verbose=False)
            if checked != 1:
                fails.append(f"{name}: expected 1 constraint parsed, got {checked}")
            if (len(found) > 0) != bool(expect):
                fails.append(f"{name}: expected {'a failure' if expect else 'no failure'}, "
                             f"got {found}")
        finally:
            os.unlink(tmp)

    for f in fails:
        print("FAIL:", f)
    print(f"\nselftest: {len(fails)} failure(s)")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--constraints", default=os.path.join(HERE, "CONSTRAINTS.md"))
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    failures, _ = check(args.constraints, HERE)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
