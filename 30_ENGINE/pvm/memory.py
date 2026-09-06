# -*- coding: utf-8 -*-
"""
THE VISUAL MEMORY GRAPH — §2 "Remember", and the largest gap the audit found.

Constitution §2 lists ten steps the product *is*, and Remember is one of them:
*"把照片变成现实人物、物品、地点、文件、购买和事件的证据"*. §15 builds every later
service on top of it — Wardrobe, Travel Memory, Purchase & Warranty, Home/Object
Memory, Document Memory — and L1-B §4 says the thing a video must ultimately leave
behind is not analysed frames but *"这个视频对用户个人视觉记忆真正贡献的新信息"*.

Until now the catalogue filed photos. Filing is not remembering. A filing system can
tell you which shelf a photo is on; a memory can answer **"我的红色行李箱最后在哪里
出现过？"** — which is the question L1-B uses as its worked example, and which needs
entities that persist across assets rather than labels attached to each one.

So this module turns classifications into **entities** (a person, a place, an object, a
document, a purchase, an event) and **observations** (that entity, seen in that asset,
at that time, in that place, for this reason). The graph is the two together.

Three boundaries that are not negotiable:

* **Every entity and every observation carries its evidence.** An entity nobody can
  justify is a claim, and the red line says a claim must be able to explain itself.
* **§11: an inferred fact declares that it is inferred.** Confidence and source travel
  with every observation; a place derived from a neighbouring photo never looks like a
  GPS fix.
* **§16 and §15: no sensitive inference, and no casual relationship inference.** The
  graph records that two people appeared together and how often. It does not conclude
  what they are to each other, and it never characterises anyone.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from . import rules, taxonomy
from .context import LibraryContext
from .signals import AssetSignals, Tier
from .verdict import Classification, Evidence, combine


class EntityKind(str, Enum):
    PERSON = "person"
    PLACE = "place"
    OBJECT = "object"
    DOCUMENT = "document"
    PURCHASE = "purchase"
    EVENT = "event"


@dataclass
class Entity:
    """A thing in the world that the library has evidence for."""
    entity_id: str
    kind: EntityKind
    name: str
    evidence: List[Evidence] = field(default_factory=list)
    # Where the catalogue files this thing, when the two differ. The shelf is coarse
    # ("Objects > Other"); the entity is specific ("Suitcase"). Keeping both means the
    # memory can answer a question the shelf cannot, without pretending the shelf is
    # finer than it is.
    category_path: Optional[str] = None

    def __post_init__(self):
        if not self.evidence:
            raise ValueError(
                f"entity {self.entity_id!r} has no evidence. An entity nobody can "
                "justify is a claim, and a claim has to be able to explain itself."
            )

    @property
    def confidence(self) -> float:
        return combine(e.weight for e in self.evidence)

    def why(self) -> str:
        return "; ".join(e.reason for e in sorted(self.evidence, key=lambda e: -e.weight))


@dataclass
class Observation:
    """This entity, seen in this asset. The unit the whole graph is made of."""
    entity_id: str
    asset_id: str
    when: Optional[datetime]
    place: Optional[str]
    confidence: float
    reason: str
    # §11: where each half of the belief came from, kept apart because they can differ.
    # `source` is how the *entity* was identified — a named face, a read of the page.
    # `place_source` is how the *location* was established — a GPS fix is measured, a
    # location borrowed from neighbouring photos is inferred.
    #
    # They must be separate. A face recognised with certainty in a photo whose location
    # was guessed from the photo before it produces a sentence that is half fact and
    # half inference, and reporting the whole thing as measured is precisely the §11
    # failure: "Anna was in London on the 18th" stated as if the camera had recorded it.
    source: str = "measured"
    place_source: str = "measured"
    # Video only: the seconds within the asset this observation covers (L1-B §4).
    segment: Optional[Tuple[float, float]] = None
    # Set to the anchor asset when this sighting repeats another from the same moment.
    # A flag, never a deletion: the observation stays, and a view may fold it.
    repeats: Optional[str] = None

    @property
    def is_inferred(self) -> bool:
        """True when any part of this sighting was derived rather than recorded."""
        return self.source != "measured" or self.place_source != "measured"

    @property
    def place_is_inferred(self) -> bool:
        return self.place is not None and self.place_source != "measured"


@dataclass
class MemoryGraph:
    entities: Dict[str, Entity] = field(default_factory=dict)
    observations: List[Observation] = field(default_factory=list)

    # -- building ----------------------------------------------------------
    def add_entity(self, entity: Entity) -> Entity:
        existing = self.entities.get(entity.entity_id)
        if existing is None:
            self.entities[entity.entity_id] = entity
            return entity
        for e in entity.evidence:
            if e.reason not in {x.reason for x in existing.evidence}:
                existing.evidence.append(e)
        return existing

    def observe(self, observation: Observation) -> None:
        self.observations.append(observation)

    # -- queries -----------------------------------------------------------
    def history(self, entity_id: str) -> List[Observation]:
        """Every time this entity was seen, oldest first. Observations with no date
        come last rather than being dropped — an undated sighting is still a sighting."""
        seen = [o for o in self.observations if o.entity_id == entity_id]
        dated = sorted((o for o in seen if o.when), key=lambda o: o.when)
        return dated + [o for o in seen if not o.when]

    def last_seen(self, entity_id: str) -> Optional[Observation]:
        dated = [o for o in self.observations if o.entity_id == entity_id and o.when]
        return max(dated, key=lambda o: o.when) if dated else None

    def find(self, text: str, kind: Optional[EntityKind] = None) -> List[Entity]:
        """Match the user's words against entity names.

        Two passes, in order of how much they claim. A substring hit is close to what
        was asked for. A word hit — "red suitcase" finding *Suitcase* — is looser, and
        the caller has to be able to tell the difference, which is why the two passes
        are not merged: `answer_where_last_seen` says out loud when it only matched
        part of the question.
        """
        needle = text.strip().lower()
        pool = [e for e in self.entities.values() if kind is None or e.kind == kind]
        exact = [e for e in pool if needle in e.name.lower()]
        if exact:
            return sorted(exact, key=lambda e: -e.confidence)
        words = {w for w in needle.replace("'s", "").split() if len(w) > 2}
        loose = [e for e in pool
                 if words & {w.lower() for w in e.name.split()}]
        return sorted(loose, key=lambda e: -e.confidence)

    def co_occurring(self, entity_id: str,
                     kind: Optional[EntityKind] = None) -> List[Tuple[str, int]]:
        """Which entities show up in the same assets, and how often.

        §15 says relationship views must not infer sensitive relations casually. This
        returns a count of shared appearances and nothing more — an observation, not a
        conclusion about what two people are to each other.
        """
        mine = {o.asset_id for o in self.observations if o.entity_id == entity_id}
        counts: Counter = Counter()
        for o in self.observations:
            if o.entity_id == entity_id or o.asset_id not in mine:
                continue
            other = self.entities.get(o.entity_id)
            if kind is not None and (other is None or other.kind != kind):
                continue
            counts[o.entity_id] += 1
        return counts.most_common()

    def answer_where_last_seen(self, text: str) -> str:
        """L1-B's own worked example — *"我的红色行李箱最后在哪里出现过？"* — answered
        in the user's words, with the uncertainty in the answer rather than behind it.

        Three things this refuses to hide:

        * §11: an inferred place is described as inferred, never as a fix.
        * A **category-level** entity is not an instance. The library recognises
          suitcases; it cannot yet tell your red one from any other, because
          per-category entity resolution (§24 Gate 2) is not built. So when the
          question asked for more than the name could match, the answer says which
          part of it went unanswered instead of quietly dropping it.
        * An entity with no dated sighting has no "last", and says so.
        """
        matches = self.find(text)
        if not matches:
            return f"Nothing in the library is recorded as “{text}”."
        entity = matches[0]
        observation = self.last_seen(entity.entity_id)
        if observation is None:
            return (f"{entity.name} is in the library, but none of those photos carry "
                    "a date, so there is no “last”.")

        when = observation.when.strftime("%-d %B %Y")
        where = observation.place or "somewhere without a recorded location"
        hedge = " (place inferred from nearby photos, not recorded by the camera)" \
            if observation.place_is_inferred else ""
        answer = (f"{entity.name} was last seen on {when}, {where}{hedge} — "
                  f"{observation.reason}.")

        unmatched = self._unmatched_words(text, entity)
        if unmatched:
            answer += (f" I matched “{entity.name.lower()}” only — nothing in the "
                       f"library distinguishes {' '.join(unmatched)}, so this is the "
                       f"most recent {entity.name.lower()}, which may not be yours.")
        return answer

    @staticmethod
    def _unmatched_words(text: str, entity: Entity) -> List[str]:
        asked = [w for w in text.strip().lower().replace("'s", "").split() if len(w) > 2]
        known = {w.lower() for w in entity.name.split()} | {"the", "my", "your"}
        return [w for w in asked if w not in known]

    def stats(self) -> Dict[str, int]:
        by_kind: Counter = Counter(e.kind.value for e in self.entities.values())
        return {"entities": len(self.entities), "observations": len(self.observations),
                **{f"kind_{k}": v for k, v in sorted(by_kind.items())}}


# --------------------------------------------------------------------------------
# Building the graph from what the classifier already worked out.
#
# L1-B's processing order applies here too: cheap signals first. A person entity comes
# from a named face cluster, not from a model asked "who is this"; a place comes from a
# GPS fix already in the metadata row; an object from a scene label that was going to be
# computed anyway. Nothing in this file spends new intelligence.
# --------------------------------------------------------------------------------

def _slug(text: str) -> str:
    return "".join(c.lower() if c.isalnum() else "-" for c in text).strip("-")


def _singular(leaf: str) -> str:
    """`Passports` -> `Passport`. The shelf is plural because it holds many; the thing
    a single photo shows is one."""
    if leaf.endswith("ies") and len(leaf) > 4:
        return leaf[:-3] + "y"
    if leaf.endswith("s") and not leaf.endswith(("ss", "us")):
        return leaf[:-1]
    return leaf


def _pretty(identifier: str) -> str:
    """`t_shirt` -> `T Shirt`. The recogniser's identifier, in the user's alphabet."""
    return " ".join(part.capitalize() for part in identifier.replace("_", " ").split())


def build(assets: Sequence[AssetSignals],
          classifications: Dict[str, Classification],
          context: Optional[LibraryContext] = None,
          moment_groups: Optional[Iterable[Sequence[str]]] = None) -> MemoryGraph:
    graph = MemoryGraph()
    by_id = {a.asset_id: a for a in assets}

    for asset in assets:
        c = classifications.get(asset.asset_id)
        if c is None:
            continue
        place_name = None
        if asset.place and (asset.place.city or asset.place.country):
            place_name = asset.place.city or asset.place.country
        # Established once, and carried by every observation this asset produces —
        # otherwise a hedge that belongs on the place gets attached to one entity kind
        # and quietly dropped from the rest.
        place_source = "measured" if (asset.geo is None or asset.geo.source == "exif") \
            else "inferred"

        _people(asset, c, place_name, place_source, graph)
        _places(asset, c, place_name, place_source, graph)
        _objects(asset, c, place_name, place_source, graph)
        _documents(asset, c, place_name, place_source, graph)
        _purchases(asset, c, place_name, place_source, graph)

    if context:
        _events(context, by_id, graph)
    if moment_groups:
        _mark_repeats(moment_groups, by_id, graph)
    return graph


def _people(asset, c, place_name, place_source, graph) -> None:
    for face in asset.face_clusters:
        if not face.name:
            continue
        entity_id = f"person:{_slug(face.name)}"
        evidence = Evidence("face_clusters", Tier.FACES, 0.88,
                            f"{face.name} is a face you named")
        graph.add_entity(Entity(entity_id, EntityKind.PERSON, face.name, [evidence]))
        graph.observe(Observation(
            entity_id, asset.asset_id, asset.created_at, place_name, 0.88,
            f"{face.name} was recognised in this photo", place_source=place_source))


def _places(asset, c, place_name, place_source, graph) -> None:
    if not place_name or asset.geo is None:
        return
    entity_id = f"place:{_slug(place_name)}"
    measured = asset.geo.source == "exif"
    weight = 0.9 if measured else 0.6
    evidence = Evidence("geo", Tier.METADATA, weight,
                        f"photos carry a location in {place_name}")
    graph.add_entity(Entity(entity_id, EntityKind.PLACE, place_name, [evidence]))
    graph.observe(Observation(
        entity_id, asset.asset_id, asset.created_at, place_name, weight,
        f"this photo was taken in {place_name}",
        source="measured" if measured else "inferred",
        place_source=place_source))


def _objects(asset, c, place_name, place_source, graph) -> None:
    """Objects are named by what was *recognised*, not by the shelf they land on.

    This is the clearest reason the memory graph has to exist separately from the
    catalogue. `Objects` is not an extensible root, and its leaves are coarse —
    Bicycle, Appliances, Devices, Furniture, Other. A suitcase files under
    `Objects > Other`, and a catalogue that stopped there could only ever answer
    "you have some objects". The memory keeps the word the recogniser actually
    produced, so the entity is *a suitcase* even though the shelf is *Other*.

    One honest limit, stated rather than papered over: this is a **category-level**
    entity. "Suitcase" is every suitcase in the library, not your red one. Telling
    two suitcases apart is per-category entity resolution (§24 Gate 2), which is not
    built — so the graph must not imply an instance it cannot distinguish.
    """
    object_paths = {p for p in c.paths if taxonomy.root_of(p) in ("Objects", "Clothing")}
    if not object_paths:
        return

    named: List[Tuple[str, str, float]] = []      # (name, path, confidence)
    for label in asset.scene_labels:
        path = rules.SCENE_MAP.get(label.identifier)
        if path in object_paths:
            named.append((_pretty(label.identifier), path, min(0.9, label.confidence)))

    # No label explains the path — fall back to the shelf, but never to "Other",
    # which names nothing and would create an entity called "Other".
    if not named:
        for path in sorted(object_paths):
            leaf = path.split(taxonomy.SEP)[-1]
            if leaf not in ("Other",):
                named.append((leaf, path, 0.7))

    for name, path, confidence in named:
        entity_id = f"object:{_slug(name)}"
        evidence = Evidence("scene_labels", Tier.VISUAL, confidence,
                            f"a {name.lower()} was recognised in your photos")
        entity = Entity(entity_id, EntityKind.OBJECT, name, [evidence])
        entity.category_path = path
        graph.add_entity(entity)
        graph.observe(Observation(
            entity_id, asset.asset_id, asset.created_at, place_name, confidence,
            f"a {name.lower()} appears in this photo", place_source=place_source))


def _documents(asset, c, place_name, place_source, graph) -> None:
    for path in c.paths:
        if not path.startswith("Documents"):
            continue
        leaf = path.split(taxonomy.SEP)[-1]
        if leaf in ("Other Documents", "Documents"):
            continue
        name = _singular(leaf)
        entity_id = f"document:{_slug(name)}"
        evidence = Evidence("ocr_text", Tier.TEXT, 0.85,
                            f"the text on the page identifies it as a {name.lower()}")
        entity = Entity(entity_id, EntityKind.DOCUMENT, name, [evidence])
        entity.category_path = path
        graph.add_entity(entity)
        graph.observe(Observation(
            entity_id, asset.asset_id, asset.created_at, place_name, 0.85,
            f"this is a photo of your {name.lower()}", place_source=place_source))


def _purchases(asset, c, place_name, place_source, graph) -> None:
    """§15 Purchase & Warranty Memory: a receipt is evidence about a *thing you own*.

    The item name is read out of the text the OCR already produced — nothing new is
    spent. Where the text does not name an item the entity is simply "Purchase": a
    receipt whose item is unknown is still a receipt, and inventing a product name
    from a total and a date would be exactly the kind of confident guess §11 forbids.
    """
    if not any(p.startswith("Purchases") for p in c.paths):
        return
    name = _purchase_item(asset.ocr_text or "") or "Purchase"
    entity_id = f"purchase:{_slug(name)}"
    evidence = Evidence("ocr_text", Tier.TEXT, 0.75,
                        f"a receipt or order in your library names {name.lower()}")
    graph.add_entity(Entity(entity_id, EntityKind.PURCHASE, name, [evidence]))
    graph.observe(Observation(
        entity_id, asset.asset_id, asset.created_at, place_name, 0.75,
        f"this receipt or order is for {name.lower()}", place_source=place_source))


def _purchase_item(text: str) -> Optional[str]:
    """Pull the item out of a receipt line, or return None rather than a guess.

    A receipt reads `RECEIPT — HEADPHONES £129.00`. The part after the dash is the
    item; the amount is not. A candidate is only accepted when it reads like a name:
    mostly letters, a sane length, and not a code. Order and receipt lines for the
    same thing therefore land on the same entity, which is the point — one purchase,
    two documents.
    """
    for separator in ("—", "–", " - ", ":"):
        if separator not in text:
            continue
        candidate = text.split(separator, 1)[1].strip()
        for currency in ("£", "$", "€", "¥"):
            candidate = candidate.split(currency)[0]
        candidate = candidate.strip(" .,\t")
        letters = sum(c.isalpha() for c in candidate)
        if letters >= 3 and 2 < len(candidate) <= 40 and letters / len(candidate) >= 0.7:
            return candidate.title()
    return None


def _events(context: LibraryContext, by_id, graph) -> None:
    """§11: 时间 + 地点 + 人物 + 内容 can form Event / Trip candidates, and the user
    should never have to create a travel album by hand."""
    for trip in context.trips:
        entity_id = f"event:{_slug(trip.label)}"
        evidence = Evidence("geo+created_at", Tier.METADATA, 0.8,
                            f"{trip.asset_count} photos over "
                            f"{(trip.end - trip.start).days + 1} days away from home")
        graph.add_entity(Entity(entity_id, EntityKind.EVENT, trip.label, [evidence]))
        for asset in by_id.values():
            if asset.created_at and trip.contains(asset.created_at):
                graph.observe(Observation(
                    entity_id, asset.asset_id, asset.created_at,
                    trip.city or trip.country, 0.8,
                    f"taken during {trip.label}"))


def _mark_repeats(groups, by_id, graph) -> None:
    """Mark the sightings that add no new information, without discarding any.

    The distinction that matters here is not the catalogue's. §9 Same Entity tells the
    *catalogue* that several assets show one real thing, so it must relate them and
    delete none of them. It does not tell the *memory* that they are one sighting —
    and for the memory that difference is the whole point. Two photos of Anna eight
    days apart are two facts about where Anna was; collapsing them would delete the
    only thing the graph exists to keep.

    So what gets marked here is narrower: assets from the **same moment** — a burst, a
    second attempt at the same shot. Those genuinely say one thing twice. They are
    still stored, still queryable, still evidence; they are flagged so a view can fold
    them, and `last_seen` is unaffected because it reads time, not this flag.
    """
    for group in groups:
        members = [m for m in group if m in by_id]
        if len(members) < 2:
            continue
        anchor = min(members, key=lambda m: by_id[m].created_at or datetime.max)
        for observation in graph.observations:
            if observation.asset_id in members and observation.asset_id != anchor:
                observation.repeats = anchor


# --------------------------------------------------------------------------------
# Video (L1-B §4). What a video must leave behind is a record, not a pile of frames.
# --------------------------------------------------------------------------------

def format_span(start: float, end: float) -> str:
    """`mm:ss`, with a decimal when the span is short enough that whole seconds would
    hide it.

    A cut lasting two thirds of a second is a real span in the data and rendered
    `00:10–00:10` on screen, which reads as nothing at all. Losing a distinction in the
    formatter after taking the trouble to keep it in the record is the same failure one
    layer out.
    """
    def clock(seconds: float, decimals: int) -> str:
        # Rounded first, then split. Splitting first prints 59.967 as "00:60.0",
        # because the carry happens in the formatter after the minute is already fixed.
        value = round(seconds, decimals)
        minutes = int(value // 60)
        rest = value - minutes * 60
        width = 2 if decimals == 0 else 2 + 1 + decimals
        return f"{minutes:02d}:{rest:0{width}.{decimals}f}"

    decimals = 1 if (end - start) < 10 else 0
    return f"{clock(start, decimals)}\u2013{clock(end, decimals)}"


@dataclass
class VideoMemoryRecord:
    """The shape L1-B §4 specifies, verbatim: Date / Place / Person / Object / Event /
    relevant segment / representative frames."""
    asset_id: str
    date: Optional[datetime]
    place: Optional[str]
    people: List[str]
    objects: List[str]
    event: Optional[str]
    segments: List[Tuple[float, float]]
    representative_frames: List[int]
    evidence: List[Evidence] = field(default_factory=list)

    def summary(self) -> str:
        parts = []
        if self.date:
            parts.append(f"Date: {self.date.strftime('%Y-%m-%d')}")
        if self.place:
            parts.append(f"Place: {self.place}")
        if self.people:
            parts.append("Person: " + ", ".join(self.people))
        if self.objects:
            parts.append("Object: " + ", ".join(self.objects))
        if self.event:
            parts.append(f"Event: {self.event}")
        if self.segments:
            parts.append("Relevant segment: " + ", ".join(
                format_span(a, b) for a, b in self.segments))
        parts.append(f"Representative frames: {len(self.representative_frames)}")
        return "\n".join(parts)


def _segments_by_content(frames: List[int], new_content: set,
                         frame_rate: float) -> List[Tuple[float, float]]:
    """A segment runs from the change that started it to the change that ended it."""
    if not frames or frame_rate <= 0:
        return []
    out: List[Tuple[float, float]] = []
    start = frames[0]
    for index in frames[1:]:
        if index in new_content:
            out.append((start / frame_rate, index / frame_rate))
            start = index
    out.append((start / frame_rate, frames[-1] / frame_rate))
    # A trailing segment that opened on the final frame has nothing after it to close
    # against. It is a moment, not a span, and is dropped rather than reported as a
    # zero-length segment the user would have to interpret.
    return [(a, b) for a, b in out if b > a] or ([] if len(frames) < 2 else out[:1])


def _segments_by_adjacency(frames: List[int], frame_rate: float) -> List[Tuple[float, float]]:
    """For callers holding bare indices with no record of why each was taken: a run of
    consecutive frames is one segment. Correct for that input and no more — the gate's
    own output should go through `_segments_by_content` instead."""
    if not frames or frame_rate <= 0:
        return []
    out: List[Tuple[float, float]] = []
    start = previous = frames[0]
    for index in frames[1:]:
        if index - previous > 1:
            out.append((start / frame_rate, previous / frame_rate))
            start = index
        previous = index
    out.append((start / frame_rate, max(previous, start) / frame_rate))
    return out


def video_record(asset: AssetSignals, keyframe_indices: Sequence[int],
                 frame_rate: float, classification: Optional[Classification] = None,
                 context: Optional[LibraryContext] = None,
                 new_content_at: Optional[Iterable[int]] = None) -> VideoMemoryRecord:
    """Build the record from the frames the delta gate already chose.

    `new_content_at` is the set of keyframes taken because something *changed* — a cut,
    a drift, the first frame. The gate also takes a keyframe every thirty frames in a
    completely static shot, as a periodic re-check, and those two kinds of keyframe mean
    opposite things here. Without the distinction a sixty-second video came back as
    sixty-one zero-length "segments" — a list of instants, which is exactly the pile of
    frames L1-B §4 says must not be what a video leaves behind.

    So a segment opens on new content and is *extended*, not ended, by a heartbeat
    sample. What gets stored is when something was happening.
    """
    frames = sorted(set(keyframe_indices))
    segments = (_segments_by_content(frames, set(new_content_at), frame_rate)
                if new_content_at is not None
                else _segments_by_adjacency(frames, frame_rate))

    place = None
    if asset.place:
        place = asset.place.city or asset.place.country
    event = None
    if context:
        trip = context.trip_for(asset.created_at, asset.geo)
        if trip:
            event = trip.label

    objects: List[str] = []
    if classification:
        for path in classification.paths:
            if taxonomy.root_of(path) in ("Objects", "Clothing"):
                objects.append(path.split(taxonomy.SEP)[-1])

    evidence = [Evidence("deltas", Tier.HASH, 0.7,
                         f"{len(frames)} frames carried new information; the rest repeated them")]
    return VideoMemoryRecord(
        asset_id=asset.asset_id,
        date=asset.created_at,
        place=place,
        people=asset.named_people,
        objects=sorted(set(objects)),
        event=event,
        segments=segments,
        representative_frames=frames,
        evidence=evidence,
    )
