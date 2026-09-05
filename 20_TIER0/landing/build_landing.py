#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T0-C2 landing pages — three arms, one template.

Implements `20_TIER0/T0C2_LANDING_PAGE_PLAN.md`.

WHAT IS BEING MANIPULATED: positioning, not price. The Tier 0 kill question is which
rung of the Value Ladder carries willingness to pay, not what the optimal price is.
So layout, price, CTA mechanics and instrumentation are IDENTICAL across arms and
generated from one template — hand-editing three files would let them drift and
silently confound the result.

    /a  L1 Organised Library    the DEC-012 differentiator (§12, §22)
    /b  L2 Continuous Manager   the rung Tier 0 §4 names (§13)
    /c  L3 Cleaner              CONTROL. Not a candidate positioning — §24 Gate 4
                                forbids shipping as a Cleaner. It exists so a low
                                number on A or B is interpretable.

ETHICS — these are structural, not decoration:
  · NO money is ever taken. There is no payment processor wired in at all, so it is
    not possible to charge someone by accident.
  · The instant anyone commits to buy, a full-screen disclosure tells them the truth
    BEFORE anything else. It is not a footnote and it cannot be scrolled past.
  · No fake countdowns, no fake scarcity, no invented reviews, no fake company.
  · Ad copy must not claim the app is available today.

PRIVACY (§26): no third-party ad pixel, no Google Analytics, no cookies. Events go
first-party to our own endpoint. Running a privacy-first product's own test on
surveillance infrastructure would be the first broken promise, made before we ship.

Usage:  python build_landing.py
        python server.py          # local preview + event capture
"""

import os
import sys
# Output is UTF-8 regardless of console locale (PF-10 — cp936 cannot encode the
# report glyphs and the tool would die after doing all the work).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "site")

PRICE = "$39"

# ---------------------------------------------------------------------------
# The only thing that differs between arms.
# ---------------------------------------------------------------------------
ARMS = {
    "a": {
        "rung": "L1 · Organised Library",
        "title": "Your camera roll, catalogued",
        "h1": "Your camera roll, catalogued.",
        "sub": "Open it once. Everything is already sorted.",
        "lede": "Not another photo app you have to organise. Install it, and 12,000 photos "
                "come back as a library — Documents, People, Screenshots, Places, Travel, "
                "Objects — with your passport where you would expect a passport to be.",
        "points": [
            ("You already know where things are",
             "Documents → Identity → Passport. Purchases → Receipts. Screenshots → Chat, "
             "Shopping, Maps. You do not search for the category — you just go there."),
            ("One photo, many places",
             "A receipt is in Purchases, in that Tuesday, in that shop, and in that trip. "
             "One copy on your phone, reachable from all of them."),
            ("It stays on your phone",
             "Everything runs on your device. Your photos, your documents, your family — "
             "none of it is uploaded, and none of it is sold to anyone."),
        ],
    },
    "b": {
        "rung": "L2 · Continuous Manager",
        "title": "Stop managing your photos",
        "h1": "Stop managing your photos.",
        "sub": "It sorts, files and cleans up. You get asked about 23 things.",
        "lede": "Every screenshot, every burst, every expired verification code — handled "
                "the moment it lands. Not a cleanup you run. A library that stays clean "
                "because something is looking after it.",
        "points": [
            ("It does the boring 99%",
             "Expired pickup codes, duplicate downloads, eight near-identical burst frames. "
             "Sorted and cleared — and everything it removes is recoverable for 30 days."),
            ("It is careful with the 1% that matters",
             "IDs, contracts, receipts and family photos are protected by default. It will "
             "never quietly delete something it cannot replace — and it tells you why it "
             "did anything."),
            ("It keeps doing it",
             "Every new photo goes through the same process, forever. You do not have to "
             "remember to run anything."),
        ],
    },
    "c": {
        "rung": "L3 · Cleaner (CONTROL — not a candidate positioning)",
        "title": "Free up space on your iPhone",
        "h1": "Free up space on your iPhone.",
        "sub": "Find duplicates, screenshots and blurry shots in one scan.",
        "lede": "Scan your library, see what is taking up room, and clear it in a few taps.",
        "points": [
            ("Find duplicates",
             "Exact copies and near-identical shots, grouped, with the best one marked."),
            ("Clear out screenshots",
             "Old screenshots and expired codes, gathered in one place."),
            ("Recover space fast",
             "See the biggest videos and photos first."),
        ],
    },
}

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
:root{--ink:#12141a;--muted:#5d646e;--line:#e6e9ee;--bg:#fff;--accent:#0b63e5}
html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--ink);font:17px/1.6 -apple-system,BlinkMacSystemFont,
     "Segoe UI","Helvetica Neue",Arial,sans-serif;-webkit-font-smoothing:antialiased}
.wrap{max-width:680px;margin:0 auto;padding:0 22px}
header{padding:64px 0 8px}
h1{font-size:clamp(34px,6vw,50px);line-height:1.08;letter-spacing:-1.2px;font-weight:750}
.sub{font-size:clamp(19px,2.6vw,23px);color:var(--muted);margin-top:14px;line-height:1.35;
     font-weight:450}
.lede{margin-top:26px;font-size:18px;color:#3a4049;max-width:600px}
.cta-block{margin:34px 0 8px}
.btn{display:inline-flex;align-items:center;gap:10px;background:var(--accent);color:#fff;
     border:none;border-radius:13px;padding:17px 30px;font-size:18px;font-weight:640;
     cursor:pointer;font-family:inherit}
.btn:hover{background:#0a58cc}
.btn .p{opacity:.85;font-weight:500}
.terms{margin-top:11px;font-size:14px;color:var(--muted)}
.shot{margin:52px 0;border:1px solid var(--line);border-radius:18px;overflow:hidden;
      background:#f7f8fa}
.shot .bar{display:flex;gap:6px;padding:12px 14px;border-bottom:1px solid var(--line)}
.shot .bar i{width:10px;height:10px;border-radius:50%;background:#d6dae1;display:block}
.shot .body{padding:26px 24px;font-size:14.5px;color:#4a515b;line-height:1.75}
.shot .body b{color:var(--ink)}
.points{margin:56px 0 0;display:grid;gap:34px}
.pt h3{font-size:20px;letter-spacing:-.3px;font-weight:680}
.pt p{margin-top:8px;color:var(--muted);font-size:16.5px}
.price{margin:64px 0;padding:30px 26px;border:1px solid var(--line);border-radius:18px;
       background:#fafbfc}
.price .amt{font-size:31px;font-weight:740;letter-spacing:-.6px}
.price .amt span{font-size:18px;font-weight:500;color:var(--muted)}
.price ul{list-style:none;margin-top:16px;display:grid;gap:7px}
.price li{font-size:16px;color:#3a4049;padding-left:24px;position:relative}
.price li::before{content:"✓";position:absolute;left:0;color:#0a7d3f;font-weight:700}
footer{margin:64px 0 90px;padding-top:26px;border-top:1px solid var(--line);
       font-size:14px;color:var(--muted)}
footer a{color:var(--muted)}
/* ---- disclosure: full screen, unmissable, fires the instant anyone commits ---- */
.veil{position:fixed;inset:0;background:rgba(14,17,22,.62);display:none;
      align-items:center;justify-content:center;padding:22px;z-index:99}
.veil.on{display:flex}
.card{background:#fff;border-radius:20px;max-width:520px;width:100%;padding:36px 32px}
.card h2{font-size:27px;letter-spacing:-.6px;font-weight:730}
.card p{margin-top:14px;color:#3a4049;font-size:17px}
.card .row{margin-top:24px;display:flex;gap:11px;flex-wrap:wrap}
.card input{flex:1;min-width:220px;padding:15px 16px;border:1px solid #ccd2da;
            border-radius:12px;font-size:16px;font-family:inherit}
.card .no{background:none;border:none;color:var(--muted);font-size:15px;cursor:pointer;
          margin-top:16px;text-decoration:underline;font-family:inherit;padding:0}
.done{display:none}
.done.on{display:block}
@media(prefers-color-scheme:dark){
  :root{--ink:#f2f4f7;--muted:#a2abb6;--line:#2a2f37;--bg:#111318}
  .shot,.price{background:#171a20}
  .card{background:#1a1d24}
  .card input{background:#111318;color:#f2f4f7;border-color:#333a44}
}
"""

JS = """
(function(){
  var ARM = document.body.dataset.arm;
  var SID = (function(){
    try{ var k='pvm_sid'; var v=sessionStorage.getItem(k);
         if(!v){ v=Math.random().toString(36).slice(2)+Date.now().toString(36);
                 sessionStorage.setItem(k,v); } return v; }
    catch(e){ return 'nostore'; }
  })();
  var sent = {};

  // First-party only. No third-party pixel, no cookies, no Google Analytics (§26).
  function ev(name, extra){
    if(sent[name] && name!=='E7') return;
    sent[name] = true;
    var body = JSON.stringify({arm:ARM, sid:SID, event:name,
                               t:Date.now(), extra:extra||null});
    try{
      if(navigator.sendBeacon){
        navigator.sendBeacon('/event', new Blob([body],{type:'application/json'}));
      }else{
        fetch('/event',{method:'POST',headers:{'Content-Type':'application/json'},
                        body:body, keepalive:true});
      }
    }catch(e){}
    if(location.protocol==='file:') console.log('[event]', name, extra||'');
  }

  ev('E2');  // landing page view

  // E3 — scrolled at least halfway: did the pitch hold attention at all
  window.addEventListener('scroll', function(){
    var h = document.body.scrollHeight - window.innerHeight;
    if(h>0 && (window.scrollY/h) >= 0.5) ev('E3');
  }, {passive:true});

  // E4 — the price block actually entered the viewport: they saw a real number
  var price = document.getElementById('price');
  if(price && 'IntersectionObserver' in window){
    new IntersectionObserver(function(es){
      es.forEach(function(e){ if(e.isIntersecting) ev('E4'); });
    },{threshold:.5}).observe(price);
  }

  var veil = document.getElementById('veil');
  var form = document.getElementById('form');
  var done = document.getElementById('done');

  // E5 — PRIMARY METRIC. The deliberate act taken after seeing a real price.
  Array.prototype.forEach.call(document.querySelectorAll('[data-buy]'), function(b){
    b.addEventListener('click', function(){
      ev('E5', {where: b.dataset.buy});
      veil.classList.add('on');            // disclosure, immediately
      // Lock the page behind it. The disclosure must not be scrollable past.
      document.body.style.overflow = 'hidden';
      ev('E6');
      var i = document.getElementById('email'); if(i) i.focus();
    });
  });

  if(form){
    form.addEventListener('submit', function(e){
      e.preventDefault();
      var email = document.getElementById('email').value.trim();
      if(!email) return;
      ev('E7', {email: email});            // intent survived the truth
      form.style.display='none';
      done.classList.add('on');
    });
  }

  var no = document.getElementById('nothanks');
  if(no) no.addEventListener('click', function(){
    ev('E8');                              // wanted the product, not the waitlist
    veil.classList.remove('on');
    document.body.style.overflow = '';
  });
})();
"""


def shot(arm_key):
    """A plain description of what the app does. No fake screenshots, no invented
    review quotes, no fabricated ratings."""
    if arm_key == "a":
        return ("<b>Documents</b> 604 &nbsp;·&nbsp; <b>People</b> 1,529 &nbsp;·&nbsp; "
                "<b>Screenshots</b> 2,487<br><b>Places</b> 4,256 &nbsp;·&nbsp; "
                "<b>Travel</b> 877 &nbsp;·&nbsp; <b>Purchases</b> 501<br><br>"
                "Documents → Identity → Passports<br>"
                "Screenshots → Temporary → Pickup Codes<br>"
                "Places → Japan → Tokyo")
    if arm_key == "b":
        return ("<b>284</b> expired verification &amp; pickup codes &nbsp;—&nbsp; cleared<br>"
                "<b>1,203</b> duplicate downloads &nbsp;—&nbsp; cleared<br>"
                "<b>641</b> near-identical burst frames &nbsp;—&nbsp; best kept<br><br>"
                "<b>Protected:</b> 12 documents · 3 IDs · 1 contract<br>"
                "Everything removed is recoverable for 30 days.<br><br>"
                "<b>23 items</b> need you.")
    return ("<b>4.2 GB</b> in duplicate photos<br>"
            "<b>1.8 GB</b> in old screenshots<br>"
            "<b>6.1 GB</b> in large videos<br><br>"
            "Review and clear in a few taps.")


def page(key, a):
    pts = "".join(f'<div class="pt"><h3>{h}</h3><p>{b}</p></div>' for h, b in a["points"])
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{a['title']} — Personal Visual Memory</title>
<meta name="description" content="{a['sub']}">
<meta name="robots" content="noindex">
<style>{CSS}</style></head>
<body data-arm="{key}">
<div class="wrap">

<header>
  <h1>{a['h1']}</h1>
  <div class="sub">{a['sub']}</div>
  <p class="lede">{a['lede']}</p>
  <div class="cta-block">
    <button class="btn" data-buy="hero">Get it <span class="p">— {PRICE}</span></button>
    <div class="terms">One-off. No subscription.</div>
  </div>
</header>

<div class="shot">
  <div class="bar"><i></i><i></i><i></i></div>
  <div class="body">{shot(key)}</div>
</div>

<div class="points">{pts}</div>

<div class="price" id="price">
  <div class="amt">{PRICE}<span>, once</span></div>
  <ul>
    <li>No subscription. No weekly charge.</li>
    <li>No ads, ever.</li>
    <li>Runs on your iPhone. Nothing is uploaded.</li>
  </ul>
  <div class="cta-block">
    <button class="btn" data-buy="price">Get it <span class="p">— {PRICE}</span></button>
  </div>
</div>

<footer>
  Personal Visual Memory runs entirely on your device. We do not upload your photos,
  and we do not sell data to anyone.<br>
  <a href="mailto:hello@example.invalid">Contact</a>
</footer>
</div>

<!-- Fires the instant anyone commits. Full screen, before anything else happens. -->
<div class="veil" id="veil">
  <div class="card">
    <div id="form-wrap">
      <h2>We are not charging you.</h2>
      <p><b>Personal Visual Memory is not out yet.</b> You just helped us prove people
      want it — that is genuinely what we needed to know.</p>
      <p>Leave your email and you will get first access at <b>{PRICE}</b>, locked in.
      Nothing to pay now, and we will only email you about this.</p>
      <form id="form" class="row" novalidate>
        <input id="email" type="email" placeholder="you@example.com" autocomplete="email">
        <button class="btn" type="submit">Lock in {PRICE}</button>
      </form>
      <button class="no" id="nothanks">No thanks</button>
    </div>
    <div class="done" id="done">
      <h2>Done.</h2>
      <p>You are on the list at <b>{PRICE}</b>. We will email you once — when it is ready.</p>
      <p style="color:#8a8f98;font-size:15px">Thank you. Genuinely: a real click on a real
      price is the only honest way to find out whether this is worth building.</p>
    </div>
  </div>
</div>

<script>{JS}</script>
</body></html>"""


def main():
    for key, a in ARMS.items():
        d = os.path.join(OUT, key)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
            f.write(page(key, a))
        print(f"wrote site/{key}/index.html   {a['rung']}")

    # Integrity check: the arms must differ ONLY in the value proposition.
    # Legitimately arm-specific: header, proof points, the description block, the
    # page title and the meta description. EVERYTHING else — price, CTA mechanics,
    # disclosure wording, instrumentation, footer — must be byte-identical, or the
    # comparison is confounded by something we did not intend to manipulate.
    import re
    def skeleton(k):
        h = open(os.path.join(OUT, k, "index.html"), encoding="utf-8").read()
        h = re.sub(r'<header>.*?</header>', '', h, flags=re.S)
        h = re.sub(r'<div class="points">.*?</div>\s*<div class="price"',
                   '<div class="price"', h, flags=re.S)
        h = re.sub(r'<div class="shot">.*?</div>\s*</div>', '', h, flags=re.S)
        h = re.sub(r'<title>.*?</title>', '', h, flags=re.S)
        h = re.sub(r'<meta name="description"[^>]*>', '', h)
        return re.sub(r'data-arm="."', '', h)
    base = skeleton("a")
    same = all(skeleton(k) == base for k in ARMS)
    print(f"\nprice block, CTA mechanics, disclosure and instrumentation identical "
          f"across arms: {same}")
    if not same:
        raise SystemExit("aborting: arms differ outside the manipulated dimension")


if __name__ == "__main__":
    main()
