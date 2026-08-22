# TEST LIBRARY — SPEC, SOURCING AND PREP
Companion to `generate_test_library.py`. Implements T0-B protocol §5.

---

## 1. What the generator produces

```bash
python generate_test_library.py --out ./library --count 10000
```

| Output | Contents |
|---|---|
| `library/manifest.json` | ground truth for every asset — category path, capture time, place, people, same-entity / same-moment group, task target, hard-negative flag |
| `library/images/*.jpg` | placeholder JPEGs with EXIF `DateTimeOriginal` and GPS written |

Verified composition at 10,000 assets — within **0.3 pp** of §5 on every class:

| Class | Actual | Spec |
|---|---|---|
| Ordinary photography | 34.7% | 35% |
| Screenshots | 24.9% | 25% |
| People & family | 15.3% | 15% |
| Bursts | 8.0% | 8% |
| Documents & IDs | 6.0% | 6% |
| Purchases | 5.0% | 5% |
| Downloaded / memes | 4.0% | 4% |
| Objects | 2.1% | 2% |

Deterministic — `SEED = 20260822`. Re-running gives the identical library, so results stay comparable across participants and across devices.

---

## 2. The foreground / background split — the core design decision

**136 foreground assets** (`requires_real_imagery: true`) carry every task target and every hard negative. A participant has to tell these apart **by looking at them**.

**9,864 background assets** supply library scale and search noise. Nobody is asked to find these, so synthetic is fine.

### ⚠️ Placeholders are not study-ready

The generator draws labelled coloured rectangles. Those are for exercising the pipeline — import, EXIF parsing, counts, scroll behaviour, indexing throughput. **Running the study on placeholders would measure whether people can read labels, not whether they can find their photos.**

Every placeholder for a foreground asset is stamped `PLACEHOLDER — REPLACE WITH REAL IMAGERY BEFORE THE STUDY` so this cannot pass unnoticed.

---

## 3. Sourcing real imagery (136 assets, ~2–3 hours of prep)

Each foreground asset carries a `source_query` field. Three routes, in order of preference:

**A · Open-licence stock** (Unsplash / Pexels / Openverse). Good for: Tokyo scenes, portraits, objects, meals. Check the licence permits this use; record the source list alongside the study report.

**B · Staged captures.** Best for documents, receipts, screenshots and bursts, because those need to be internally consistent — the same contract across four pages, the same bicycle in three settings, the same person on one trip.
- **Documents: use SPECIMEN documents only.** Never a real ID, passport, licence or signed contract, whether the Owner's or anyone else's. Search "specimen"/"sample" document images, or produce obvious mock-ups. This is a privacy line, and it also keeps the study distributable.
- **Bursts:** take one real burst of 8 on a phone, then a second burst of 7 where frame 5 has a clearly different expression — that frame is the §8 hard negative.

**C · The Owner's own photos**, if de-identified and the Owner consents to strangers seeing them. Most realistic; the highest privacy cost. Not recommended for documents.

### Consistency requirements that decide whether tasks work at all

| Requirement | Why |
|---|---|
| **T2:** exactly ONE PERSON_B photo in a white top on the Tokyo trip | If there are two, the task has no single right answer |
| **T2 distractors:** same person, same trip, other clothing (14 of them) | Otherwise "find the person" solves it without the attribute |
| **T3 distractors:** 5 other receipts | Otherwise "the only receipt" is the answer |
| **T6 distractors:** 11 pickup codes in other weeks | Forces a genuinely time-scoped answer |
| **T5:** the same recognisable bicycle in 3 different settings | Same-entity across time only works if it is visibly the same object |
| **Contract:** 4 pages that look alike but read differently | The §9 hard negative |
| **Meme:** 4 byte-identical copies | Use `copy` — do not re-encode, or they stop being exact duplicates |

---

## 4. Loading onto the device

1. Generate the library and replace the 136 foreground placeholders.
2. Verify EXIF survived — `DateTimeOriginal` and GPS must be present, or Timeline and Places views are empty in **both** arms and two tasks become untestable.
3. Import to the loaner iPhone (Finder sync, AirDrop in batches, or iCloud from a dedicated test Apple ID).
4. **Let Apple Photos finish indexing.** People must be populated. Leave the device idle and plugged in — this can take hours on 10k assets.
5. Confirm the on-device asset count matches `manifest.json`.
6. Load the prototype catalogue from the same manifest.
7. Launch both apps once, then close them, so first-open is genuinely first-open.

> Step 4 is the fair-configuration rule (PF-07). An Apple Photos instance that has not finished indexing People would hand us a rigged win on T2 and T4. **A rigged win is worse than a loss.**

---

## 5. Task answer key

Read `manifest.json` → `task_targets`. IDs are stable for a given seed and count.

| Task | Target | Notes |
|---|---|---|
| T1 | 2 assets — ID card front + back | Plus one re-shot front months later: same entity, **not** a duplicate |
| T2 | 1 asset — PERSON_B, white top, Tokyo | 14 same-person distractors on the same trip |
| T3 | 1 asset — headphones receipt | 5 distractor receipts; related warranty card + order screenshot share an entity group |
| T4 | PERSON_A across 3 years | 28 solo + 6 group shots; group shots test completeness |
| T5 | Bicycle, 3 occasions | 5 object distractors |
| T6 | Pickup code, ~7 weeks ago | 11 distractors in other weeks, 9 verification codes |
| T7 | Burst of 8 at the beach | Performed **manually** in both arms — we measure today's cost, we do not build the fix |
| — | Passport | Target of the pre-tap predictability question (protocol §7 step 4) |

**9 hard negatives** are listed in `manifest.json` → `hard_negatives`.

---

## 6. Also usable for T0-A

The same generator can pad a device library for the device benchmark — but **the harness has its own on-device generator** (`SyntheticCorpus.swift`), which is the right tool there: it inserts via `PHAssetCreationRequest` with no transfer step, and tracks its own asset ids so cleanup can never touch anything pre-existing (DEC-009).

Use this Python generator when you need **ground truth**; use the on-device one when you need **scale**.

---

## 7. Files

| File | Purpose |
|---|---|
| `generate_test_library.py` | manifest + placeholder generator |
| `build_prototype.py` | the T0-B Visual Library prototype **and** the four T0-D header variants of the same home |
| `prototype/index.html` | home — first-run result in a 3-line header, then the library |
| `prototype/<path>.html` | every taxonomy node to leaf level (82 pages, 3 levels deep) |
| `prototype/ledger_v1..v4.html` | the four T0-D variants; the library section is byte-identical across all four |
| `FACILITATOR_SCRIPT.md` | verbatim session script, both studies, with the rota |
| `SCORING_T0B_RETRIEVAL.md` | T0-B sheet |
| `SCORING_T0D_AUTONOMY.md` | T0-D sheet — **separate by design** |

Everything is generated from a single script on purpose: a between-subjects manipulation is only valid if the variants are identical except for the manipulated dimension. Hand-editing HTML would let wording and spacing drift and silently confound the result. Verified after each build that the library section is byte-identical across all four variants. If counts or structure change, edit `TAXONOMY` / `SUMMARY` in the script and regenerate — never edit the HTML by hand.

**Superseded 2026-08-22 (DEC-017):** `build_ledger_variants.py` and its `ledger/` output were removed. The ledger is no longer a standalone dashboard — it is the header and lower section of the Visual Library home, so it is generated by `build_prototype.py`.
