#!/usr/bin/env python3
"""Prove the app has no way to send anything anywhere.

The privacy policy's first line is "this app collects nothing, because it does not go
online". That is the kind of claim that is true on the day it is written and quietly
false two releases later, when someone adds a crash SDK to find a bug. This check is
what keeps it from being a claim.

It fails the build if the app's own sources contain a networking API or a known
analytics / attribution / crash-reporting SDK. Apple's StoreKit is allowed — purchases
necessarily talk to Apple, the user initiates them, and no data of ours rides along.

Usage:
    python3 40_APP/check_no_network.py
    python3 40_APP/check_no_network.py --selftest
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCANNED = [ROOT / "40_APP" / "PVM", ROOT / "40_APP" / "PVMCore" / "Sources"]

BANNED = re.compile(
    r"\b("
    # Foundation / CFNetwork / Network.framework
    r"URLSession|URLRequest|NSURLConnection|NSURLSession|CFReadStream|CFWriteStream"
    r"|CFSocket|NWConnection|NWListener|NWPathMonitor|NWBrowser"
    r"|getaddrinfo|CFHTTPMessage|NSURLProtocol"
    # embedded web views — a web view is a network stack with a UI
    r"|WKWebView|UIWebView|SFSafariViewController|ASWebAuthenticationSession"
    # the SDKs the competitor teardown found in this category
    r"|Crashlytics|FirebaseAnalytics|FirebaseCore|Sentry|Bugsnag|Instabug"
    r"|Adjust|AppsFlyer|Amplitude|Mixpanel|Segment|BranchSDK|OneSignal"
    r"|GoogleMobileAds|FBSDK|UnityAds|AppLovin|Admost"
    r")\b"
)

COMMENT = re.compile(r"^\s*(//|/\*|\*)")

# The one file allowed to contain these words: it is the privacy policy, generated from
# `50_LAUNCH/PRIVACY_POLICY.md`, and the policy names the APIs it promises not to use.
# Excluded by name rather than by pattern so that adding a second exception is a visible
# edit to this list.
ALLOWED = {"LegalText.generated.swift"}


def offences(paths: list[pathlib.Path]) -> list[str]:
    found: list[str] = []
    for root in paths:
        for swift in sorted(root.rglob("*.swift")):
            if swift.name in ALLOWED:
                continue
            for number, line in enumerate(swift.read_text(encoding="utf-8").splitlines(), 1):
                if COMMENT.match(line):
                    continue
                match = BANNED.search(line)
                if match:
                    try:
                        shown = swift.relative_to(ROOT)
                    except ValueError:
                        shown = swift
                    found.append(f"{shown}:{number}: {match.group(1)} — {line.strip()}")
    return found


def check_project_dependencies() -> list[str]:
    """No third-party package may be linked into the app at all."""
    spec = (ROOT / "40_APP" / "project.yml").read_text(encoding="utf-8")
    packages = re.findall(r"^  (\w+):\s*$", spec.split("packages:", 1)[-1].split("settings:", 1)[0],
                          flags=re.MULTILINE)
    return [f"project.yml declares a third-party package: {name}"
            for name in packages if name != "PVMCore"]


def selftest() -> int:
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        base = pathlib.Path(directory)
        (base / "Bad.swift").write_text(
            "func f() {\n    let s = URLSession.shared\n}\n", encoding="utf-8")
        (base / "Comment.swift").write_text(
            "// there is no URLSession in this app\n/// and no Crashlytics either\n"
            "func g() {}\n", encoding="utf-8")
        (base / "Clean.swift").write_text("func h() { }\n", encoding="utf-8")
        found = offences([base])
        assert len(found) == 1, found
        assert "URLSession" in found[0], found
        assert "Comment.swift" not in "".join(found), found

        (base / "LegalText.generated.swift").write_text(
            'let t = "no URLSession here"\n', encoding="utf-8")
        assert len(offences([base])) == 1, "the generated policy must be exempt"
    print("check_no_network selftest: ok")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    if parser.parse_args().selftest:
        return selftest()

    problems = offences(SCANNED) + check_project_dependencies()
    if problems:
        print("NETWORK CODE IN AN APP THAT PROMISES NOT TO HAVE ANY:", file=sys.stderr)
        for problem in problems:
            print("  " + problem, file=sys.stderr)
        print("\nThe privacy policy and the App Store privacy label both say this app "
              "collects nothing.\nIf that has changed, change those first — "
              "50_LAUNCH/PRIVACY_POLICY.md and the App Privacy questionnaire.",
              file=sys.stderr)
        return 1

    scanned = sum(1 for root in SCANNED for _ in root.rglob("*.swift"))
    print(f"no networking API and no analytics SDK in {scanned} Swift files "
          "(StoreKit excepted: purchases go to Apple, user-initiated)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
