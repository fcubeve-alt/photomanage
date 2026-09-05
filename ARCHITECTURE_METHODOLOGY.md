# ARCHITECTURE METHODOLOGY — Information-Change-First / Minimum Necessary Inference
Canonical digest of **PVME 底层方法论更新 v1.0** (2026-08-24), incorporated as a long-term
engineering constraint.
Source: `10_SOURCE_DOCS/PVME_Information_Change_First_Methodology_Update_v1.0.docx`
Plain text: `10_SOURCE_DOCS/_extracted_text/L1B_INFORMATION_CHANGE_FIRST_METHODOLOGY_v1.0.txt`

> **Authority: L1-B.** Binds all architecture and model decisions from now on. It does
> **not** change product goals, the Visual Library taxonomy, risk grading, lifecycle
> management, natural-language retrieval, or the current P0 / Tier 0 execution order —
> the source document says so explicitly. Where it appears to conflict with
> Constitution v1.3 product truth, the Constitution wins and the conflict is escalated.

---

## The one-line constraint

> **Do not understand everything. Understand what changed, and spend intelligence only
> where it creates new memory.**

A library does not re-read every book each day. It maintains an index and opens the
few relevant volumes when there is an actual reason to.

---

## Principle 1 — Minimum Necessary Inference (MNI)

Facing 30,000–100,000 photos plus video, **any architecture that hands every asset to a
heavy model is wrong by construction** — not merely slow.

**Mandatory processing order:**

```
Cheap Signals → Candidate Reduction → Selective Intelligence → Structured Memory
```

**Cheap signals come first, always:** metadata (time, place, file attributes, source) ·
hash / perceptual hash · OCR · lightweight embeddings · Apple Vision and system-native
capability · the existing PVME index and taxonomy · video codec, scene-change and
motion/change information.

Only when cheap signals **cannot reliably complete the task** may the expensive layer be
entered.

**Worked example — "find the black charger I photographed a while ago":**
- ✅ `50,000 photos → cheap retrieval → 30–50 candidates → stronger grounding model → 1–3 results`
- ❌ `50,000 photos → heavy VLM × 50,000`

**Apple Native, Gemma, Mage, LocateAnything, or any future model must serve this
architecture. The architecture never bends to accommodate a model.**

## Principle 2 — Information-Change-First (ICF)

Process **new information**, not every asset mechanically. Before any expensive
inference, answer three questions in order:

1. **What changed?**
2. **What is actually new?**
3. **Does this new information deserve deeper inference?**

**Photos.** Near-duplicates, same-moment bursts, and re-downloads of identical content
must **not** be treated as independent new objects requiring full re-understanding.
Identify duplication, near-duplication, same-scene and degree-of-change with cheap
signals *first*, then decide whether deeper classification, grounding or same-entity
resolution is warranted.

**Video** — the most important new application of this methodology.

- ❌ **Forbidden by default:** `Video → sample every N frames → run a full visual model on each frame`
- ✅ **Required direction:** `Video → codec / metadata → scene & change detection → meaningful segments / representative frames → selective visual understanding → Video Memory Record`

What PVME stores is **not** a pile of AI-analysed frames. It is the *new information
this video contributes to the user's personal visual memory*:

```
Date: 2026-08-20
Place: Tokyo Hotel
Person: Anna
Object: Red suitcase
Event: Packing
Relevant segment: 00:17–00:24
Representative frames: 4
```

Video records enter the **same Unified Visual Memory Graph** as photos. "Where did my
red suitcase last appear?" must return photos *and* video, ideally jumping straight to
the timestamp.

## Unified architecture

```
Camera Roll
  ↓ Visual Ingestion Layer
  ↓ Cheap Understanding Layer   metadata / hash / OCR / embedding / Apple Vision
  ↓                             / codec / scene & change detection
  ↓ Candidate Reduction
  ↓ Selective Intelligence Layer   stronger models ONLY when necessary
  ↓ Unified Visual Memory Graph
  ↓ Documents / People / Objects / Clothing / Places / Travel / Purchases / Work /
  ↓ Screenshots / Timeline …
  ↓ Visual Library Entry + Natural Language Entry
```

**Relation to Constitution §25.** The 8-layer Progressive Intelligence Pipeline already
orders cheap→expensive and is not contradicted. What this adds is **Candidate Reduction
as an explicit, named stage** — §25 has no equivalent — and the requirement that video
flow through the same pipeline into the same graph.

## Model selection — restated

The question is no longer *"which model is strongest?"* but:

> **What is the minimum computational capability required to complete this specific
> visual task?**

| If … | Then |
|---|---|
| rules / metadata solve it | **use no AI** |
| a light model solves it | **do not use a large model** |
| Apple Native solves it | **add no additional model** |
| benchmark proves a definite capability gap | *only then* research Gemma / Mage / LocateAnything / grounding-mini candidates |

Any added model must demonstrate that its accuracy or capability gain **outweighs**
binary size, memory, battery, thermal cost and engineering complexity.

**LocateAnything, Mage and Gemma remain Candidate / Benchmark status. None is a product
dependency.**

---

# CONFLICT REVIEW — current work vs this methodology

Performed 2026-08-24 per §7 of the source: *review and **mark** designs that clearly
violate these principles; **do not refactor working results without reason**.*
Findings are **marked, not fixed** — except where noted, and nothing here changes the
T0-A/B/C/D execution order.

## ✅ Already compliant — built this way before the methodology arrived

| Existing design | Principle |
|---|---|
| **T0-A scope lock: Layer 1 + Layer 2 only**, never the full 8-layer pipeline | MNI |
| **C-1 gated OCR** — OCR runs only on assets that cheap signals flag as text-bearing, never all 100k. `ocr_attempted` vs `ocr_gated_out` recorded | MNI, textbook case |
| **C-2 thumbnails only, `isNetworkAccessAllowed = false`** — never fetches originals | MNI |
| **Apple-native `VNGenerateImageFeaturePrintRequest`** for L2 — zero bundled model, zero binary growth | Model selection |
| **P-04** — Apple-native first; no heavy model without benchmark evidence; tightened to *beat a shipped 262 MB baseline* | Model selection |
| **`LibraryChangeTracker`** — persistent change token + observer; processes only inserted/updated/deleted | **ICF, implemented at the index layer** |
| Constitution §8 Equivalence Margin, §9 classify-before-clean | ICF on photos |

The A4 change-tracking work is Information-Change-First in everything but name.

## ⚠️ MARKED VIOLATIONS

### V-1 · The cheap signal is computed, then not used to skip the expensive one
`AssetIndexer` computes `dHash` for every asset, `IndexStore` stores it and even builds
`idx_dhash` — and **nothing ever queries it**. Every asset then pays for gated OCR *and*
a feature-print embedding, including exact re-downloads of an identical image.

This is the precise shape MNI forbids: the cheap signal that would authorise skipping is
paid for and discarded.

**Consequence for Tier 0 — this is the part that matters.** The A1 throughput number
would measure a *naive* design, not the intended architecture. Spec §5 already states
the opposite intent: *"These are engineering decisions the harness must embody, so the
benchmark measures the intended design rather than a naive baseline."* A real camera
roll contains meaningful exact-duplicate and burst volume, so the measured cost per
asset would be **pessimistic** — and A1 could fail a budget the intended design meets.

**Recommendation: fix before the device campaign, not after.** It is the same class of
decision as C-1 gating, which is already in the spec, and no data has been collected yet
so there is nothing to invalidate. **Owner decision** — flagged rather than done,
because §7 says not to refactor without reason and this is a judgement call about what
"the intended design" means. Cost: a lookup before the OCR/embedding stage.

### V-2 · Video is absent from the entire Tier 0 apparatus
- The harness records `mediaType` and otherwise treats every asset as an image;
  `AssetIndexer` requests a thumbnail even for videos.
- The test library generator emits **only JPEGs** — zero video.
- The taxonomy has no video concept.

**Consequence.** T0-A can say nothing about video, while real 100k libraries contain a
lot of it and video is exactly where naive per-frame processing explodes. **A1 measured
on a photos-only library is therefore an optimistic bound, not a representative one.**

**Do not fix in Tier 0.** Building the Video Memory Record pipeline now would be Tier
1/2 work and the source document forbids entering it early. **Record as a stated
limitation of the T0-A result** so no one reads a photos-only A1 PASS as a claim about
mixed libraries.

### V-3 · Deep inference on every asset in the cold path
The cold run applies the same treatment to every asset with no "is this new information?"
question. Defensible for a *first* index — everything genuinely is new — but the cold
path still ignores intra-run duplication (V-1), and the design should be explicit about
which parts are cold-path exemptions rather than leaving it implicit.

### V-4 · Tier 1 / Tier 2 plans assume classify-everything
`T1-A` (taxonomy coverage), `T2-E` (multi-signal classification) are specified as
whole-library classification exercises. Under MNI they should be scoped as *classify
what needs classifying, after candidate reduction*. **Marked for the Tier 1 protocol —
not changed now**, since Tier 1 is locked and rewriting a locked protocol would violate
the Execution Index.

## REQUIRED FUTURE CHANGES — the register

| ID | Change | When | Blocking? |
|---|---|---|---|
| **FC-1** | Skip OCR + embedding on exact-duplicate `dHash` hits; link to the existing record instead. Record `dedup_skipped` in the CSV. **Precondition FC-1a below is mandatory** | **Before the T0-A device campaign** (Owner decision) | No |
| **FC-2** | State "photos only, no video" as an explicit limitation in the T0-A result and in `TIER0_GO_NO_GO.md` | When T0-A is written up | No |
| **FC-3** | Add video to the Tier 1 test corpus and define the Video Memory Record schema | **Tier 1** | Yes, for any video claim |
| **FC-4** | Implement `codec / metadata → scene & change detection → segments → selective understanding → Video Memory Record` | **Tier 2** | Yes |
| **FC-5** | Video records enter the same Unified Visual Memory Graph; retrieval returns photos *and* video with timestamp jump | **Tier 2** | Yes |
| **FC-6** | Re-scope T1-A and T2-E around candidate reduction rather than whole-library classification | **Tier 1 protocol authoring** | No |
| **FC-7** | Make Candidate Reduction an explicit named stage in the architecture, alongside Constitution §25 | Tier 1 architecture | No |

### FC-1a · `dHash == 0` is not a duplicate — measured, not theorised
Found on 2026-09-06 by the new iOS Simulator test step, before any device existed.

`Layer1.dHash` sets a bit only where a pixel is **brighter than the one to its right**.
An image with no bright-to-dark horizontal step — a dark-to-bright gradient, a flat
colour, a uniform-row image — therefore hashes to **0**. So does every image the
function fails on: `guard let cg = image.cgImage else { return 0 }`.

**Two unrelated photos, and every hash failure, share the value 0.** This is harmless
today precisely *because* nothing reads `dhash` back — that is MNI-1. It becomes a data
loss the moment FC-1 lands and a dHash match authorises skipping OCR and the embedding:
unrelated assets would be linked as duplicates of each other, and a failed hash would
look like a confident match.

**FC-1 may not be implemented without, at minimum:** a distinct sentinel for "not
hashed" separate from the legitimate hash 0, and a confirming comparison (byte size, or
a second signal) before any skip is taken. Locked in as
`Layer1SignalsTests.testAWholeClassOfImagesHashesToZero`, so FC-1 cannot ship without
meeting it.

## What did NOT change
Product goals · Visual Library taxonomy · risk grading R0–R6 · lifecycle management ·
natural-language retrieval · **the T0-A / T0-B / T0-C / T0-D execution order** · the
Tier 0 gate logic. No work was stopped, reversed or redone. No Tier 1/Tier 2 development
was started.
