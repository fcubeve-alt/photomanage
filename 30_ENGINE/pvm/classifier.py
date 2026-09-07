# -*- coding: utf-8 -*-
"""
THE CLASSIFIER.

Given one asset's signals and the library it lives in, decide where it belongs, how
sure we are, and why — then stop as early as the evidence allows.

The escalation policy is the part that matters, and it is L1-B (Information-Change-
First / Minimum Necessary Inference) made executable:

    Run the cheapest tier. If the answer is already settled — a leaf, above the
    settle threshold — stop. Otherwise buy the next tier and ask again.

Two consequences worth being explicit about, because both are features:

* Most of a real camera roll settles at Tier.METADATA. A photo with a GPS fix and a
  date is `Places > United Kingdom > London` and `Timeline > 2025` for free. The
  expensive tiers exist for the minority that needs them, and `tier_used` reports
  how large that minority actually is — which is the number that decides whether
  first-run cataloguing is affordable.

* When the evidence supports "Screenshots" and nothing narrower, the engine returns
  `Screenshots`. It does not guess a leaf. A library full of confidently wrong leaves
  is worse than one that admits the depth it earned, because the user cannot tell the
  two apart until they go looking for something.
"""

from __future__ import annotations

from typing import Iterable, List, Optional

from . import rules, taxonomy
from .context import LibraryContext
from .signals import AssetSignals, Tier
from .verdict import Assignment, Classification, Evidence, REVIEW_FLOOR

# A leaf at or above this needs no further signal. Chosen so that a single strong
# unambiguous signal (a screenshot subtype, a GPS fix, a named face) settles, while
# anything resting on one hedged signal does not.
SETTLE_AT = 0.85


class Classifier:
    """Stateless per asset; the library context is shared and read-only."""

    def __init__(self, context: LibraryContext, budget: Tier = Tier.TEXT):
        # `budget` is what makes the ablation runnable: classify the same library at
        # Tier.METADATA to see what the cheap signals alone are worth, without
        # maintaining a second engine that would drift from this one.
        self.ctx = context
        self.budget = budget

    # -- public ------------------------------------------------------------
    def classify(self, a: AssetSignals) -> Classification:
        c = Classification(a.asset_id)
        c.tiers_spent.add(Tier.METADATA)

        self._timeline(a, c)
        self._metadata_root(a, c)

        # Screenshots are exempt from the visual tiers. Face clustering and scene
        # classification on a chat window produce noise at full price — the only
        # signal that tells you anything about a screenshot is its text.
        visual_worth_it = not (a.is_screenshot or a.is_screen_recording)

        if visual_worth_it and not self._settled(c) and self.budget >= Tier.VISUAL:
            c.tiers_spent.add(Tier.VISUAL)
            self._scenes(a, c)
        if visual_worth_it and not self._settled(c) and self.budget >= Tier.FACES:
            c.tiers_spent.add(Tier.FACES)
            self._faces(a, c)
        if self.budget >= Tier.TEXT and self._wants_text(a, c):
            c.tiers_spent.add(Tier.TEXT)
            self._text(a, c)

        # Places runs LAST among the content roots, and that ordering is load-bearing.
        # Run first, a GPS fix settled every photographed document as `Places > … >
        # London` at 0.91 confidence, the escalation policy saw a settled leaf, and the
        # OCR pass that would have recognised the passport never happened. Nine of nine
        # foreground documents were lost that way, silently, with a plausible answer in
        # their place. Location is context; it is not what the thing IS.
        self._places(a, c)
        self._travel(a, c)
        self._prune_implied_ancestors(c)
        self._cross_list(c)
        self._unfiled(a, c)
        return c

    def classify_all(self, assets: Iterable[AssetSignals]) -> List[Classification]:
        return [self.classify(a) for a in assets]

    # -- escalation policy -------------------------------------------------
    def _settled(self, c: Classification) -> bool:
        p = c.primary
        return bool(p and taxonomy.is_leaf(p.path) and p.confidence >= SETTLE_AT)

    def _wants_text(self, a: AssetSignals, c: Classification) -> bool:
        """Whether to READ text that exists. Whether to SPEND an OCR pass in the first
        place is the C-1 gate, and it lives upstream in the indexer where the pixels
        are — `OCRGate.swift`. Duplicating that decision here on metadata the engine
        cannot verify would be two gates disagreeing about one photo.

        Screenshots always read their text: the subtype settles the root, and only the
        text can ever open the leaf."""
        if not a.ocr_ran or not a.ocr_text:
            return False
        root = taxonomy.root_of(c.primary.path) if c.primary else None
        if root == "Screenshots":
            return True
        return not self._settled(c)

    # -- tiers -------------------------------------------------------------
    def _timeline(self, a: AssetSignals, c: Classification) -> None:
        """Every asset is reachable from Timeline. This is the multi-index premise:
        one original, many entries (§3), and the one entry that never fails.

        §3 asks for **Year → Month → Day → Moment**, not just a year. Only the year was
        indexed, which meant "the photos from that afternoon" had nothing to resolve
        against — a whole level of the tree the Constitution names as first-class.

        Only the deepest node survives `_prune_implied_ancestors`, which is correct
        and not a loss: the browse tree rolls counts up from the leaves, so a year still
        shows the right total, and holding the same asset at four depths would count it
        four times inside its own parent.

        Moment is a **capture session**, not a clock hour: a run of photographs taken
        close together. Hour boundaries cut bursts in half — six frames at 17:59 and
        two at 18:01 are one moment and would land in two — so the moment is derived
        from neighbours in `LibraryContext`, and is absent rather than guessed when
        this asset has none.
        """
        if a.created_at is None:
            c.notes.append("no capture date — this asset cannot be placed on the timeline")
            return
        when = a.created_at
        # Built without %-d / %e: those are glibc extensions and this project's own
        # machine is Windows, where they raise. A date format is not worth a
        # platform-specific crash.
        year = taxonomy.ensure_node(f"Timeline > {when.year}")
        c.add(Assignment(year, [Evidence(
            "created_at", Tier.METADATA, 0.98,
            f"taken on {when.day} {when:%B %Y}")]))

        month = taxonomy.ensure_node(f"{year} > {when:%m %B}")
        c.add(Assignment(month, [Evidence(
            "created_at", Tier.METADATA, 0.98, f"taken in {when:%B %Y}")]))

        day = taxonomy.ensure_node(f"{month} > {when:%d}")
        c.add(Assignment(day, [Evidence(
            "created_at", Tier.METADATA, 0.98,
            f"taken on {when.day} {when:%B %Y}")]))

        moment = self.ctx.moment_for(a.asset_id)
        if moment:
            node = taxonomy.ensure_node(f"{day} > {moment.label}")
            c.add(Assignment(node, [Evidence(
                "created_at", Tier.METADATA, 0.9,
                f"one of {moment.asset_count} photos taken around "
                f"{moment.start:%H:%M} that day")]))

    def _metadata_root(self, a: AssetSignals, c: Classification) -> None:
        if a.media_type == "video":
            # The canonical tree has eleven roots and none of them is Video. That is a
            # real gap (MNI-2 / FC-2), not something to paper over by filing video as
            # a photo, so it is recorded on the asset and surfaced by the catalogue.
            c.notes.append("video: the taxonomy has no node for video assets (FC-2)")

        if a.is_screenshot or a.is_screen_recording:
            c.add(Assignment("Screenshots", [Evidence(
                "is_screenshot", Tier.METADATA, 0.95,
                "the system recorded this as a screenshot")], is_primary=True))
            return

        if a.source == "downloaded":
            c.add(Assignment("Downloads", [Evidence(
                "source", Tier.METADATA, 0.88,
                "saved from another app rather than taken with the camera")], is_primary=True))
            return

    # Paperwork is not a place memory. A receipt photographed at the kitchen table
    # does not belong in `Places > United Kingdom > London` alongside the photos of
    # London — the shelf would stop meaning anything.
    _NOT_PLACES = frozenset({"Documents", "Purchases", "Screenshots", "Downloads"})

    def _places(self, a: AssetSignals, c: Classification) -> None:
        """A measured GPS fix is the single strongest cheap signal in a camera roll,
        and it is already in the metadata row. §11: an inferred fix is not this."""
        if a.geo is None or a.geo.source != "exif":
            return
        if a.place is None or not a.place.country:
            return
        if any(taxonomy.root_of(x.path) in self._NOT_PLACES for x in c.assignments):
            return

        parts = ["Places", a.place.country]
        reason = f"the location saved with the photo is in {a.place.country}"
        if a.place.city:
            parts.append(a.place.city)
            reason = f"the location saved with the photo is in {a.place.city}, {a.place.country}"
        path = taxonomy.ensure_node(taxonomy.SEP.join(parts))

        weight = min(0.92, 0.55 + 0.40 * a.place.confidence) * a.geo.confidence
        is_primary = not any(x.is_primary for x in c.assignments)
        c.add(Assignment(path, [Evidence("geo", Tier.METADATA, weight, reason)], is_primary=is_primary))

    def _travel(self, a: AssetSignals, c: Classification) -> None:
        """Travel is a library-level judgement, not a per-photo one: a run of days
        spent away from the home cluster. One photo in Tokyo is not a trip."""
        trip = self.ctx.trip_for(a.created_at, a.geo)
        if trip is None:
            return
        path = taxonomy.ensure_node(f"Travel > {trip.label}")
        span = (trip.end - trip.start).days + 1
        c.add(Assignment(path, [Evidence(
            "geo+created_at", Tier.METADATA, 0.80,
            f"part of {span} days away from home in {trip.city or trip.country or 'another place'}, "
            f"{trip.start.strftime('%B %Y')}")]))

    def _faces(self, a: AssetSignals, c: Classification) -> None:
        named = a.named_people
        if named:
            if len(named) == 1:
                path = taxonomy.ensure_node(f"People > {named[0]}")
                reason = f"{named[0]} was recognised in this photo"
                weight = 0.88
            else:
                path = "People > Groups"
                reason = "recognised " + ", ".join(named) + " together in this photo"
                weight = 0.85
            is_primary = not any(x.is_primary for x in c.assignments)
            c.add(Assignment(path, [Evidence("face_clusters", Tier.FACES, weight, reason)],
                             is_primary=is_primary))
        elif a.face_clusters:
            # An unnamed cluster still changes the risk class, which is the point:
            # "someone is in this photo" is enough to stop treating it as disposable.
            c.notes.append("unnamed person present")

    def _scenes(self, a: AssetSignals, c: Classification) -> None:
        best = {}
        for label in a.scene_labels:
            if label.confidence < rules.SCENE_FLOOR:
                continue
            path = rules.SCENE_MAP.get(label.identifier)
            if not path:
                continue
            if path not in best or label.confidence > best[path].confidence:
                best[path] = label
        for path, label in best.items():
            w = rules.scene_weight(label.confidence)
            pretty = label.identifier.replace("_", " ")
            is_primary = (not any(x.is_primary for x in c.assignments)
                          and taxonomy.root_of(path) in ("Objects", "Downloads"))
            c.add(Assignment(path, [Evidence(
                "scene_labels", Tier.VISUAL, w,
                f"a {pretty} was recognised in the picture")], is_primary=is_primary))

    def _text(self, a: AssetSignals, c: Classification) -> None:
        text = a.ocr_text or ""
        if not text.strip():
            return
        root = taxonomy.root_of(c.primary.path) if c.primary else None

        groups = [rules.SCREENSHOT_RULES, rules.DOCUMENT_RULES,
                  rules.PURCHASE_RULES, rules.WORK_TEXT_RULES]
        # Within a group the first match wins, so specific rules must precede general
        # ones in the table — `Documents > Identity > Passports` before `Documents`.
        for group in groups:
            for rule in group:
                if rule.requires_root and rule.requires_root != root:
                    continue
                if not rule.pattern.search(text):
                    continue
                is_primary = (not any(x.is_primary for x in c.assignments)
                              or (root == "Screenshots" and rule.requires_root == "Screenshots"))
                if root == "Screenshots" and rule.requires_root == "Screenshots":
                    # Deepen the existing Screenshots assignment rather than adding a
                    # competing root.
                    for existing in c.assignments:
                        if existing.path == "Screenshots":
                            existing.is_primary = False
                c.add(Assignment(rule.path, [Evidence("ocr_text", Tier.TEXT, rule.weight, rule.reason)],
                                 is_primary=is_primary))
                break

    def _prune_implied_ancestors(self, c: Classification) -> None:
        """`Screenshots` and `Screenshots > Temporary > Pickup Codes` are one entry,
        not two. The browse tree rolls counts up from the leaves, so leaving both in
        would count the asset twice in its own parent.

        The ancestor's evidence is merged into the descendant rather than discarded —
        "the system recorded this as a screenshot" is half the reason the leaf is
        right, and the user is owed the whole reason."""
        held = {x.path for x in c.assignments}
        for assignment in list(c.assignments):
            deeper = [p for p in held
                      if p != assignment.path and assignment.path in taxonomy.ancestors(p)]
            if not deeper:
                continue
            target = min(deeper, key=lambda p: taxonomy.depth(p))
            for other in c.assignments:
                if other.path == target:
                    other.evidence.extend(assignment.evidence)
                    other.is_primary = other.is_primary or assignment.is_primary
                    break
            c.assignments.remove(assignment)
            held.discard(assignment.path)

    def _cross_list(self, c: Classification) -> None:
        """`_also_in` from the canonical tree. One original, two entries (§3) — the
        receipt the user thinks of as paperwork and the receipt they think of as a
        purchase are the same photo, filed once."""
        for assignment in list(c.assignments):
            also = taxonomy.cross_listing(assignment.path)
            if not also:
                continue
            c.add(Assignment(also, [Evidence(
                "taxonomy", Tier.METADATA, min(0.9, assignment.confidence),
                f"also filed under {also} — the same photo, not a copy "
                f"(cross-listed from {assignment.path})")],
                cross_listed_from=assignment.path))

    def _unfiled(self, a: AssetSignals, c: Classification) -> None:
        """An asset with a date and nothing else is on the timeline and nowhere else.
        Saying so is more useful than inventing a home for it, and it is the honest
        count of how much of a library the engine cannot yet explain."""
        content = [x for x in c.assignments if taxonomy.root_of(x.path) != "Timeline"]
        if not content:
            c.notes.append("unfiled: no signal placed this asset anywhere but the timeline")
