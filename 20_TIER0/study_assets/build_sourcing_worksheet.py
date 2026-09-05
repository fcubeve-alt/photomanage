#!/usr/bin/env python3
"""
Turn the manifest's 136 foreground assets into an executable sourcing worksheet.

    python build_sourcing_worksheet.py

Writes FOREGROUND_SOURCING_WORKSHEET.md.

Why this exists. TEST_LIBRARY_SPEC.md section 3 budgets 2-3 hours to source the 136
foreground images, but the constraints that decide whether a task is answerable at
all - one white top and only one, four contract pages that look alike, the same
bicycle three times, four byte-identical memes - are spread across a prose table
while the assets themselves live in a 10,000-entry JSON file. Anyone doing the work
would have to hold both in their head at once, and a single miss silently destroys
a task rather than failing loudly.

So the worksheet is generated from the manifest, never hand-written (DEC-019). If
the library is regenerated, this is regenerated with it and cannot drift.
"""
import io, json, os, sys
from collections import defaultdict

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, "library", "manifest.json")
OUT = os.path.join(HERE, "FOREGROUND_SOURCING_WORKSHEET.md")

# Route per TEST_LIBRARY_SPEC.md section 3. A = open-licence stock, B = staged
# capture, C = the Owner's own photos (highest privacy cost, never for documents).
ROUTE = {
    "document_id": ("B", "SPECIMEN documents only. Never a real ID, passport, licence or signed contract — anyone's. This is a privacy line, and it also keeps the study distributable."),
    "purchase": ("B", "Staged. Receipts and warranty cards must be internally consistent with the order they belong to."),
    "screenshot": ("B", "Staged on a phone. Screenshots must look like screenshots — status bar, real app chrome, correct aspect ratio."),
    "burst": ("B", "Must actually be shot as a burst. A burst faked from one frame will not carry the near-duplicate signal the task depends on."),
    "people_family": ("B/C", "Needs consenting people, photographed across one staged trip. Route C (the Owner's own, de-identified) is the most realistic library and the highest privacy cost — whoever appears must consent to strangers seeing the images."),
    "ordinary_photography": ("A", "Open-licence stock is fine — Unsplash / Pexels / Openverse. Record the licence and the URL."),
    "object": ("A", "Open-licence stock, EXCEPT where a same-entity group demands the identical object in several settings — that has to be staged."),
    "downloaded_meme": ("A", "Grab once, then copy the file for the duplicates. Re-encoding destroys the exact-duplicate property (section 8)."),
}

# The section 3 constraint table, restated as counts this script can check. Copying
# the numbers out of the spec by hand would produce a worksheet that stays confident
# while the library moves underneath it — so each row names a population, and the
# expected size is verified against the manifest before anything is written.
#
#   (task, count_of, expected, sentence)
CONSTRAINTS = [
    ("T2", lambda a: a.get("task_target") == "T2", 1,
     "Exactly ONE photo of Ben in a white top on the Tokyo trip. If there are two, the task has no single right answer."),
    ("T2", lambda a: a["category_path"] == "People > Ben" and a.get("place") == "tokyo", 15,
     "1 answer + 14 distractors: same person, same trip, other clothing. Otherwise “find the person” solves it without the attribute."),
    ("T3", lambda a: a["category_path"] == "Purchases > Receipts", 6,
     "1 answer + 5 other receipts. Otherwise “the only receipt in the library” is the answer."),
    ("T5", lambda a: a.get("same_entity_group") == "ENTITY_BICYCLE", 3,
     "The SAME recognisable bicycle in 3 different settings. Same-entity across time only works if it is visibly the same object."),
    ("T6", lambda a: a["category_path"] == "Screenshots > Temporary > Pickup Codes", 12,
     "1 answer + 11 pickup codes in other weeks, or the answer is not genuinely time-scoped."),
    ("HARD-NEG", lambda a: a.get("same_entity_group") == "ENTITY_CONTRACT_TENANCY", 4,
     "The tenancy contract: 4 pages that look alike but read differently (section 9)."),
    ("HARD-NEG", lambda a: a.get("same_entity_group") == "ENTITY_MEME_DUP", 4,
     "The meme: 4 byte-identical copies. Use a file copy, do not re-encode (section 8)."),
    ("HARD-NEG", lambda a: a.get("same_moment_group") == "MOMENT_BURST_HARDNEG", 7,
     "The second burst: 7 frames where frame 5 has a clearly different expression. That frame is the section 8 hard negative."),
]


def verify(fg):
    """Abort rather than emit a worksheet the library contradicts."""
    wrong = []
    for task, pred, expected, sentence in CONSTRAINTS:
        got = sum(1 for a in fg if pred(a))
        if got != expected:
            wrong.append("  {} — expected {}, manifest has {}: {}"
                         .format(task, expected, got, sentence))
    if wrong:
        sys.exit("the manifest no longer matches the section 3 constraint table:\n"
                 + "\n".join(wrong)
                 + "\n\nEither the library changed and TEST_LIBRARY_SPEC.md section 3 "
                   "needs updating, or the library is wrong. Do not source images "
                   "against a worksheet that disagrees with the library.")
    return len(CONSTRAINTS)

GROUP_NOTES = {
    "ENTITY_CONTRACT_TENANCY": "Four pages of ONE tenancy contract. They must look alike and read differently.",
    "ENTITY_MEME_DUP": "Byte-identical copies of one image. Copy the file, never re-encode.",
    "ENTITY_ID_CARD": "One specimen ID card; both sides required, and grouping must not hide either.",
    "ENTITY_BICYCLE": "One visibly identical bicycle in three different settings.",
    "ENTITY_HEADPHONES": "One identical pair of headphones in two contexts.",
    "MOMENT_BURST_T7": "One real burst of 8 frames, same moment.",
    "MOMENT_BURST_HARDNEG": "A second burst of 7 where frame 5 has a clearly different expression — that frame is the hard negative.",
}


def main():
    m = json.load(io.open(MANIFEST, encoding="utf-8"))
    fg = [a for a in m["assets"] if a.get("requires_real_imagery")]
    if not fg:
        sys.exit("no foreground assets in the manifest — has it been regenerated?")
    checked = verify(fg)

    by_cat = defaultdict(list)
    for a in fg:
        by_cat[a["category"]].append(a)

    groups = defaultdict(list)
    for a in fg:
        for key in ("same_entity_group", "same_moment_group"):
            if a.get(key):
                groups[a[key]].append(a["id"])

    L = []
    w = L.append
    w("# FOREGROUND SOURCING WORKSHEET")
    w("")
    w("**Generated by `build_sourcing_worksheet.py` from `library/manifest.json` "
      "(seed {}). Do not hand-edit — regenerate.**".format(m.get("seed")))
    w("")
    w("{} assets need real imagery. The other {:,} are synthetic filler for scale and "
      "noise and need nothing.".format(len(fg), m["total_assets"] - len(fg)))
    w("")
    w("These carry **every task target and every hard negative** in T0-B and T0-D. The "
      "placeholders currently in the library are stamped so they cannot be used in a real "
      "session by accident — that stamp is a guard, not an inconvenience, and it stays "
      "until an asset is genuinely replaced.")
    w("")
    w("> **This worksheet is preparation, not permission.** Running the studies still "
      "needs **HG-4** (n ≥ 15 external participants). Sourcing the images needs no gate "
      "except the two judgement calls below.")
    w("")

    w("## Owner decisions needed before starting")
    w("")
    w("1. **Route for the {} `people_family` assets.** Route B (staged, with consenting "
      "people) or Route C (the Owner's own photos, de-identified). C gives the most "
      "realistic library at the highest privacy cost — external strangers will look at "
      "these images in a study session. B costs more time and needs at least two people "
      "available across a staged trip.".format(len(by_cat.get("people_family", []))))
    w("2. **Confirm the specimen-document line.** Every `document_id` asset is sourced as "
      "a SPECIMEN or an obvious mock-up. No real identity document belonging to the Owner "
      "or to anyone else, at any point, for any reason.")
    w("")

    w("## Constraints that decide whether a task is answerable at all")
    w("")
    w("A miss here does not produce a worse result. It produces a task with no correct "
      "answer, and that is not visible until a participant is sitting in front of it.")
    w("")
    w("Every count below is **verified against the manifest** each time this file is "
      "generated. If the library and this table ever disagree, the generator refuses to "
      "write rather than hand you a confident, wrong worksheet.")
    w("")
    w("| Task | Population | Expected | Constraint |")
    w("|---|---|---|---|")
    for task, pred, expected, text in CONSTRAINTS:
        w("| **{}** | {} | {} | {} |".format(
            task, sum(1 for a in fg if pred(a)), expected, text))
    w("")

    w("## Grouped assets — source these together or not at all")
    w("")
    w("| Group | Assets | What must hold |")
    w("|---|---|---|")
    for g in sorted(groups):
        ids = ", ".join("`{}`".format(i) for i in sorted(groups[g]))
        w("| `{}` | {} — {} | {} |".format(
            g, len(groups[g]), ids,
            GROUP_NOTES.get(g, "Same entity or moment across all listed assets.")))
    w("")

    w("## Work list by route")
    w("")
    order = sorted(by_cat, key=lambda c: (ROUTE.get(c, ("Z", ""))[0], -len(by_cat[c])))
    for cat in order:
        route, guidance = ROUTE.get(
            cat, ("?", "No route assigned — decide before sourcing."))
        items = sorted(by_cat[cat], key=lambda a: a["id"])
        w("### {} · {} assets · **Route {}**".format(cat, len(items), route))
        w("")
        w(guidance)
        w("")
        w("| ID | Where it files | Captured | What to source | Flags | Note |")
        w("|---|---|---|---|---|---|")
        for a in items:
            flags = []
            if a.get("task_target"):
                flags.append("**{}**".format(a["task_target"]))
            if a.get("hard_negative"):
                flags.append("HARD-NEG")
            if a.get("same_entity_group"):
                flags.append("grp `{}`".format(a["same_entity_group"]))
            if a.get("same_moment_group"):
                flags.append("grp `{}`".format(a["same_moment_group"]))
            if a.get("exact_duplicate_of"):
                flags.append("copy of `{}`".format(a["exact_duplicate_of"]))
            w("| `{}` | {} | {} | {} | {} | {} |".format(
                a["id"], a["category_path"], a["captured_at"][:10],
                a.get("source_query") or "—",
                " · ".join(flags) or "—",
                a.get("note") or ""))
        w("")

    w("## Recording the sources")
    w("")
    w("Keep a `library/SOURCES.csv` beside the images: "
      "`asset_id,route,url_or_capture,licence,captured_by,consent`. Write it as the "
      "images are gathered, not afterwards from memory. Two things depend on it — the "
      "licence claim in the study report, and the ability to say precisely whose face is "
      "in the library if consent is ever withdrawn.")
    w("")

    io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(L))
    print("wrote {}  —  {} assets, {} categories, {} groups that must stay consistent, "
          "{} constraints verified against the manifest"
          .format(os.path.relpath(OUT, HERE), len(fg), len(by_cat), len(groups), checked))


if __name__ == "__main__":
    main()
