#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Work-Done Ledger — the artifact under test in T0-D.

All four variants are generated from ONE template. That is deliberate: a
between-subjects manipulation is only valid if the variants are identical except
for the dimension being manipulated. Hand-editing four HTML files would let
wording, spacing and colour drift and silently confound the result.

  V1 Full         baseline (protocol §5)
  V2 No numbers   qualitative only          -> is QUANTIFICATION what lands?
  V3 No Protected -> does visible restraint drive trust?
  V4 Review-first "23 items need you" on top -> service, or homework?

Numbers correspond to the 10,000-asset standardised test library. If the library
size changes, change LIBRARY below and regenerate — never edit the HTML by hand.

Usage:  python build_ledger_variants.py
"""

import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ledger")

LIBRARY = {
    "total": "10,000",
    "elapsed": "2 min ago",
    "cats": [("Documents", "604"), ("Purchases", "498"), ("Screenshots", "2,491"),
             ("People", "1,532"), ("Places", "3,118"), ("Objects", "208")],
    "travel": "3 trips", "timeline": "2022–2026",
    "handled": [("284", "expired verification &amp; pickup codes", "cleared"),
                ("1,203", "duplicate downloads", "cleared"),
                ("641", "near-identical burst frames", "best kept")],
    "handled_qual": [("Expired verification &amp; pickup codes", "cleared"),
                     ("Duplicate downloads", "cleared"),
                     ("Near-identical burst frames", "best kept")],
    "protected": [("12", "documents"), ("3", "IDs"), ("1", "contract")],
    "review": "23",
}

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{background:#eef0f3;font:16px/1.45 -apple-system,BlinkMacSystemFont,"SF Pro Text",
     "Helvetica Neue",Arial,sans-serif;color:#111;display:flex;justify-content:center;
     padding:24px 12px}
.phone{width:390px;background:#fff;border-radius:38px;overflow:hidden;
       box-shadow:0 12px 40px rgba(0,0,0,.18)}
.status{height:44px;display:flex;align-items:center;justify-content:space-between;
        padding:0 26px;font-size:13px;font-weight:600}
.hdr{padding:8px 22px 18px}
.hdr h1{font-size:26px;font-weight:700;letter-spacing:-.4px}
.hdr .sub{margin-top:4px;font-size:13px;color:#6b7280}
.sec{padding:0 22px 20px}
.lbl{font-size:11px;font-weight:700;letter-spacing:1.1px;color:#8a8f98;
     text-transform:uppercase;margin:16px 0 9px;display:flex;justify-content:space-between;
     align-items:baseline}
.lbl .foot{font-weight:500;letter-spacing:.2px;text-transform:none;font-size:11px;color:#9aa0a8}
.grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px}
.tile{background:#f5f6f8;border-radius:13px;padding:11px 10px}
.tile .n{font-size:19px;font-weight:700}
.tile .t{font-size:11px;color:#6b7280;margin-top:1px}
.wide{display:flex;gap:8px;margin-top:8px}
.wide .tile{flex:1}
.row{display:flex;align-items:center;gap:11px;padding:10px 0;border-bottom:1px solid #f0f1f3}
.row:last-child{border-bottom:none}
.row .n{font-size:17px;font-weight:700;min-width:52px;font-variant-numeric:tabular-nums}
.row .d{flex:1;font-size:14px;color:#33383f}
.row .s{font-size:12px;color:#0a7d3f;background:#e6f6ec;padding:3px 9px;border-radius:20px;
        white-space:nowrap;font-weight:600}
.row .why{font-size:12px;color:#2f6fd0;text-decoration:none;white-space:nowrap}
.prot{background:#f7f4ee;border-radius:13px;padding:13px 15px}
.prot .l{font-size:14px;font-weight:600;color:#7a5c14}
.prot .m{font-size:12.5px;color:#8a6f2e;margin-top:3px}
.cta{margin:4px 22px 22px;background:#0b63e5;color:#fff;border-radius:15px;
     padding:15px 18px;display:flex;align-items:center;justify-content:space-between}
.cta .l{font-size:15px;font-weight:600}
.cta .r{font-size:14px;opacity:.95}
.cta.top{margin-top:2px}
.note{margin:0 22px 20px;font-size:12px;color:#9aa0a8;text-align:center}
"""

def tiles():
    t = "".join(f'<div class="tile"><div class="n">{n}</div><div class="t">{c}</div></div>'
                for c, n in LIBRARY["cats"])
    return (f'<div class="grid">{t}</div>'
            f'<div class="wide">'
            f'<div class="tile"><div class="n">{LIBRARY["travel"]}</div><div class="t">Travel</div></div>'
            f'<div class="tile"><div class="n">{LIBRARY["timeline"]}</div><div class="t">Timeline</div></div>'
            f'</div>')

def tiles_qual():
    t = "".join(f'<div class="tile"><div class="n" style="font-size:14px">{c}</div>'
                f'<div class="t">sorted</div></div>' for c, _ in LIBRARY["cats"])
    return (f'<div class="grid">{t}</div>'
            f'<div class="wide">'
            f'<div class="tile"><div class="n" style="font-size:14px">Travel</div><div class="t">grouped</div></div>'
            f'<div class="tile"><div class="n" style="font-size:14px">Timeline</div><div class="t">built</div></div>'
            f'</div>')

def handled(numbers=True):
    if numbers:
        rows = "".join(f'<div class="row"><div class="n">{n}</div><div class="d">{d}</div>'
                       f'<div class="s">{s}</div><a class="why" href="#">why?</a></div>'
                       for n, d, s in LIBRARY["handled"])
    else:
        rows = "".join(f'<div class="row"><div class="d">{d}</div>'
                       f'<div class="s">{s}</div><a class="why" href="#">why?</a></div>'
                       for d, s in LIBRARY["handled_qual"])
    return rows

def protected():
    items = " · ".join(f'{n} {t}' for n, t in LIBRARY["protected"])
    return (f'<div class="prot"><div class="l">{items}</div>'
            f'<div class="m">Never touched automatically</div></div>')

def review_cta(top=False):
    return (f'<div class="cta{" top" if top else ""}">'
            f'<div class="l">{LIBRARY["review"]} items need you</div>'
            f'<div class="r">Review &rsaquo;</div></div>')

def page(variant, body, subtitle):
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Work-Done Ledger — {variant}</title>
<style>{CSS}</style></head>
<body><div class="phone">
<div class="status"><span>9:41</span><span>&#9679;&#9679;&#9679; &#9646;</span></div>
<div class="hdr"><h1>Your library is organised.</h1>
<div class="sub">{subtitle}</div></div>
{body}
</div>
<div class="note">T0-D variant {variant} — shown to one participant only (AB-11)</div>
</body></html>"""


def build():
    os.makedirs(OUT, exist_ok=True)
    sub_full = f'{LIBRARY["total"]} photos &middot; finished {LIBRARY["elapsed"]}'
    sub_qual = f'Finished {LIBRARY["elapsed"]}'
    recover = '<span class="foot">all recoverable for 30 days</span>'

    # V1 — full baseline
    v1 = (f'<div class="sec"><div class="lbl">Organised</div>{tiles()}'
          f'<div class="lbl">Handled for you {recover}</div>{handled(True)}'
          f'<div class="lbl">Protected</div>{protected()}</div>'
          f'{review_cta()}')

    # V2 — identical except numbers removed
    v2 = (f'<div class="sec"><div class="lbl">Organised</div>{tiles_qual()}'
          f'<div class="lbl">Handled for you {recover}</div>{handled(False)}'
          f'<div class="lbl">Protected</div>'
          f'<div class="prot"><div class="l">Documents, IDs and contracts</div>'
          f'<div class="m">Never touched automatically</div></div></div>'
          f'<div class="cta"><div class="l">A few items need you</div>'
          f'<div class="r">Review &rsaquo;</div></div>')

    # V3 — identical to V1 except the Protected block is absent
    v3 = (f'<div class="sec"><div class="lbl">Organised</div>{tiles()}'
          f'<div class="lbl">Handled for you {recover}</div>{handled(True)}</div>'
          f'{review_cta()}')

    # V4 — identical content to V1, review moved to the top
    v4 = (f'{review_cta(top=True)}'
          f'<div class="sec"><div class="lbl">Organised</div>{tiles()}'
          f'<div class="lbl">Handled for you {recover}</div>{handled(True)}'
          f'<div class="lbl">Protected</div>{protected()}</div>')

    pages = {
        "v1_full.html":         page("V1 · Full", v1, sub_full),
        "v2_no_numbers.html":   page("V2 · No numbers", v2, sub_qual),
        "v3_no_protected.html": page("V3 · No Protected block", v3, sub_full),
        "v4_review_first.html": page("V4 · Review-first", v4, sub_full),
    }
    for name, html in pages.items():
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write(html)
        print("wrote ledger/" + name)


if __name__ == "__main__":
    build()
