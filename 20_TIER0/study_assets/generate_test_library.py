#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T0-B / T0-D standardised test library generator.

Builds the library specified in T0B_RETRIEVAL_ENTRY_STUDY_PROTOCOL.md §5:
composition, deliberate hard negatives, and full ground truth for every task target.

TWO CLASSES OF ASSET — this distinction is the whole design:

  FOREGROUND (~120 assets, `requires_real_imagery: true`)
      Every task target and every hard negative. A participant must be able to tell
      these apart by LOOKING at them. Synthetic placeholders are NOT adequate here —
      see TEST_LIBRARY_SPEC.md "Sourcing real imagery".

  BACKGROUND (~9,880 assets, `requires_real_imagery: false`)
      Filler that supplies library scale and search noise. Synthetic is fine; nobody
      is asked to find these.

Placeholders generated here are for exercising the pipeline (import, EXIF, counts,
scroll performance). Running the study on placeholders alone would measure whether
people can read labels, not whether they can find their photos.

Usage:
    python generate_test_library.py --out ./library --count 10000
    python generate_test_library.py --manifest-only        # ground truth, no pixels
"""

import argparse, json, os, random, hashlib, shutil
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

SEED = 20260822
random.seed(SEED)

# --- §5 composition -------------------------------------------------------------
COMPOSITION = [
    ("ordinary_photography", 0.35, "Photography"),
    ("screenshot",           0.25, "Screenshots"),
    ("people_family",        0.15, "People"),
    ("burst",                0.08, "Photography/Burst"),
    ("document_id",          0.06, "Documents"),
    ("purchase",             0.05, "Purchases"),
    ("downloaded_meme",      0.04, "Downloads"),
    ("object",               0.02, "Objects"),
]

PEOPLE = ["PERSON_A", "PERSON_B", "PERSON_C", "PERSON_D"]

PLACES = {
    "home":   ("United Kingdom", "London",  51.5074,  -0.1278),
    "tokyo":  ("Japan",          "Tokyo",   35.6762, 139.6503),
    "coast":  ("United Kingdom", "Brighton",50.8225,  -0.1372),
    "office": ("United Kingdom", "London",  51.5155,  -0.0922),
}

NOW = datetime(2026, 8, 22, 12, 0, 0)
TOKYO_TRIP = (datetime(2025, 4, 11), datetime(2025, 4, 19))   # "last year" for T2


def d(days_ago, hour=None, minute=None):
    t = NOW - timedelta(days=days_ago)
    return t.replace(hour=hour if hour is not None else random.randint(7, 22),
                     minute=minute if minute is not None else random.randint(0, 59),
                     second=random.randint(0, 59))


class Builder:
    def __init__(self):
        self.assets = []
        self.n = 0

    def add(self, **kw):
        self.n += 1
        a = {
            "id": f"A{self.n:05d}",
            "category": kw.get("category"),
            "category_path": kw.get("category_path"),
            "captured_at": kw["captured_at"].isoformat(),
            "place": kw.get("place"),
            "people": kw.get("people", []),
            "same_entity_group": kw.get("same_entity_group"),
            "same_moment_group": kw.get("same_moment_group"),
            "requires_real_imagery": kw.get("requires_real_imagery", False),
            "source_query": kw.get("source_query"),
            "task_target": kw.get("task_target"),
            "hard_negative": kw.get("hard_negative"),
            "is_screenshot": kw.get("is_screenshot", False),
            "exact_duplicate_of": kw.get("exact_duplicate_of"),
            "note": kw.get("note"),
            "placeholder_text": kw.get("placeholder_text", ""),
        }
        self.assets.append(a)
        return a

    # ---------------- FOREGROUND: task targets and hard negatives ----------------

    def foreground(self):
        # ---- T1 · ID card front and back (same real entity, both must stay findable)
        for side in ("front", "back"):
            self.add(category="document_id", category_path=f"Documents/Identity/ID Card/{side.title()}",
                     captured_at=d(430, 14, 3), place="home",
                     same_entity_group="ENTITY_ID_CARD", requires_real_imagery=True,
                     source_query=f"specimen national id card {side}, sample document",
                     task_target="T1", placeholder_text=f"ID CARD — {side.upper()}",
                     note="T1 answer. Both sides required; grouping must not hide either.")

        # A second, LATER capture of the SAME id card — §9 Same Entity across time.
        self.add(category="document_id", category_path="Documents/Identity/ID Card/Front",
                 captured_at=d(90, 9, 12), place="home",
                 same_entity_group="ENTITY_ID_CARD", requires_real_imagery=True,
                 source_query="specimen national id card front, sample document, different lighting",
                 hard_negative="same-entity-later-capture", placeholder_text="ID CARD — FRONT (re-shot)",
                 note="Same physical card months later. Same Entity, NOT a duplicate to delete.")

        # ---- Passport / driver licence (used by the §7 predictability question)
        self.add(category="document_id", category_path="Documents/Identity/Passport",
                 captured_at=d(510, 11, 20), place="home", requires_real_imagery=True,
                 source_query="specimen passport photo page, sample document",
                 task_target="PASSPORT_PREDICTION", placeholder_text="PASSPORT",
                 note="Target of the pre-tap predictability question (protocol §7 step 4).")
        self.add(category="document_id", category_path="Documents/Identity/Driver Licence",
                 captured_at=d(505, 11, 25), place="home", requires_real_imagery=True,
                 source_query="specimen driving licence card, sample document",
                 placeholder_text="DRIVER LICENCE")

        # ---- HARD NEGATIVE · 4-page contract: near-identical, different content
        for page in range(1, 5):
            self.add(category="document_id", category_path="Documents/Legal/Contract",
                     captured_at=d(200, 16, 40 + page), place="office",
                     same_entity_group="ENTITY_CONTRACT_TENANCY", requires_real_imagery=True,
                     source_query=f"printed contract page {page} of 4, dense text, plain paper",
                     hard_negative="near-identical-different-content",
                     placeholder_text=f"CONTRACT — PAGE {page} OF 4",
                     note="Pages look alike and MUST NOT be treated as duplicates (§9).")

        # ---- T3 · receipt for a specific purchase
        self.add(category="purchase", category_path="Purchases/Receipts",
                 captured_at=d(160, 13, 5), place="home", requires_real_imagery=True,
                 source_query="paper till receipt for headphones, electronics store",
                 task_target="T3", placeholder_text="RECEIPT — HEADPHONES £129.00",
                 note="T3 answer.")
        for i, q in enumerate(["supermarket till receipt", "restaurant bill receipt",
                               "pharmacy receipt", "taxi receipt", "hardware store receipt"]):
            self.add(category="purchase", category_path="Purchases/Receipts",
                     captured_at=d(150 - i * 9, 18, 12), place="home",
                     requires_real_imagery=True, source_query=q,
                     placeholder_text=f"RECEIPT — {q.split()[0].upper()}",
                     note="Distractor receipt; T3 must not be findable by 'only one receipt exists'.")
        self.add(category="purchase", category_path="Purchases/Warranty",
                 captured_at=d(159, 13, 9), place="home", requires_real_imagery=True,
                 source_query="product warranty card", placeholder_text="WARRANTY CARD — HEADPHONES",
                 same_entity_group="ENTITY_HEADPHONES")
        self.add(category="purchase", category_path="Purchases/Orders",
                 captured_at=d(163, 20, 41), place="home", requires_real_imagery=True,
                 is_screenshot=True, source_query="order confirmation email screenshot",
                 placeholder_text="ORDER CONFIRMATION — HEADPHONES",
                 same_entity_group="ENTITY_HEADPHONES")

        # ---- T2 · person in a white top, Tokyo trip, last year
        trip_days = (TOKYO_TRIP[1] - TOKYO_TRIP[0]).days
        self.add(category="people_family", category_path="People/PERSON_B",
                 captured_at=TOKYO_TRIP[0] + timedelta(days=3, hours=10),
                 place="tokyo", people=["PERSON_B"], requires_real_imagery=True,
                 source_query="woman in white top standing in tokyo street, daytime",
                 task_target="T2", placeholder_text="PERSON_B · WHITE TOP · TOKYO",
                 note="T2 answer. Must be the ONLY white-top PERSON_B shot on the trip.")
        # Trip distractors: same person, same trip, other clothing.
        for i in range(14):
            self.add(category="people_family", category_path="People/PERSON_B",
                     captured_at=TOKYO_TRIP[0] + timedelta(days=random.randint(0, trip_days),
                                                           hours=random.randint(8, 20)),
                     place="tokyo", people=["PERSON_B"], requires_real_imagery=True,
                     source_query=f"woman in {random.choice(['blue jacket','red dress','black coat','green shirt'])} in tokyo",
                     placeholder_text="PERSON_B · TOKYO")
        for i in range(22):
            self.add(category="ordinary_photography", category_path="Photography/Travel",
                     captured_at=TOKYO_TRIP[0] + timedelta(days=random.randint(0, trip_days),
                                                           hours=random.randint(8, 21)),
                     place="tokyo", requires_real_imagery=True,
                     source_query="tokyo street scene, temple, ramen, neon signage",
                     placeholder_text="TOKYO SCENE")

        # ---- T4 · one person across three years
        for year_offset, count in ((0, 9), (1, 11), (2, 8)):
            for i in range(count):
                self.add(category="people_family", category_path="People/PERSON_A",
                         captured_at=d(365 * year_offset + random.randint(5, 350)),
                         place=random.choice(["home", "coast", "office"]),
                         people=["PERSON_A"], requires_real_imagery=True,
                         source_query="same man portrait, casual, varied settings",
                         task_target="T4" if year_offset == 0 and i == 0 else None,
                         placeholder_text=f"PERSON_A · {2026 - year_offset}")
        # Group shots — PERSON_A present but not alone.
        for i in range(6):
            self.add(category="people_family", category_path="People/Groups",
                     captured_at=d(random.randint(30, 900)), place="home",
                     people=["PERSON_A", random.choice(["PERSON_C", "PERSON_D"])],
                     requires_real_imagery=True, source_query="two people together, casual photo",
                     placeholder_text="GROUP · PERSON_A + OTHER",
                     note="T4 completeness check: must surface in a PERSON_A view.")

        # ---- T5 · same object on three separate occasions
        for i, (days, place) in enumerate([(700, "home"), (330, "office"), (45, "coast")]):
            self.add(category="object", category_path="Objects/Bicycle",
                     captured_at=d(days, 15, 30), place=place,
                     same_entity_group="ENTITY_BICYCLE", requires_real_imagery=True,
                     source_query="same blue bicycle, different background and angle",
                     task_target="T5" if i == 0 else None,
                     placeholder_text=f"BICYCLE · OCCASION {i+1}")
        for i in range(5):
            self.add(category="object", category_path="Objects/Other",
                     captured_at=d(random.randint(60, 800)), place="home",
                     requires_real_imagery=True,
                     source_query=random.choice(["kettle", "office chair", "houseplant",
                                                 "laptop", "washing machine"]),
                     placeholder_text="OBJECT DISTRACTOR")

        # ---- T6 · pickup-code screenshot from a given week
        target_day = 47
        self.add(category="screenshot", category_path="Screenshots/Temporary/Pickup Code",
                 captured_at=d(target_day, 9, 14), place="home", is_screenshot=True,
                 requires_real_imagery=True, source_query="parcel pickup code sms screenshot",
                 task_target="T6", placeholder_text="PICKUP CODE 4417 — LOCKER B12",
                 note="T6 answer. Week of " + d(target_day).strftime("%Y-%m-%d") + ".")
        for i in range(11):
            self.add(category="screenshot", category_path="Screenshots/Temporary/Pickup Code",
                     captured_at=d(target_day + random.choice([-40, -25, 25, 60, 120]), 10, 5),
                     place="home", is_screenshot=True, requires_real_imagery=True,
                     source_query="parcel pickup code sms screenshot",
                     placeholder_text=f"PICKUP CODE {1000+i*137}",
                     note="Distractor: same type, different week. Forces a time-scoped answer.")
        for i in range(9):
            self.add(category="screenshot", category_path="Screenshots/Temporary/Verification Code",
                     captured_at=d(random.randint(20, 400), 12, 0), place="home",
                     is_screenshot=True, requires_real_imagery=True,
                     source_query="one time verification code sms screenshot",
                     placeholder_text=f"VERIFICATION CODE {100000+i*7919}",
                     note="Expired temporary content — R1 material for the T0-D ledger.")

        # ---- T7 · burst of 8, and the HARD NEGATIVE burst
        for i in range(8):
            self.add(category="burst", category_path="Photography/Burst",
                     captured_at=d(120, 16, 22) + timedelta(seconds=i),
                     place="coast", people=["PERSON_C"],
                     same_moment_group="MOMENT_BURST_T7", requires_real_imagery=True,
                     source_query="near identical burst frame, person on beach, slight pose variation",
                     task_target="T7" if i == 0 else None,
                     placeholder_text=f"BURST T7 · FRAME {i+1}/8")
        for i in range(7):
            different = (i == 4)
            self.add(category="burst", category_path="Photography/Burst",
                     captured_at=d(260, 13, 8) + timedelta(seconds=i),
                     place="home", people=["PERSON_D"],
                     same_moment_group="MOMENT_BURST_HARDNEG", requires_real_imagery=True,
                     source_query=("same burst but subject laughing with eyes closed, clearly different"
                                   if different else "near identical burst frame, neutral expression"),
                     hard_negative="different-expression-in-burst" if different else None,
                     placeholder_text=f"BURST HN · FRAME {i+1}/7" + (" · DIFFERENT EXPRESSION" if different else ""),
                     note="Frame 5 is genuinely different and MUST NOT be silently collapsed (§8)."
                          if different else None)

        # ---- HARD NEGATIVE · one image downloaded four times, byte-identical
        first = self.add(category="downloaded_meme", category_path="Downloads/Memes",
                         captured_at=d(310, 21, 3), place=None, requires_real_imagery=True,
                         source_query="a single reaction meme image",
                         same_entity_group="ENTITY_MEME_DUP",
                         placeholder_text="MEME (original download)")
        for i in range(3):
            self.add(category="downloaded_meme", category_path="Downloads/Memes",
                     captured_at=d(310 - (i + 1) * 12, 21, 30), place=None,
                     requires_real_imagery=True, source_query="identical copy of the same meme",
                     same_entity_group="ENTITY_MEME_DUP", exact_duplicate_of=first["id"],
                     hard_negative="exact-duplicate-safe-to-clean",
                     placeholder_text="MEME (identical re-download)",
                     note="Byte-identical. R0 — may be handled aggressively (§9).")

    # ---------------- BACKGROUND: filler for scale and search noise ----------------

    def background(self, target_total):
        remaining = target_total - self.n
        if remaining <= 0:
            return
        buckets = []
        for cat, share, path in COMPOSITION:
            buckets.extend([(cat, path)] * max(1, int(round(share * remaining))))
        random.shuffle(buckets)
        for cat, path in buckets[:remaining]:
            place = random.choice(list(PLACES.keys()) + [None])
            people = [random.choice(PEOPLE)] if cat == "people_family" else []
            self.add(category=cat, category_path=path,
                     captured_at=d(random.randint(1, 1500)),
                     place=place, people=people,
                     is_screenshot=(cat == "screenshot"),
                     requires_real_imagery=False,
                     placeholder_text=cat.replace("_", " ").upper())


# ---------------------------------------------------------------------------------
# Placeholder rendering — pipeline exercise only, NOT study-ready imagery.
# ---------------------------------------------------------------------------------

def font(size):
    for name in ("arial.ttf", "DejaVuSans.ttf", "Helvetica.ttc"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def render(asset, path, size=(1512, 1134)):
    """Deterministic per-id colour so distinct assets look distinct while scrolling."""
    h = int(hashlib.md5(asset["id"].encode()).hexdigest()[:6], 16)
    if asset["is_screenshot"]:
        size = (1170, 2532)
        bg, fg = (250, 250, 252), (20, 20, 24)
    else:
        bg = ((h >> 16) % 160 + 60, (h >> 8) % 160 + 60, h % 160 + 60)
        fg = (255, 255, 255)
    img = Image.new("RGB", size, bg)
    dr = ImageDraw.Draw(img)
    if not asset["is_screenshot"]:
        for i in range(0, size[1], 90):
            dr.line([(0, i), (size[0], i + 45)], fill=(bg[0] // 2, bg[1] // 2, bg[2] // 2), width=7)
    f1, f2 = font(46), font(30)
    dr.text((60, 60), asset["placeholder_text"] or asset["category"], font=f1, fill=fg)
    dr.text((60, 130), asset["id"], font=f2, fill=fg)
    dr.text((60, 175), asset["category_path"] or "", font=f2, fill=fg)
    dr.text((60, 220), asset["captured_at"][:10], font=f2, fill=fg)
    if asset["place"]:
        dr.text((60, 265), PLACES[asset["place"]][1], font=f2, fill=fg)
    if asset["requires_real_imagery"]:
        dr.text((60, size[1] - 90), "PLACEHOLDER — REPLACE WITH REAL IMAGERY BEFORE THE STUDY",
                font=f2, fill=(255, 90, 90))

    exif = Image.Exif()
    dt = datetime.fromisoformat(asset["captured_at"]).strftime("%Y:%m:%d %H:%M:%S")
    exif[306] = dt            # DateTime
    exif[36867] = dt          # DateTimeOriginal
    exif[36868] = dt          # DateTimeDigitized
    exif[271] = "PVMBench"
    exif[272] = "TestLibrary"
    if asset["place"]:
        _, _, lat, lon = PLACES[asset["place"]]
        gps = {
            1: "N" if lat >= 0 else "S",
            2: (int(abs(lat)), 1, int(abs(lat) % 1 * 60), 1, 0, 1),
            3: "E" if lon >= 0 else "W",
            4: (int(abs(lon)), 1, int(abs(lon) % 1 * 60), 1, 0, 1),
        }
        try:
            exif.get_ifd(0x8825).update(gps)
        except Exception:
            pass
    img.save(path, "JPEG", quality=62, exif=exif)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="./library")
    ap.add_argument("--count", type=int, default=10000)
    ap.add_argument("--manifest-only", action="store_true")
    ap.add_argument("--foreground-only", action="store_true",
                    help="render pixels for the ~120 task-critical assets only")
    args = ap.parse_args()

    b = Builder()
    b.foreground()
    fg_count = b.n
    b.background(args.count)

    os.makedirs(args.out, exist_ok=True)
    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "seed": SEED,
        "spec": "T0B_RETRIEVAL_ENTRY_STUDY_PROTOCOL.md §5",
        "total_assets": b.n,
        "foreground_assets": fg_count,
        "background_assets": b.n - fg_count,
        "places": {k: {"country": v[0], "city": v[1], "lat": v[2], "lon": v[3]}
                   for k, v in PLACES.items()},
        "tokyo_trip": [TOKYO_TRIP[0].date().isoformat(), TOKYO_TRIP[1].date().isoformat()],
        "task_targets": {},
        "hard_negatives": [],
        "assets": b.assets,
    }
    for a in b.assets:
        if a["task_target"]:
            manifest["task_targets"].setdefault(a["task_target"], []).append(a["id"])
        if a["hard_negative"]:
            manifest["hard_negatives"].append({"id": a["id"], "kind": a["hard_negative"],
                                               "note": a["note"]})

    with open(os.path.join(args.out, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1, ensure_ascii=False)

    print(f"assets: {b.n}  (foreground {fg_count}, background {b.n - fg_count})")
    print(f"task targets: { {k: len(v) for k, v in manifest['task_targets'].items()} }")
    print(f"hard negatives: {len(manifest['hard_negatives'])}")

    if args.manifest_only:
        print("manifest only — no pixels rendered")
        return

    img_dir = os.path.join(args.out, "images")
    os.makedirs(img_dir, exist_ok=True)
    todo = [a for a in b.assets if a["requires_real_imagery"]] if args.foreground_only else b.assets
    for i, a in enumerate(todo, 1):
        render(a, os.path.join(img_dir, f"{a['id']}.jpg"))
        if i % 500 == 0:
            print(f"  rendered {i}/{len(todo)}")
    print(f"rendered {len(todo)} placeholder images -> {img_dir}")
    print("\nREMINDER: placeholders exercise the pipeline. They are NOT study-ready.")
    print("Replace every requires_real_imagery asset before running with participants.")


if __name__ == "__main__":
    main()
