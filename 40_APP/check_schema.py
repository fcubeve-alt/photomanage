#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
THE TWO CATALOGUES MUST HAVE THE SAME SHAPE.

This exists because of a specific bug. `media_type` was added to
`30_ENGINE/pvm/catalog.py` and not to `40_APP/PVMCore/Sources/PVMCore/Catalog.swift`,
so the app's Intent Search built `WHERE assets.media_type = ?` against a column that did
not exist. `sqlite3_prepare_v2` failed, the unchecked statement stayed nil, and the
search **reported "no matches" to a question it had never asked**.

`generate_shared.py` already stops the taxonomy and the rules drifting, because those
are generated from the engine. The schema is not generated — both files write their own
`CREATE TABLE` statements — so nothing was comparing them. This does.

It compares table and column NAMES, not types or constraints. Two implementations
writing into the same file need to agree on what is there; SQLite is loosely typed
enough that declared types are the weaker half of the contract, and a check that
demanded byte-identical DDL would fail on comments and formatting and be turned off
within a week.

    python 40_APP/check_schema.py
"""

from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON_CATALOG = os.path.join(ROOT, "30_ENGINE", "pvm", "catalog.py")
SWIFT_CATALOG = os.path.join(ROOT, "40_APP", "PVMCore", "Sources", "PVMCore", "Catalog.swift")

_TABLE = re.compile(r"CREATE TABLE IF NOT EXISTS\s+(\w+)\s*\((.*?)\n?\s*\);", re.S)


def _split_top_level(body: str):
    """Split on commas that are not inside parentheses — `DEFAULT (a, b)` is one
    column, not two."""
    depth, current = 0, []
    for character in body:
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
        if character == "," and depth == 0:
            yield "".join(current)
            current = []
        else:
            current.append(character)
    if current:
        yield "".join(current)


def tables(path: str) -> dict:
    """table name -> set of column names, from the CREATE TABLE statements in a file."""
    with open(path, encoding="utf-8") as fh:
        source = fh.read()
    out = {}
    for name, body in _TABLE.findall(source):
        # Comments out, then table-level clauses out, then split on top-level commas.
        # Splitting per line was the first version and it read only the first column of
        # every line — the Swift DDL puts several on one line, so it reported seven
        # differences that did not exist. A drift checker with false positives gets
        # muted, which is worse than not having one.
        body = re.sub(r"--.*$", "", body, flags=re.M)
        body = re.sub(r"\b(PRIMARY KEY|FOREIGN KEY|UNIQUE|CHECK)\s*\([^)]*\)", "",
                      body, flags=re.I)
        columns = set()
        for fragment in _split_top_level(body):
            match = re.match(r"\s*(\w+)\b", fragment)
            if match and match.group(1).upper() not in ("PRIMARY", "FOREIGN", "UNIQUE",
                                                        "CHECK", "REFERENCES"):
                columns.add(match.group(1))
        out[name] = columns
    return out


def main() -> int:
    python, swift = tables(PYTHON_CATALOG), tables(SWIFT_CATALOG)
    problems = []

    if not python or not swift:
        print("could not parse either schema — this check would pass by finding nothing")
        return 1

    for name in sorted(set(python) - set(swift)):
        problems.append(f"table `{name}` exists in the engine and not in the app")
    for name in sorted(set(swift) - set(python)):
        problems.append(f"table `{name}` exists in the app and not in the engine")

    for name in sorted(set(python) & set(swift)):
        missing_in_swift = python[name] - swift[name]
        missing_in_python = swift[name] - python[name]
        for column in sorted(missing_in_swift):
            problems.append(f"{name}.{column} is in the engine and not in the app")
        for column in sorted(missing_in_python):
            problems.append(f"{name}.{column} is in the app and not in the engine")

    shared = len(set(python) & set(swift))
    columns = sum(len(python[t]) for t in set(python) & set(swift))
    for problem in problems:
        print(f"DRIFT: {problem}")
    print(f"\n{shared} shared tables, {columns} columns checked · "
          f"{len(problems)} difference(s)")
    if problems:
        print("\nBoth implementations write into the same database file. A column one "
              "of them does not know about is a query that fails at runtime — and in "
              "the case this check was written for, failed silently.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
