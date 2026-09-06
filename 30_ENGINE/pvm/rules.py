# -*- coding: utf-8 -*-
"""
THE RULE SET — data, not control flow.

Rules are declarative rows so they can be read, argued with and ported. The engine in
`classifier.py` contains the escalation policy; this file contains what each signal
means. Keeping them apart is what makes it possible to change "receipts also live
under Documents" without touching the part that decides when to spend an OCR pass.

Three constraints are load-bearing:

* **A rule states the deepest node its evidence actually supports.** A rule that can
  only tell you "this is a screenshot" says `Screenshots` and stops. Inventing
  `Screenshots > Chat` from a screenshot subtype alone would be a confident lie, and
  the browse tree would fill with wrong leaves that look right.

* **§16 boundary on Medical.** A rule may recognise that the user photographed a
  medical DOCUMENT. No rule may infer, store or expose anything about the person's
  health — no condition, no medication, no treatment. The category holds documents;
  it never characterises the human. `MEDICAL_IS_DOCUMENT_ONLY` exists so this is a
  named, testable property rather than an intention.

* **Weights are doubt-removal, not probability.** 0.9 means "this alone removes 90%
  of the doubt", so two independent 0.6 signals beat one 0.85. Nothing reaches 1.0.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Pattern

from .signals import Tier

MEDICAL_IS_DOCUMENT_ONLY = True


@dataclass(frozen=True)
class TextRule:
    pattern: Pattern
    path: str
    weight: float
    reason: str
    # Only fires when the asset already sits under this root, if set. Keeps
    # "verification code" from pulling a photographed letter into Screenshots.
    requires_root: Optional[str] = None


def _rx(p: str) -> Pattern:
    return re.compile(p, re.IGNORECASE)


# A note that cost a real miss: a trailing \b after a PREFIX never matches. The
# original rule for order confirmations was `\border\s+(number|no|confirm)\b`, and
# on the text "ORDER CONFIRMATION" the group matched "CONFIRM" while the \b that
# followed it landed between M and A — both word characters — so the whole rule
# failed. One screenshot was filed as a plain screenshot instead of a purchase, which
# is exactly the kind of miss nobody notices until they go looking for the order.
# Rules that key on a word STEM use `\w*` before the boundary.


# --------------------------------------------------------------------------------
# Identity, contracts, finance, health — the Protect-by-default classes.
# Weights are high because these phrases are not ambiguous, and being *sure* is what
# earns the asset its Protect status. Under-detecting here is the dangerous direction.
# --------------------------------------------------------------------------------
DOCUMENT_RULES: List[TextRule] = [
    TextRule(_rx(r"\bpassport\b"), "Documents > Identity > Passports", 0.90,
             "the text “passport” was read on the document"),
    TextRule(_rx(r"\bdriv(er|ing)'?s?\s+licen[cs]e\b"), "Documents > Identity > Driver Licenses", 0.90,
             "the text “driving licence” was read on the document"),
    TextRule(_rx(r"\b(id\s*card|national\s+id|identity\s+card)\b"), "Documents > Identity > ID Cards", 0.90,
             "the text “ID card” was read on the document"),
    TextRule(_rx(r"\bvisa\b(?!\s*(card|debit|credit))"), "Documents > Identity > Visas", 0.78,
             "the text “visa” was read on the document"),

    TextRule(_rx(r"\b(tenancy|lease\s+agreement|assured\s+shorthold)\b"), "Documents > Contracts > Tenancy", 0.85,
             "tenancy wording was read on the document"),
    TextRule(_rx(r"\b(employment\s+(contract|agreement)|offer\s+letter)\b"), "Documents > Contracts > Employment", 0.85,
             "employment-contract wording was read on the document"),
    TextRule(_rx(r"\b(insurance|policy\s+(number|no\.?)|underwrit)"), "Documents > Contracts > Insurance", 0.82,
             "insurance-policy wording was read on the document"),
    TextRule(_rx(r"\bcontract\b"), "Documents > Contracts", 0.70,
             "the text “contract” was read on the document"),

    TextRule(_rx(r"\b(sort\s*code|iban\b|account\s+number|bank\s+of\b)"), "Documents > Financial > Bank", 0.85,
             "bank-account details were read on the document"),
    TextRule(_rx(r"\b(hmrc|p60\b|p45\b|tax\s+(return|year|code))"), "Documents > Financial > Tax", 0.85,
             "tax wording was read on the document"),
    TextRule(_rx(r"\b(statement|balance\s+(brought|carried))\b"), "Documents > Financial > Statements", 0.72,
             "statement wording was read on the document"),

    # §16: recognises the DOCUMENT. Says nothing about the person, and nothing
    # downstream may extract health content from it.
    TextRule(_rx(r"\b(prescription\w*|nhs\b|test\s+results?|referral\s+letter|clinic\w*|surgery\s+appointment)\b"),
             "Documents > Medical", 0.80,
             "this looks like a medical document — filed as a document, and nothing "
             "about your health is inferred, stored or shown from it"),

    # Deliberately weak, deliberately shallow. "Document" tells you it is paperwork
    # and nothing about which kind, so the rule stops at the root.
    TextRule(_rx(r"\bdocument\b"), "Documents", 0.55,
             "text on the image reads as a document rather than a scene"),
]

# --------------------------------------------------------------------------------
# Purchases. `Receipts` and `Warranty` are declared `_also_in` by the canonical tree,
# so the cross-listing is taken from the tree rather than restated here.
# --------------------------------------------------------------------------------
PURCHASE_RULES: List[TextRule] = [
    TextRule(_rx(r"\breceipt\b|\b(vat|subtotal)\b|\btotal\s*[:£$€]"), "Purchases > Receipts", 0.85,
             "receipt wording and a total were read on the image"),
    TextRule(_rx(r"\b(warrant\w*|guarantee\w*)\b"), "Purchases > Warranty", 0.85,
             "warranty wording was read on the image"),
    TextRule(_rx(r"\border\s+(number|no\.?|confirm\w*)\b|\byour\s+order\b|\border\s+placed\b"), "Purchases > Orders", 0.80,
             "an order confirmation was read on the image"),
    TextRule(_rx(r"\b(out\s+for\s+delivery|tracking\s+(number|no\.?)|dispatch\w*|delivered\s+on|courier)\b"),
             "Purchases > Delivery", 0.80, "delivery-tracking wording was read on the image"),
    TextRule(_rx(r"\bpurchase\b"), "Purchases", 0.55,
             "the image reads as purchase paperwork, but not which kind"),
]

# --------------------------------------------------------------------------------
# Screenshots. The subtype tells you it is a screenshot; only the text tells you what
# KIND. Temporary codes matter most: they are the R2 class whose whole value is that
# they stop being useful, and a library that cannot find them cannot tidy them.
# --------------------------------------------------------------------------------
SCREENSHOT_RULES: List[TextRule] = [
    TextRule(_rx(r"\b(verification|confirmation|security)\s+code\b|\bone[-\s]?time\s+(code|password)\b|\botp\b"),
             "Screenshots > Temporary > Verification Codes", 0.88,
             "a one-time verification code was read in the screenshot", "Screenshots"),
    TextRule(_rx(r"\b(pickup|collection)\s+code\b|\block(er)?\s*[a-z]?\d+\b"),
             "Screenshots > Temporary > Pickup Codes", 0.86,
             "a parcel pickup code was read in the screenshot", "Screenshots"),
    TextRule(_rx(r"\b(boarding\s+pass|e[-\s]?ticket|gate\s+\d+|seat\s+\d+[a-z]\b|booking\s+reference)\b"),
             "Screenshots > Temporary > Tickets", 0.84,
             "a ticket or boarding pass was read in the screenshot", "Screenshots"),
    TextRule(_rx(r"\b(directions|route|\d+\s*min\s+(drive|walk)|maps?)\b"),
             "Screenshots > Maps", 0.72, "map or directions wording was read in the screenshot", "Screenshots"),
    TextRule(_rx(r"\b(add\s+to\s+(bag|cart|basket)|checkout|in\s+stock|free\s+returns)\b"),
             "Screenshots > Shopping", 0.75, "shop wording was read in the screenshot", "Screenshots"),
    TextRule(_rx(r"\b(typing|delivered|read\s+\d{1,2}:\d{2}|whatsapp|imessage|telegram)\b"),
             "Screenshots > Chat", 0.72, "chat wording was read in the screenshot", "Screenshots"),
    TextRule(_rx(r"\b(error\w*|fail\w*|unable\s+to|something\s+went\s+wrong|exception|crash\w*)\b"),
             "Screenshots > Errors", 0.74, "an error message was read in the screenshot", "Screenshots"),
    TextRule(_rx(r"\b(sprint|stand-?up|jira|confluence|agenda|slide\s+\d+|action\s+items?)\b"),
             "Screenshots > Work", 0.72, "work wording was read in the screenshot", "Screenshots"),
    TextRule(_rx(r"https?://|\bwww\.|\.com\b"),
             "Screenshots > Web", 0.62, "a web address was read in the screenshot", "Screenshots"),
]

# --------------------------------------------------------------------------------
# Work. Whiteboards and meeting captures are camera photos of a room, not screenshots,
# so they are found by scene rather than by subtype.
# --------------------------------------------------------------------------------
WORK_TEXT_RULES: List[TextRule] = [
    TextRule(_rx(r"\b(agenda|minutes|action\s+items?|attendees)\b"), "Work > Meetings", 0.70,
             "meeting wording was read on the image"),
]

# --------------------------------------------------------------------------------
# Scene labels -> categories. Vision's identifiers, mapped once. Weight scales with
# the label's own confidence, so a hesitant classifier produces a hesitant assignment
# instead of a confident wrong leaf.
# --------------------------------------------------------------------------------
SCENE_MAP = {
    "bicycle": "Objects > Bicycle", "bike": "Objects > Bicycle",
    "refrigerator": "Objects > Appliances", "washing_machine": "Objects > Appliances",
    "oven": "Objects > Appliances", "microwave": "Objects > Appliances",
    "laptop": "Objects > Devices", "computer": "Objects > Devices",
    "mobile_phone": "Objects > Devices", "camera": "Objects > Devices",
    "television": "Objects > Devices", "headphones": "Objects > Devices",
    "chair": "Objects > Furniture", "table": "Objects > Furniture",
    "sofa": "Objects > Furniture", "bed": "Objects > Furniture",
    "cabinet": "Objects > Furniture", "desk": "Objects > Furniture",

    "shirt": "Clothing > Tops", "t_shirt": "Clothing > Tops",
    "blouse": "Clothing > Tops", "sweater": "Clothing > Tops",
    "coat": "Clothing > Outerwear", "jacket": "Clothing > Outerwear",
    "shoe": "Clothing > Shoes", "sneaker": "Clothing > Shoes", "boot": "Clothing > Shoes",

    "whiteboard": "Work > Whiteboards", "blackboard": "Work > Whiteboards",
    "projection_screen": "Work > Meetings", "conference_room": "Work > Meetings",
    "presentation": "Work > Meetings",

    "meme": "Downloads > Memes", "wallpaper": "Downloads > Wallpapers",
}

# A scene label below this is a hint, not a finding, and never opens a leaf on its own.
SCENE_FLOOR = 0.35


def scene_weight(label_confidence: float) -> float:
    """Vision's confidence, mapped into doubt-removal. Even a 1.0 label is capped
    below certainty: the classifier has been confidently wrong about a photo of a
    photo before, and will be again."""
    return max(0.30, min(0.86, 0.30 + 0.60 * label_confidence))
