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
pvm/cli.py         classify / tree / why / review
eval/              measurement against the 10,000-asset labelled library
tests/             55 behavioural tests, including every safety red line
```

## Run it

```bash
python -m pvm.cli classify --library ../20_TIER0/study_assets/library/manifest.json \
                           --catalog out.sqlite
python -m pvm.cli tree   --catalog out.sqlite
python -m pvm.cli why    --catalog out.sqlite --asset A00001
python -m pvm.cli review --catalog out.sqlite

python -m unittest discover -s tests
python eval/evaluate.py --library ../20_TIER0/study_assets/library/manifest.json
```

No third-party dependencies. Python 3.11+.

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
| answered by metadata alone | 74.1% |
| classification throughput (decision logic only) | ~5,700 assets/s |
| safety red lines, audited against the written catalogue | 4 / 4 PASS |
| metadata-only ablation, macro F1 | 0.569 |

The ablation is the interesting column: free signals alone get you 0.569, and the
expensive tiers are what buy the remaining 0.43.

## What it does not do yet

- **No video.** The canonical tree has eleven roots and none is Video (FC-2). Video
  assets are noted as having nowhere to go rather than filed as photos.
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
