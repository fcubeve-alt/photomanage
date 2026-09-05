#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T0-C2 local preview + event collector.

Two jobs:
  1. Serve /a /b /c so the pages can be checked before anything is deployed.
  2. Be the REFERENCE IMPLEMENTATION of the event endpoint — the production
     deployment needs exactly these two routes and nothing more.

Events land in `events.jsonl`, emails in `emails.jsonl`. Append-only, so a crash
loses at most the last line.

PRIVACY (§26): first-party only. No third-party pixel, no cookies, no analytics SDK.
The IP address is NOT stored — only a random per-session id the page generates
itself, which is enough to compute a funnel and nothing more. Running a
privacy-first product's own test on surveillance infrastructure would be the first
broken promise, made before we ship anything.

    python server.py            # http://localhost:8000/a
    python server.py --report   # funnel table from whatever has been collected
"""

import argparse, json, os, sys, datetime
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
# Output is UTF-8 regardless of console locale (PF-10 — cp936 cannot encode the
# report glyphs and the tool would die after doing all the work).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "site")
EVENTS = os.path.join(HERE, "events.jsonl")
EMAILS = os.path.join(HERE, "emails.jsonl")

FUNNEL = [
    ("E2", "landing page view"),
    ("E3", "scrolled >= 50%"),
    ("E4", "price block seen"),
    ("E5", "clicked Get it   <-- PRIMARY"),
    ("E6", "disclosure shown"),
    ("E7", "email captured"),
    ("E8", "no thanks"),
]


def append(path, obj):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=SITE, **kw)

    def log_message(self, fmt, *args):
        pass  # keep the console readable; events are the output that matters

    def do_POST(self):
        if self.path != "/event":
            self.send_error(404)
            return
        try:
            n = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            self.send_error(400)
            return

        rec = {
            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "arm": data.get("arm"),
            "sid": data.get("sid"),
            "event": data.get("event"),
        }
        extra = data.get("extra") or {}

        # Emails are the one piece of personal data here, so they are stored apart
        # from the funnel and never inside the event stream.
        if rec["event"] == "E7" and extra.get("email"):
            append(EMAILS, {"ts": rec["ts"], "arm": rec["arm"],
                            "email": extra["email"], "price": "39"})
            extra = {"captured": True}
        if extra:
            rec["extra"] = extra

        append(EVENTS, rec)
        print(f'  {rec["arm"]}  {rec["event"]:<4} {rec["sid"][:8]}')
        self.send_response(204)
        self.end_headers()


def report():
    if not os.path.exists(EVENTS):
        print("no events yet")
        return
    rows = [json.loads(l) for l in open(EVENTS, encoding="utf-8") if l.strip()]
    arms = sorted({r["arm"] for r in rows if r.get("arm")})
    # Count unique sessions per event, not raw hits.
    uniq = {}
    for r in rows:
        uniq.setdefault((r["arm"], r["event"]), set()).add(r["sid"])

    print(f"\n{'':<34}" + "".join(f"{('/' + a):>10}" for a in arms))
    for code, label in FUNNEL:
        line = f"{code} {label:<30}"
        for a in arms:
            line += f"{len(uniq.get((a, code), ())):>10}"
        print(line)

    print("\npre-registered criteria (T0C2_LANDING_PAGE_PLAN.md §6):")
    for a in arms:
        e2 = len(uniq.get((a, "E2"), ()))
        e4 = len(uniq.get((a, "E4"), ()))
        e5 = len(uniq.get((a, "E5"), ()))
        e7 = len(uniq.get((a, "E7"), ()))
        if not e2:
            continue
        cp1 = e5 / e2 * 100
        cp3 = e7 / e5 * 100 if e5 else 0
        cp4 = e5 / e4 * 100 if e4 else 0
        print(f"  /{a}  C-P1 click-to-buy {cp1:5.2f}%   "
              f"C-P3 survives disclosure {cp3:5.1f}%   C-P4 price not blocker {cp4:5.1f}%")
    print("\nNOTE: n>=400 per arm before any of this is readable. Thresholds are "
          "pre-registered and must not be revised to fit the data (AB-7).")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()

    if args.report:
        report()
        return
    if not os.path.isdir(SITE):
        sys.exit("site/ not built — run: python build_landing.py")

    print(f"serving {SITE} on http://localhost:{args.port}")
    print("  arm A (Organised Library)   http://localhost:%d/a/" % args.port)
    print("  arm B (Continuous Manager)  http://localhost:%d/b/" % args.port)
    print("  arm C (Cleaner, control)    http://localhost:%d/c/" % args.port)
    print("\nevents -> events.jsonl   ·   emails -> emails.jsonl   ·   Ctrl-C to stop\n")
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
