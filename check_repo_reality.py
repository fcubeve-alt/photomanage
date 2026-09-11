#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Does the repository actually look the way the state documents say it does?

A third-party audit on 2026-09-11 found four claims on the front page and in
`PROJECT_STATE.md` that were true when written and had silently stopped being true:
the repository was described as PRIVATE while GitHub served it publicly, the README
said the product was "zero lines" while an engine and an app existed, the harness was
"NEVER COMPILED" after it had compiled, and the active branch was recorded as `main`
while 67 commits of work sat somewhere else.

`recovery_check.py` passed through all of it, because it checks that the documents are
parseable and internally cross-referenced — not that they are TRUE. Those are different
questions and only one of them had a check.

This is the other one. It compares what the documents assert against what git and the
GitHub API actually report. It is deliberately small: a handful of facts that are cheap
to observe and expensive to get wrong.

    python check_repo_reality.py              # uses git; API facts need a token
    python check_repo_reality.py --selftest
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "PROJECT_STATE.md")
README = os.path.join(HERE, "README.md")
SLUG = "fcubeve-alt/photomanage"


def _git(*args) -> str:
    try:
        return subprocess.run(["git", "-C", HERE, *args], capture_output=True,
                              text=True, timeout=30).stdout.strip()
    except Exception:
        return ""


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


# In CI the network is available and a token is provided, so "could not reach the API"
# means the check did not run — and a check that silently does not run is worse than no
# check, because the green tick still appears. `--ci` turns that into a failure.
FAIL_CLOSED = False


def check_visibility(state: str):
    """The claim that mattered most, and the one nothing was watching."""
    claims_private = bool(re.search(r"\bPRIVATE\b", state)) and \
        not re.search(r"\*\*PUBLIC\*\*", state)
    if not claims_private:
        return []

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    request = urllib.request.Request(f"https://api.github.com/repos/{SLUG}")
    request.add_header("Accept", "application/vnd.github+json")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            private = json.loads(response.read()).get("private")
    except Exception as exc:                       # offline, rate-limited, no token
        # On a developer machine this is not a failure: a check that fails whenever the
        # network is unavailable gets switched off, and then it checks nothing. In CI
        # it IS a failure, because there the only reasons to land here are a missing
        # token, a revoked one, or rate limiting — all of which mean the claim went
        # unverified while the build reported success.
        if FAIL_CLOSED:
            return [f"the repository's visibility could not be verified "
                    f"({type(exc).__name__}) and this run requires it"]
        print(f"  (visibility not verified: {type(exc).__name__}) ")
        return []
    if private is False:
        return ["PROJECT_STATE.md describes the repository as PRIVATE and the GitHub "
                "API reports it as PUBLIC"]
    return []


def check_branch(state: str):
    """`main` being the recorded branch while the work is elsewhere."""
    problems = []
    head = _git("rev-parse", "--abbrev-ref", "HEAD")
    if not head:
        return problems
    behind = _git("rev-list", "--count", "origin/main..HEAD")
    ahead = int(behind) if behind.isdigit() else 0
    if ahead > 0 and head != "main":
        if head not in state:
            problems.append(
                f"the working branch is {head!r}, {ahead} commits ahead of main, and "
                "PROJECT_STATE.md does not mention it")
    return problems


def check_zero_lines(readme: str):
    """The README claiming the product does not exist while it does."""
    problems = []
    engine = os.path.join(HERE, "30_ENGINE", "pvm", "classifier.py")
    app = os.path.join(HERE, "40_APP", "PVM", "PVMApp.swift")
    exists = os.path.exists(engine) and os.path.exists(app)
    if exists and re.search(r"(Zero lines|zero lines|do not exist)", readme):
        # Allowed only where the README is explicitly narrating the correction.
        narrating = "stopped being true" in readme or "until 2026-09-11" in readme
        if not narrating:
            problems.append(
                "README.md says the product is not built, and both "
                "30_ENGINE/pvm/classifier.py and 40_APP/PVM/PVMApp.swift exist")
    return problems


def check_never_compiled(state: str):
    if "NEVER COMPILED" in state and "stopped being true" not in state:
        return ["PROJECT_STATE.md still says the harness was NEVER COMPILED"]
    return []


def run(state: str, readme: str):
    problems = []
    problems += check_visibility(state)
    problems += check_branch(state)
    problems += check_zero_lines(readme)
    problems += check_never_compiled(state)
    return problems


def selftest() -> int:
    """Feed each check the state it exists to catch."""
    fails = []
    if not check_zero_lines("the product is Zero lines and nothing is built"):
        fails.append("a README claiming zero lines was not caught")
    if check_zero_lines("an engine and an app exist"):
        fails.append("a correct README was reported as wrong")
    if not check_never_compiled("the harness was NEVER COMPILED"):
        fails.append("a NEVER COMPILED claim was not caught")
    if check_never_compiled("NEVER COMPILED — that stopped being true on 2026-09-06"):
        fails.append("a narrated correction was reported as a stale claim")

    # The fail-closed path, which is the whole point of --ci and was not covered.
    # Pointed at a host that cannot resolve, so the request is guaranteed to raise.
    global SLUG, FAIL_CLOSED
    slug, closed = SLUG, FAIL_CLOSED
    SLUG = "invalid.invalid/nothing"
    try:
        FAIL_CLOSED = False
        if check_visibility("the repo must stay PRIVATE"):
            fails.append("an unreachable API was reported as drift in the default mode")
        FAIL_CLOSED = True
        if not check_visibility("the repo must stay PRIVATE"):
            fails.append("an unreachable API did not fail the check under --ci")
        if check_visibility("the repo is **PUBLIC** by decision"):
            fails.append("a document that does not claim PRIVATE still hit the network")
    finally:
        SLUG, FAIL_CLOSED = slug, closed
    for f in fails:
        print("FAIL:", f)
    print(f"\nselftest: {len(fails)} failure(s)")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--ci", action="store_true",
                    help="treat an unverifiable claim as drift (see FAIL_CLOSED)")
    args = ap.parse_args()
    if args.selftest:
        return selftest()

    global FAIL_CLOSED
    FAIL_CLOSED = args.ci

    problems = run(_read(STATE), _read(README))
    for problem in problems:
        print("DRIFT:", problem)
    print(f"\n{len(problems)} claim(s) the repository does not support")
    if problems:
        print("\nThese are statements about the world, not about the code. "
              "`recovery_check.py` cannot catch them — it checks that the documents "
              "are coherent, not that they are true.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
