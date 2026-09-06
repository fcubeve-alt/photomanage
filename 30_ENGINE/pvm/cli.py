# -*- coding: utf-8 -*-
"""
CLI for the classification engine.

    python -m pvm.cli classify --library <manifest.json> --catalog out.sqlite
    python -m pvm.cli tree     --catalog out.sqlite
    python -m pvm.cli why      --catalog out.sqlite --asset A00001
    python -m pvm.cli review   --catalog out.sqlite
    python -m pvm.cli remember --catalog out.sqlite
    python -m pvm.cli remember --catalog out.sqlite --where "my red suitcase"

The `--library` reader is deliberately pluggable. On a phone the source is PhotoKit;
here it is whatever adapter can produce `AssetSignals`, which is the only contract the
engine has with the outside world.
"""

from __future__ import annotations

import argparse
import os
import signal
import sys

# `pvm tree | head` is the first thing anyone does with this, and without restoring the
# default SIGPIPE handler Python turns the closed pipe into a traceback after the useful
# output has already been printed. Not available on Windows, hence the guard.
if hasattr(signal, "SIGPIPE"):
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pvm import pipeline, taxonomy                      # noqa: E402
from pvm.catalog import Catalog                          # noqa: E402
from pvm.schedule import plan_ingestion, progress_report  # noqa: E402
from pvm.signals import Tier                             # noqa: E402


def _load(path: str):
    from eval.adapter import load_manifest
    return load_manifest(path)


def cmd_classify(args) -> int:
    assets = _load(args.library)
    catalog = Catalog(args.catalog)
    budget = {"metadata": Tier.METADATA, "hash": Tier.HASH, "visual": Tier.VISUAL,
              "faces": Tier.FACES, "ocr": Tier.TEXT}[args.budget]

    def progress(done, total):
        print(f"  … {done}/{total}", file=sys.stderr)

    stats = pipeline.run(assets, catalog, budget=budget,
                         progress=progress if args.verbose else None)
    print(stats.summary())
    print(f"catalogue: {catalog.size_bytes()/1e6:.1f} MB "
          f"({catalog.size_bytes()/max(1,stats.seen):.0f} B/asset)")
    ctx = stats.context
    if ctx and ctx.home_city:
        print(f"learned home: {ctx.home_city}, {ctx.home_country} "
              f"(confidence {ctx.home_confidence:.2f}, from {ctx.home_sample_size} captures)")
    for t in (ctx.trips if ctx else []):
        print(f"learned trip: {t.label}  {t.start}..{t.end}  {t.asset_count} assets")
    catalog.close()
    return 0


def cmd_plan(args) -> int:
    """What a user with this many photos would actually be told and offered."""
    n = args.assets
    if n is None:
        n = len(_load(args.library))
    plan = plan_ingestion(n, pessimistic=not args.optimistic)
    print(plan.user_message())
    print()
    print(f"breadth pass : {plan.breadth.assets:,} assets in {plan.breadth.human()} "
          f"— {plan.breadth.what_the_user_gets}")
    print("depth pass   : offered as")
    for o in plan.options:
        mark = "*" if o.key == plan.recommended else " "
        print(f"  {mark} [{o.key:9s}] {o.label:32s} {o.daily_assets:>7,}/day  "
              f"{o.days:>4} days  {o.daily_work_min:.0f} min/day")
        if o.caveat:
            print(f"                {o.caveat}")
    print()
    for note in plan.notes:
        print(f"note: {note}")
    return 0


def cmd_tree(args) -> int:
    catalog = Catalog(args.catalog)
    counts = catalog.counts_by_path()
    rolled = {}
    for path, n in counts.items():
        rolled[path] = rolled.get(path, 0) + n
        for anc in taxonomy.ancestors(path):
            rolled[anc] = rolled.get(anc, 0) + n
    for path in sorted(rolled):
        indent = "  " * (taxonomy.depth(path) - 1)
        print(f"{rolled[path]:6d}  {indent}{path.split(taxonomy.SEP)[-1]}")
    catalog.close()
    return 0


def cmd_why(args) -> int:
    catalog = Catalog(args.catalog)
    reasons = catalog.why(args.asset)
    if not reasons:
        print(f"{args.asset}: not in the catalogue")
        catalog.close()
        return 1
    print(args.asset)
    for path, rs in reasons.items():
        print(f"  {path}")
        for r in rs:
            print(f"      · {r}")
    catalog.close()
    return 0


def cmd_review(args) -> int:
    catalog = Catalog(args.catalog)
    rows = catalog.review_queue(args.limit)
    if not rows:
        print("nothing waiting for review")
    for aid, action, risk, note, why in rows:
        print(f"{aid}  [{action}]  {note}")
        print(f"      why: {why}")
    catalog.close()
    return 0


def cmd_remember(args) -> int:
    """§2 Remember, at the command line.

    Two shapes. Without `--where` it lists what the library knows exists — the memory
    itself. With `--where` it answers a question about one of them, which is the only
    output that ever needs hedging, so the hedging lives in `MemoryGraph` and is
    printed verbatim rather than reassembled here.
    """
    catalog = Catalog(args.catalog)
    if args.where:
        graph = _graph_from(catalog)
        print(graph.answer_where_last_seen(args.where))
        catalog.close()
        return 0 if graph.find(args.where) else 1

    rows = catalog.entities(kind=args.kind, limit=args.limit)
    if not rows:
        print("the library remembers nothing yet — run `classify` first")
        catalog.close()
        return 1
    kind = None
    for entity_id, entity_kind, name, category_path, confidence, why in rows:
        if entity_kind != kind:
            kind = entity_kind
            print(f"\n{kind.upper()}")
        shelf = f"   filed under {category_path}" if category_path else ""
        print(f"  {name}  ({confidence:.2f}){shelf}")
        print(f"      because {why}")
        for asset_id, seen_at, place, _conf, reason, _src, place_source, repeats in \
                catalog.sightings(entity_id, limit=args.sightings):
            when = (seen_at or "undated")[:10]
            where = place or "no recorded location"
            hedge = " (inferred)" if place_source != "measured" else ""
            again = f"  — same moment as {repeats}" if repeats else ""
            print(f"      · {when}  {where}{hedge}  [{asset_id}]  {reason}{again}")
    catalog.close()
    return 0


def _graph_from(catalog) -> "MemoryGraph":
    """Read the stored memory back into a graph so questions are answered by the same
    code that built it. Rebuilding the answer logic against SQL would be a second
    implementation of the hedging rules, and the two would drift."""
    from datetime import datetime

    from pvm.memory import Entity, EntityKind, MemoryGraph, Observation
    from pvm.signals import Tier as _Tier
    from pvm.verdict import Evidence

    graph = MemoryGraph()
    for entity_id, kind, name, category_path, confidence, why in catalog.entities(limit=100000):
        entity = Entity(entity_id, EntityKind(kind), name,
                        [Evidence("catalog", _Tier.METADATA, float(confidence), why)])
        entity.category_path = category_path
        graph.entities[entity_id] = entity
        for asset_id, seen_at, place, conf, reason, source, place_source, repeats in \
                catalog.sightings(entity_id, limit=100000):
            graph.observe(Observation(
                entity_id, asset_id,
                datetime.fromisoformat(seen_at) if seen_at else None,
                place, float(conf), reason, source=source, place_source=place_source,
                repeats=repeats))
    return graph


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="pvm", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("classify")
    p.add_argument("--library", required=True)
    p.add_argument("--catalog", default="pvm_catalog.sqlite")
    p.add_argument("--budget", default="ocr",
                   choices=["metadata", "hash", "visual", "faces", "ocr"],
                   help=("highest signal tier the engine may spend. `metadata` IS the "
                         "breadth pass: no pixel is decoded, so a 100k library gets its "
                         "shelves in seconds and the depth pass can be paced afterwards"))
    p.add_argument("--verbose", action="store_true")
    p.set_defaults(fn=cmd_classify)

    p = sub.add_parser("plan", help="how a library of this size would be ingested")
    p.add_argument("--assets", type=int, help="library size; or use --library to count one")
    p.add_argument("--library")
    p.add_argument("--optimistic", action="store_true",
                   help="quote the faster of the two measured runs (default: the slower)")
    p.set_defaults(fn=cmd_plan)

    p = sub.add_parser("tree")
    p.add_argument("--catalog", default="pvm_catalog.sqlite")
    p.set_defaults(fn=cmd_tree)

    p = sub.add_parser("why")
    p.add_argument("--catalog", default="pvm_catalog.sqlite")
    p.add_argument("--asset", required=True)
    p.set_defaults(fn=cmd_why)

    p = sub.add_parser("review")
    p.add_argument("--catalog", default="pvm_catalog.sqlite")
    p.add_argument("--limit", type=int, default=25)
    p.set_defaults(fn=cmd_review)

    p = sub.add_parser("remember",
                       help="what the library knows exists, and where it last saw it")
    p.add_argument("--catalog", default="pvm_catalog.sqlite")
    p.add_argument("--kind", choices=["person", "place", "object", "document",
                                      "purchase", "event"])
    p.add_argument("--where", metavar="THING",
                   help='answer "where did I last see X" for one thing')
    p.add_argument("--limit", type=int, default=40)
    p.add_argument("--sightings", type=int, default=3)
    p.set_defaults(fn=cmd_remember)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
