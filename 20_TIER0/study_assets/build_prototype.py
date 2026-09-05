#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T0-B prototype — the Visual Library home and its drill-down.

DIRECTIVE (Owner, 2026-08-22 · DEC-017):
    This is NOT an "AI work report dashboard". It is first and foremost the entry
    point that replaces Apple Photos, and only second a report of what the system
    did. ORGANIZED is not a handful of smart collections — it is a stable,
    predictable Library Taxonomy that drills down through second and third levels.

DATA (DEC-019): the tree comes from `taxonomy.py` and every count and every asset
comes from `library/manifest.json`. Nothing here is hand-written any more. Before
this, counts were invented and leaves were coloured rectangles — which meant a
facilitator could not actually complete a task inside the prototype, and the study
would have been unrunnable in the room.

SCOPE BOUNDARY: a NAVIGATIONAL SKELETON, hand-authored for the test library. NOT the
Tier 1-A Visual Asset Taxonomy (no classifier, no confusion matrix, no risk or
lifecycle defaults) — the Execution Index forbids building that now (DEC-003, P-01).

The prototype must NEVER label which asset is a task answer. The answer key lives in
manifest.json for the facilitator, not on screen.

Usage:  python generate_test_library.py --out ./library --count 10000 --manifest-only
        python build_prototype.py
"""

import os, json, html, hashlib
import taxonomy
import sys
# Output is UTF-8 regardless of console locale (PF-10 — cp936 cannot encode the
# report glyphs and the tool would die after doing all the work).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "prototype")
MANIFEST = os.path.join(HERE, "library", "manifest.json")

# Work-report figures. These describe actions the system claims to have taken; they
# are prepared for the study (T0-B L-1 / T0-D L-4) and are deliberately consistent
# with the library composition rather than invented independently.
HANDLED = [
    ("284",   "expired verification &amp; pickup codes", "cleared"),
    ("1,203", "duplicate downloads",                     "cleared"),
    ("641",   "near-identical burst frames",             "best kept"),
]
PROTECTED = [("12", "documents"), ("3", "IDs"), ("1", "contract")]
REVIEW = "23"

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{background:#eef0f3;font:16px/1.45 -apple-system,BlinkMacSystemFont,"SF Pro Text",
     "Helvetica Neue",Arial,sans-serif;color:#111;display:flex;justify-content:center;padding:24px 12px}
a{text-decoration:none;color:inherit}
.phone{width:390px;background:#fff;border-radius:38px;overflow:hidden;
       box-shadow:0 12px 40px rgba(0,0,0,.18);min-height:760px}
.status{height:44px;display:flex;align-items:center;justify-content:space-between;
        padding:0 26px;font-size:13px;font-weight:600}
.summary{padding:6px 22px 18px}
.summary h1{font-size:26px;font-weight:700;letter-spacing:-.4px}
.summary .lines{margin-top:7px;font-size:13.5px;color:#5b626b;line-height:1.6}
.summary .lines b{color:#111;font-variant-numeric:tabular-nums}
.summary .need{margin-top:10px;display:inline-block;background:#eef4ff;color:#0b63e5;
     border-radius:20px;padding:6px 13px;font-size:13px;font-weight:600}
.nav{display:flex;align-items:center;gap:10px;padding:10px 18px 6px}
.nav a.back{font-size:15px;color:#0b63e5;font-weight:600}
.nav .crumb{font-size:12px;color:#8a8f98;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.title{padding:2px 22px 12px}
.title h2{font-size:24px;font-weight:700;letter-spacing:-.3px}
.title .c{font-size:13px;color:#8a8f98;margin-top:2px}
.lbl{font-size:11px;font-weight:700;letter-spacing:1.1px;color:#8a8f98;text-transform:uppercase;
     margin:14px 22px 9px;display:flex;justify-content:space-between;align-items:baseline}
.lbl .foot{font-weight:500;letter-spacing:.2px;text-transform:none;font-size:11px;color:#9aa0a8}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:9px;padding:0 22px}
.card{background:#f5f6f8;border-radius:14px;padding:13px 12px;display:block;border:1px solid transparent}
.card:hover{border-color:#d9dde3;background:#f0f2f5}
.card .ic{font-size:20px}
.card .nm{font-size:14.5px;font-weight:650;margin-top:6px}
.card .ct{font-size:12px;color:#8a8f98;margin-top:1px;font-variant-numeric:tabular-nums}
.list{padding:0 22px}
.row{display:flex;align-items:center;gap:12px;padding:13px 2px;border-bottom:1px solid #f0f1f3}
.row:last-child{border-bottom:none}
.row .nm{flex:1;font-size:15px;font-weight:550}
.row .ct{font-size:13px;color:#8a8f98;font-variant-numeric:tabular-nums}
.row .ch{font-size:16px;color:#c3c8cf}
.row .tag{font-size:10.5px;color:#8a6f2e;background:#f7f4ee;border-radius:5px;padding:2px 6px}
.row .pend{font-size:10.5px;color:#a33;background:#fdeaea;border-radius:5px;padding:2px 6px}
.assets{display:grid;grid-template-columns:1fr 1fr 1fr;gap:3px;padding:0 22px}
.asset{aspect-ratio:1;border-radius:5px;display:flex;align-items:flex-end;
       font-size:8.5px;color:#fff;padding:4px;text-shadow:0 1px 2px rgba(0,0,0,.6);
       line-height:1.15;overflow:hidden}
.more{padding:14px 22px 0;font-size:12px;color:#8a8f98}
.hr{height:9px;background:#f1f3f5;margin-top:26px}
.wrow{display:flex;align-items:center;gap:11px;padding:10px 22px;border-bottom:1px solid #f4f5f7}
.wrow .n{font-size:16px;font-weight:700;min-width:50px;font-variant-numeric:tabular-nums}
.wrow .d{flex:1;font-size:13.5px;color:#33383f}
.wrow .s{font-size:11.5px;color:#0a7d3f;background:#e6f6ec;padding:3px 8px;border-radius:20px;
         white-space:nowrap;font-weight:600}
.wrow .why{font-size:11.5px;color:#2f6fd0;white-space:nowrap}
.prot{margin:0 22px;background:#f7f4ee;border-radius:13px;padding:12px 14px}
.prot .l{font-size:13.5px;font-weight:600;color:#7a5c14}
.prot .m{font-size:12px;color:#8a6f2e;margin-top:2px}
.cta{margin:16px 22px 24px;background:#0b63e5;color:#fff;border-radius:15px;padding:14px 17px;
     display:flex;align-items:center;justify-content:space-between}
.cta .l{font-size:15px;font-weight:600}
.cta .r{font-size:14px;opacity:.95}
.caption{width:390px;text-align:center;color:#8a8f98;font-size:12px;margin-top:14px}
"""


def esc(s): return html.escape(str(s))


def slug(parts):
    return "_".join(p.lower().replace(" ", "-").replace("·", "").replace("&", "and").strip("-")
                    for p in parts) or "index"


def load_manifest():
    if not os.path.exists(MANIFEST):
        raise SystemExit(
            f"manifest not found: {MANIFEST}\n"
            "Run first:  python generate_test_library.py --out ./library "
            "--count 10000 --manifest-only")
    with open(MANIFEST, encoding="utf-8") as f:
        return json.load(f)


def index_assets(manifest):
    """path -> [assets]. An asset appears under every path it is indexed by (§3)."""
    by_path = {}
    for a in manifest["assets"]:
        for p in a.get("paths", []):
            by_path.setdefault(p, []).append(a)
    return by_path


def count_under(by_path, node_path):
    """Unique assets at or below a node. Deduplicated, because one asset reachable
    from two entries must not be counted twice."""
    prefix = taxonomy.SEP.join(node_path)
    ids = set()
    for p, assets in by_path.items():
        if p == prefix or p.startswith(prefix + taxonomy.SEP):
            ids.update(a["id"] for a in assets)
    return len(ids)


pages = {}


def shell(body, caption=""):
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<title>Visual Library</title><style>{CSS}</style></head><body>
<div><div class="phone">
<div class="status"><span>9:41</span><span>&#9679;&#9679;&#9679; &#9646;</span></div>
{body}
</div><div class="caption">{caption}</div></div></body></html>"""


def summary_header(manifest, variant="v1"):
    total = f'{manifest["total_assets"]:,}'
    handled = f'{sum(int(n.replace(",", "")) for n, _, _ in HANDLED):,}'
    if variant == "v2":
        return ('<div class="summary"><h1>Your library is organised.</h1>'
                '<div class="lines">Everything analysed.<br>Duplicates, expired codes '
                'and burst frames handled.</div>'
                '<div class="need">A few items need you &rsaquo;</div></div>')
    return (f'<div class="summary"><h1>Your library is organised.</h1>'
            f'<div class="lines"><b>{total}</b> photos and videos analysed<br>'
            f'<b>{handled}</b> items organised or handled</div>'
            f'<div class="need">Only <b>{REVIEW}</b> need your attention &rsaquo;</div></div>')


def library_grid(by_path):
    cells = []
    for top in taxonomy.TREE:
        icon = taxonomy.TREE[top].get("_icon", "📁")
        n = count_under(by_path, [top])
        cells.append(f'<a class="card" href="{slug([top])}.html">'
                     f'<div class="ic">{icon}</div>'
                     f'<div class="nm">{esc(top)}</div>'
                     f'<div class="ct">{n:,}</div></a>')
    return f'<div class="lbl">Your library</div><div class="grid">{"".join(cells)}</div>'


def work_report(variant="v1"):
    if variant == "v3_no_protected":
        prot = ""
    else:
        items = " · ".join(f"{n} {t}" for n, t in PROTECTED)
        prot = (f'<div class="lbl">Protected</div><div class="prot"><div class="l">{items}</div>'
                f'<div class="m">Never touched automatically</div></div>')
    if variant == "v2":
        rows = "".join(f'<div class="wrow"><div class="d">{d}</div>'
                       f'<div class="s">{s}</div><div class="why">why?</div></div>'
                       for _, d, s in HANDLED)
    else:
        rows = "".join(f'<div class="wrow"><div class="n">{n}</div><div class="d">{d}</div>'
                       f'<div class="s">{s}</div><div class="why">why?</div></div>'
                       for n, d, s in HANDLED)
    return ('<div class="hr"></div>'
            '<div class="lbl">Handled for you <span class="foot">all recoverable for 30 days</span></div>'
            + rows + prot)


def review_cta():
    return (f'<a class="cta" href="#"><div class="l">{REVIEW} items need you</div>'
            f'<div class="r">Review &rsaquo;</div></a>')


def render_assets(assets):
    """Leaf view. Neutral labels only — the prototype must never reveal which asset
    is a task answer, or the task becomes trivial."""
    assets = sorted(assets, key=lambda a: a["captured_at"], reverse=True)
    shown = assets[:24]
    tiles = []
    for a in shown:
        h = int(hashlib.md5(a["id"].encode()).hexdigest()[:2], 16) * 360 // 256
        label = a.get("placeholder_text") or ""
        date = a["captured_at"][:10]
        tiles.append(f'<div class="asset" style="background:hsl({h},42%,55%)">'
                     f'{esc(label[:34])}<br>{date}</div>')
    more = ""
    if len(assets) > len(shown):
        more = f'<div class="more">+ {len(assets) - len(shown):,} more</div>'
    return f'<div class="assets">{"".join(tiles)}</div>{more}'


def build_node(path, by_path):
    name = path[-1]
    meta = taxonomy.node_meta(path)
    children = meta.get("children")
    parent_href = (slug(path[:-1]) + ".html") if len(path) > 1 else "index.html"
    crumb = " › ".join(path)
    n = count_under(by_path, path)

    nav = (f'<div class="nav"><a class="back" href="{parent_href}">&lsaquo; Back</a>'
           f'<div class="crumb">{esc(crumb)}</div></div>')
    head = (f'<div class="title"><h2>{esc(name)}</h2>'
            f'<div class="c">{n:,} item{"" if n == 1 else "s"}</div></div>')

    if children:
        rows = []
        for cname in children:
            if cname.startswith("_"):
                continue
            cmeta = children[cname]
            cn = count_under(by_path, path + [cname])
            tag = ""
            if cmeta.get("_also_in"):
                tag = f'<span class="tag">also in {esc(cmeta["_also_in"])}</span>'
            if cmeta.get("_pending"):
                tag = '<span class="pend">pending decision</span>'
            rows.append(f'<a class="row" href="{slug(path + [cname])}.html">'
                        f'<div class="nm">{esc(cname)}</div>{tag}'
                        f'<div class="ct">{cn:,}</div><div class="ch">&rsaquo;</div></a>')
            build_node(path + [cname], by_path)
        body = nav + head + f'<div class="list">{"".join(rows)}</div>'
    else:
        assets = by_path.get(taxonomy.SEP.join(path), [])
        body = nav + head + render_assets(assets)

    pages[slug(path) + ".html"] = shell(body, f"T0-B prototype · {esc(crumb)}")


def build_home(filename, manifest, by_path, variant="v1", review_first=False, cap=None):
    parts = [summary_header(manifest, variant)]
    if review_first:
        parts += [review_cta(), library_grid(by_path), work_report(variant)]
    else:
        parts += [library_grid(by_path), work_report(variant), review_cta()]
    pages[filename] = shell("".join(parts), cap or "T0-B prototype · Home")


def main():
    manifest = load_manifest()
    by_path = index_assets(manifest)

    for top in taxonomy.TREE:
        build_node([top], by_path)

    build_home("index.html", manifest, by_path, "v1")
    build_home("ledger_v1.html", manifest, by_path, "v1", cap="T0-D variant V1 · Full")
    build_home("ledger_v2.html", manifest, by_path, "v2", cap="T0-D variant V2 · No numbers")
    build_home("ledger_v3.html", manifest, by_path, "v3_no_protected",
               cap="T0-D variant V3 · No Protected block")
    build_home("ledger_v4.html", manifest, by_path, "v1", review_first=True,
               cap="T0-D variant V4 · Review-first")

    os.makedirs(OUT, exist_ok=True)
    for fn, htm in pages.items():
        with open(os.path.join(OUT, fn), "w", encoding="utf-8") as f:
            f.write(htm)

    print(f"wrote {len(pages)} pages -> {OUT}")
    print(f"assets indexed: {manifest['total_assets']:,}  "
          f"index entries: {sum(len(v) for v in by_path.values()):,}")

    # Every task answer must be reachable by clicking. If one is not, the study is
    # unrunnable in the room and we would only find out with a participant present.
    print("\ntask answers reachable in the prototype:")
    ok = True
    for tt, ids in sorted(manifest["task_targets"].items()):
        target = next(a for a in manifest["assets"] if a["id"] == ids[0])
        leaf = target["paths"][0]
        page = slug(leaf.split(taxonomy.SEP)) + ".html"
        present = page in pages and target in by_path.get(leaf, [])
        ok &= present
        print(f"  {'OK ' if present else 'MISSING'}  {tt:<20} {leaf}  ->  {page}")
    if not ok:
        raise SystemExit("aborting: a task answer is not reachable")


if __name__ == "__main__":
    main()
