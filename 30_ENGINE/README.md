# 30_ENGINE — the classification engine

The part of the product that decides **what a photo is**, where it belongs, how sure it
is, and what may safely be done about it.

Built 2026-09-06 on Owner instruction (DEC-028). Everything before this in the
repository was validation instrumentation; PF-11 put it plainly — the classifier, the
taxonomy engine and the risk policy engine were at zero lines and were the hard part.
This is that part.

## What it is

```
pvm/signals.py     the input contract — everything the classifier may see, and nothing
                   a real iPhone cannot produce
pvm/taxonomy.py    bridge to the canonical tree in 20_TIER0/study_assets/taxonomy.py.
                   One tree, many consumers. A rule that invents a category is refused
pvm/rules.py       the rule set as data: text patterns, scene mappings, weights
pvm/context.py     library-level facts no single photo contains — home, trips, people
pvm/classifier.py  the escalation policy: cheapest signal first, stop when the answer
                   stops changing
pvm/verdict.py     assignments, evidence, confidence. An assignment with no evidence
                   cannot be constructed
pvm/risk.py        R0-R6 and what each one permits. There is no DELETE action
pvm/dedup.py       duplicates, and the four things that only look like duplicates
pvm/catalog.py     SQLite: checkpointing, incrementality, stored explanations
pvm/pipeline.py    context -> classify -> relate and score, resumable throughout
pvm/schedule.py    paced ingestion: a free breadth pass, then depth over days (DEC-029)
pvm/deltas.py      change-driven processing for video and sequences (DEC-029)
pvm/cli.py         plan / classify / tree / why / review
eval/              measurement against the 10,000-asset labelled library
tests/             55 behavioural tests, including every safety red line
```

## Run it

```bash
python -m pvm.cli plan     --assets 100000
python -m pvm.cli classify --library ../20_TIER0/study_assets/library/manifest.json \
                           --catalog out.sqlite --budget metadata   # breadth pass
python -m pvm.cli classify --library ../20_TIER0/study_assets/library/manifest.json \
                           --catalog out.sqlite                     # depth pass
python -m pvm.cli tree   --catalog out.sqlite
python -m pvm.cli why    --catalog out.sqlite --asset A00001
python -m pvm.cli review --catalog out.sqlite

python -m unittest discover -s tests
python eval/evaluate.py --library ../20_TIER0/study_assets/library/manifest.json
```

No third-party dependencies. Python 3.11+.

## Breadth is free; depth is what you pace

The single most useful thing the measurements said. A breadth pass reads PhotoKit
metadata only and decodes **no pixels** — 0.17 ms/asset in a real run, so a 100k library
has Timeline, Places, Travel and Screenshots **in under 30 seconds**. The depth pass
(OCR, embedding, faces) is 105–154 ms/asset, three orders of magnitude more.

So a large library is never "wait N days for your library". It is "your library is here
in a minute, and it gets deeper while you use the phone" — and `pvm plan` produces the
options a user is offered rather than choosing for them.

The thing this does *not* fix, and the reason it is written down here: pacing makes
survivability **more** critical, not less. A ninety-minute run that loses its place
costs ninety minutes; a twenty-two-day plan that loses its place never finishes. The
resume cursor is the load-bearing part of the whole design.

## The five decisions worth arguing with

**1 · Escalate, then stop.** Signals are ordered by what they cost — metadata, hash,
scene, faces, OCR — and the engine buys the next one only while the answer is still
moving. On the test library 74% of assets are answered by metadata alone. `tier_used`
and `tiers_spent` are reported separately on purpose: a photo answered by its GPS fix
still cost a face pass if one ran, and only the second number shows up in a battery
graph.

**2 · Return the depth the evidence supports, never a leaf.** "CONTRACT — PAGE 1 OF 4"
proves it is a contract and not which kind, so the answer is `Documents > Contracts`
and it stops there. A tree full of confidently wrong leaves is worse than one that
admits what it knows, because the user cannot tell the two apart until they go looking
for something and it is not there.

**3 · Location is context, not identity.** A passport photographed at the kitchen table
is a passport. This one was learned the hard way: with the location rule running first,
a GPS fix filed every photographed document under `Places > United Kingdom > London` at
0.91 confidence, the escalation policy saw a settled answer, and the OCR pass that
would have recognised the passport never ran. Nine of nine identity documents lost,
silently, each with a plausible wrong answer in its place. The ordering is now
load-bearing and `LocationIsContextNotIdentity` in the tests exists to keep it that way.

**4 · Only byte-identity is allowed to be confident.** Everything else — a burst, a
near-identical page, the same card photographed six months later — produces a
*relation*, which is useful for browsing and is never on its own a reason to remove
anything. The four cases that are not duplicates and look exactly like them each have
a named test.

**5 · The engine cannot delete.** `Action` has no DELETE member. The strongest thing it
can produce is a confirmable, reversible proposal, and `Proposal.__post_init__` refuses
to construct one that removes a person or a document, one that is irreversible, or one
with no explanation attached. These are constructor checks rather than conventions
because conventions are what erode at 2am.

## Measured

Against `20_TIER0/study_assets/library/manifest.json` — 10,000 labelled assets. Read
the evaluation's own first section before the numbers: 4,155 of those assets carry a
leaf the generator chose with `random.choice`, and scoring them would report coin flips
as classifier error forever, so they are counted and not scored.

| | |
|---|--:|
| macro F1, root level, scored roots | **0.998** |
| leaf exact, where the label is derivable (n=5,845) | **99.8%** |
| wrong root | **0** |
| answered by metadata alone | 73.3% |
| classification throughput (decision logic only) | ~5,000 assets/s |
| safety red lines, audited against the written catalogue | 4 / 4 PASS |
| metadata-only ablation, macro F1 | 0.569 |

The ablation is the interesting column: free signals alone get you 0.569, and the
expensive tiers are what buy the remaining 0.43.

## What it does not do yet

- **No video *classification*.** The canonical tree has eleven roots and none is Video
  (FC-2), so video assets are noted as having nowhere to go rather than filed as photos.
  What does exist is `deltas.py`: change-driven frame selection, which saves 61–88% of
  the per-frame work depending on motion, compares against the last processed keyframe
  rather than the previous frame (the naive version processes 1 frame of 600 on a slow
  pan and never sees the scene change), and refuses to skip on a failed hash, on
  document content, or for more than 30 frames in a row.
- **OPEN-3: dHash on real footage is unverified.** The frame-selection decisions are
  measured on synthetic hash sequences and the cost saving is arithmetic from measured
  stage costs. Whether `dHash` separates scenes as cleanly through motion blur, exposure
  shifts and compression is the assumption the whole saving rests on. It needs real
  video, not a device.
- **Objects, Clothing, Downloads are untested against real data.** Their rules exist and
  are unit-tested, but the corpus carries no scene labels and no provenance, so nothing
  here measures them. That is a missing signal, not a missing rule, and inventing either
  from the label would have measured only the adapter.
- **Entity resolution is a relation, not a resolver.** The engine can say "these two are
  the same subject on different occasions". It does not yet maintain an entity across a
  library, which is Tier 1-A.
- **It is Python.** The product is iOS. This is the reference implementation: the rules
  are data, the schema is plain SQLite matching `IndexStore.swift`, and the escalation
  policy is the part that ports. Nothing here ships as-is.
