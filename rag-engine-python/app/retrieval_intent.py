from __future__ import annotations

import json
import re
from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator


INTENT_SCHEMA_VERSION = "4"


class SemanticIntentTag(StrEnum):
    ADVERSE_EVENT = "adverse_event"
    PET_HOSPITALIZATION = "pet_hospitalization"
    GASTROINTESTINAL = "gastrointestinal"
    NEUROLOGIC_SIGNS = "neurologic_signs"
    RESPIRATORY_CONTEXT = "respiratory_context"
    INGREDIENT_QUESTION = "ingredient_question"
    SUPPLIER_QUESTION = "supplier_question"
    BUD_QUESTION = "bud_question"
    DEVICE_CONCERN = "device_concern"
    EFFICACY_CONCERN = "efficacy_concern"
    APPEARANCE_CONCERN = "appearance_concern"
    STORAGE_CONCERN = "storage_concern"
    ADMINISTRATION_QUESTION = "administration_question"
    QUANTITY_DISCREPANCY = "quantity_discrepancy"
    PALATABILITY_CONCERN = "palatability_concern"
    TRANSDERMAL_SITE_CONCERN = "transdermal_site_concern"


class RetrievalIntentTag(StrEnum):
    ADVERSE_EVENT = "adverse_event"
    PET_HOSPITALIZATION = "pet_hospitalization"
    GASTROINTESTINAL = "gastrointestinal"
    NEUROLOGIC_SIGNS = "neurologic_signs"
    RESPIRATORY_CONTEXT = "respiratory_context"
    INGREDIENT_QUESTION = "ingredient_question"
    SUPPLIER_QUESTION = "supplier_question"
    BUD_QUESTION = "bud_question"
    DEVICE_CONCERN = "device_concern"
    EFFICACY_CONCERN = "efficacy_concern"
    APPEARANCE_CONCERN = "appearance_concern"
    STORAGE_CONCERN = "storage_concern"
    ADMINISTRATION_QUESTION = "administration_question"
    QUANTITY_DISCREPANCY = "quantity_discrepancy"
    PALATABILITY_CONCERN = "palatability_concern"
    TRANSDERMAL_SITE_CONCERN = "transdermal_site_concern"
    PHARMACIST_OUTREACH = "pharmacist_outreach"
    FRONTLINE_PHARMACIST_RESPONSE = "frontline_pharmacist_response"
    ADVERSE_EVENT_REVIEW = "adverse_event_review"
    SEVERE_ESCALATION = "severe_escalation"
    QUALITY_REVIEW = "quality_review"
    ADMINISTRATION_REVIEW = "administration_review"
    REFERENCE_REVIEW = "reference_review"
    LOT_BATCH_REVIEW = "lot_batch_review"
    TREND_REVIEW = "trend_review"
    DISCLOSURE_BOUNDARY = "disclosure_boundary"
    PUBLIC_CORPUS_BOUNDARY = "public_corpus_boundary"
    REFERENCE_BOUNDARY = "reference_boundary"


class SemanticRetrievalIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tags: list[SemanticIntentTag] = Field(default_factory=list)

    @field_validator("tags", mode="after")
    @classmethod
    def canonicalize_tags(
        cls,
        value: list[SemanticIntentTag],
    ) -> list[SemanticIntentTag]:
        order = {tag: index for index, tag in enumerate(SemanticIntentTag)}
        return sorted(set(value), key=order.__getitem__)


class RetrievalIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tags: list[RetrievalIntentTag] = Field(default_factory=list)

    @field_validator("tags", mode="after")
    @classmethod
    def canonicalize_tags(
        cls,
        value: list[RetrievalIntentTag],
    ) -> list[RetrievalIntentTag]:
        order = {tag: index for index, tag in enumerate(RetrievalIntentTag)}
        return sorted(set(value), key=order.__getitem__)


class RetrievalIntentDetector(Protocol):
    def detect(self, concern_text: str) -> SemanticRetrievalIntent:
        ...


class JsonCompletionClient(Protocol):
    def complete_json(self, prompt: str) -> str:
        ...


class UnknownIntentTagError(ValueError):
    def __init__(self, unknown_tags: list[str]) -> None:
        self.unknown_tags = unknown_tags
        super().__init__(
            "Unknown semantic retrieval intent tags: "
            + ", ".join(unknown_tags)
        )


INTENT_SEARCH_TERMS: dict[RetrievalIntentTag, tuple[str, ...]] = {
    RetrievalIntentTag.ADVERSE_EVENT: ("adverse event", "suspected ADE"),
    RetrievalIntentTag.PET_HOSPITALIZATION: ("hospitalization", "severe escalation"),
    RetrievalIntentTag.GASTROINTESTINAL: (
        "vomiting", "diarrhea", "blood in stool", "gastrointestinal symptoms",
    ),
    RetrievalIntentTag.NEUROLOGIC_SIGNS: (
        "difficulty walking", "weakness", "ataxia", "neurologic signs",
    ),
    RetrievalIntentTag.RESPIRATORY_CONTEXT: (
        "shortness of breath", "respiratory symptoms",
    ),
    RetrievalIntentTag.INGREDIENT_QUESTION: (
        "inactive ingredient", "ingredient presence", "formulation information",
    ),
    RetrievalIntentTag.SUPPLIER_QUESTION: (
        "supplier manufacturer disclosure", "ingredient source information",
    ),
    RetrievalIntentTag.BUD_QUESTION: (
        "beyond use date", "BUD clarification", "stability limitation",
    ),
    RetrievalIntentTag.DEVICE_CONCERN: (
        "dispensing device", "pen function", "click mechanism",
    ),
    RetrievalIntentTag.EFFICACY_CONCERN: (
        "lack of efficacy", "therapeutic response", "worsening bloodwork",
    ),
    RetrievalIntentTag.APPEARANCE_CONCERN: (
        "appearance change", "odor color viscosity", "product quality concern",
    ),
    RetrievalIntentTag.STORAGE_CONCERN: (
        "storage conditions", "temperature excursion", "refrigerated storage", "room temperature",
    ),
    RetrievalIntentTag.ADMINISTRATION_QUESTION: (
        "administration technique", "dose administration", "food absorption",
    ),
    RetrievalIntentTag.QUANTITY_DISCREPANCY: (
        "oral liquid shortage", "quantity discrepancy", "syringe measurement",
    ),
    RetrievalIntentTag.PALATABILITY_CONCERN: (
        "palatability", "flavor rejection", "drooling foaming",
    ),
    RetrievalIntentTag.TRANSDERMAL_SITE_CONCERN: (
        "transdermal application site", "ear irritation", "skin reaction",
    ),
    RetrievalIntentTag.PHARMACIST_OUTREACH: (
        "pharmacist outreach", "customer clinical follow up",
    ),
    RetrievalIntentTag.FRONTLINE_PHARMACIST_RESPONSE: (
        "frontline pharmacist response", "delegate back guidance",
    ),
    RetrievalIntentTag.ADVERSE_EVENT_REVIEW: (
        "adverse event review", "suspected ADE review",
    ),
    RetrievalIntentTag.SEVERE_ESCALATION: (
        "leadership escalation", "life threatening or legal",
    ),
    RetrievalIntentTag.QUALITY_REVIEW: (
        "quality review", "record review", "inventory inspection",
    ),
    RetrievalIntentTag.ADMINISTRATION_REVIEW: (
        "administration review", "customer context review",
    ),
    RetrievalIntentTag.REFERENCE_REVIEW: (
        "external reference review", "unsupported clinical reference",
    ),
    RetrievalIntentTag.LOT_BATCH_REVIEW: (
        "lot batch review", "same batch concern",
    ),
    RetrievalIntentTag.TREND_REVIEW: (
        "trend review", "pattern monitoring",
    ),
    RetrievalIntentTag.DISCLOSURE_BOUNDARY: (
        "disclosure boundary", "proprietary information limitation",
    ),
    RetrievalIntentTag.PUBLIC_CORPUS_BOUNDARY: (
        "unsupported public corpus", "public information boundary",
    ),
    RetrievalIntentTag.REFERENCE_BOUNDARY: (
        "external reference boundary", "product specific stability unsupported",
    ),
}


class RuleIntentDetector:
    def detect(self, concern_text: str) -> SemanticRetrievalIntent:
        text = normalize_text(require_text(concern_text))
        tags: list[SemanticIntentTag] = []

        def add(*values: SemanticIntentTag) -> None:
            tags.extend(values)

        hospitalized = has_affirmed_hospitalization(text)
        gastrointestinal = contains_any_pattern(text, GASTROINTESTINAL_PATTERNS)
        neurologic = contains_any_pattern(text, NEUROLOGIC_PATTERNS)
        respiratory = contains_any_pattern(text, RESPIRATORY_PATTERNS)
        ingredient_request = is_ingredient_request(text)
        supplier_request = is_supplier_request(text)
        bud_question = is_bud_question(text)
        device_concern = contains_any_pattern(text, DEVICE_PATTERNS)
        efficacy_concern = is_efficacy_concern(text)
        appearance_concern = contains_any_pattern(text, APPEARANCE_PATTERNS)
        storage_concern = contains_any_pattern(text, STORAGE_PATTERNS)
        administration_question = is_administration_question(text)
        quantity_discrepancy = contains_any_pattern(text, QUANTITY_PATTERNS)
        palatability_concern = (
            not ingredient_request
            and contains_any_pattern(text, PALATABILITY_PATTERNS)
        )
        transdermal_site_concern = contains_any_pattern(text, TRANSDERMAL_PATTERNS)

        if hospitalized:
            add(SemanticIntentTag.PET_HOSPITALIZATION)
        if gastrointestinal:
            add(SemanticIntentTag.GASTROINTESTINAL)
        if neurologic:
            add(SemanticIntentTag.NEUROLOGIC_SIGNS)
        if respiratory:
            add(SemanticIntentTag.RESPIRATORY_CONTEXT)
        if ingredient_request:
            add(SemanticIntentTag.INGREDIENT_QUESTION)
        if supplier_request:
            add(SemanticIntentTag.SUPPLIER_QUESTION)
        if bud_question:
            add(SemanticIntentTag.BUD_QUESTION)
        if device_concern:
            add(SemanticIntentTag.DEVICE_CONCERN)
        if efficacy_concern:
            add(SemanticIntentTag.EFFICACY_CONCERN)
        if appearance_concern:
            add(SemanticIntentTag.APPEARANCE_CONCERN)
        if storage_concern:
            add(SemanticIntentTag.STORAGE_CONCERN)
        if administration_question:
            add(SemanticIntentTag.ADMINISTRATION_QUESTION)
        if quantity_discrepancy:
            add(SemanticIntentTag.QUANTITY_DISCREPANCY)
        if palatability_concern:
            add(SemanticIntentTag.PALATABILITY_CONCERN)
        if transdermal_site_concern:
            add(SemanticIntentTag.TRANSDERMAL_SITE_CONCERN)
        if gastrointestinal or neurologic or respiratory:
            add(SemanticIntentTag.ADVERSE_EVENT)

        return SemanticRetrievalIntent(tags=tags)


class NanoIntentDetector:
    def __init__(self, client: JsonCompletionClient) -> None:
        self._client = client

    def detect(self, concern_text: str) -> SemanticRetrievalIntent:
        text = require_text(concern_text)
        payload = parse_json_object(
            self._client.complete_json(build_nano_intent_prompt(text))
        )
        if set(payload) != {"tags"}:
            raise ValueError(
                "nano intent output must contain exactly one key: tags"
            )

        raw_tags = payload["tags"]
        if not isinstance(raw_tags, list):
            raise TypeError("tags must be a list")

        allowed = {tag.value for tag in SemanticIntentTag}
        normalized = [normalize_tag(str(tag)) for tag in raw_tags]
        unknown = sorted({tag for tag in normalized if tag not in allowed})
        if unknown:
            raise UnknownIntentTagError(unknown)

        typed_tags = [SemanticIntentTag(tag) for tag in normalized]
        return SemanticRetrievalIntent(tags=typed_tags)


def derive_retrieval_intent(
    semantic_intent: SemanticRetrievalIntent,
) -> RetrievalIntent:
    semantic = set(semantic_intent.tags)
    tags = [RetrievalIntentTag(tag.value) for tag in semantic_intent.tags]

    def add(*values: RetrievalIntentTag) -> None:
        tags.extend(values)

    def add_quality_review() -> None:
        add(
            RetrievalIntentTag.QUALITY_REVIEW,
            RetrievalIntentTag.TREND_REVIEW,
        )

    if SemanticIntentTag.PET_HOSPITALIZATION in semantic:
        add(
            RetrievalIntentTag.ADVERSE_EVENT,
            RetrievalIntentTag.ADVERSE_EVENT_REVIEW,
            RetrievalIntentTag.SEVERE_ESCALATION,
        )
    if semantic & {
        SemanticIntentTag.GASTROINTESTINAL,
        SemanticIntentTag.NEUROLOGIC_SIGNS,
    }:
        add(
            RetrievalIntentTag.ADVERSE_EVENT,
            RetrievalIntentTag.ADVERSE_EVENT_REVIEW,
        )
    if SemanticIntentTag.RESPIRATORY_CONTEXT in semantic:
        add(
            RetrievalIntentTag.ADVERSE_EVENT,
            RetrievalIntentTag.ADVERSE_EVENT_REVIEW,
            RetrievalIntentTag.PHARMACIST_OUTREACH,
        )
    if semantic & {
        SemanticIntentTag.INGREDIENT_QUESTION,
        SemanticIntentTag.SUPPLIER_QUESTION,
    }:
        add(
            RetrievalIntentTag.FRONTLINE_PHARMACIST_RESPONSE,
            RetrievalIntentTag.DISCLOSURE_BOUNDARY,
            RetrievalIntentTag.PUBLIC_CORPUS_BOUNDARY,
        )
    if SemanticIntentTag.BUD_QUESTION in semantic:
        add(
            RetrievalIntentTag.REFERENCE_REVIEW,
            RetrievalIntentTag.REFERENCE_BOUNDARY,
        )
    if SemanticIntentTag.DEVICE_CONCERN in semantic:
        add_quality_review()
    if SemanticIntentTag.EFFICACY_CONCERN in semantic:
        add(
            RetrievalIntentTag.ADMINISTRATION_REVIEW,
            RetrievalIntentTag.REFERENCE_REVIEW,
        )
    if SemanticIntentTag.APPEARANCE_CONCERN in semantic:
        add(RetrievalIntentTag.LOT_BATCH_REVIEW)
        add_quality_review()
    if SemanticIntentTag.STORAGE_CONCERN in semantic:
        add(
            RetrievalIntentTag.ADMINISTRATION_REVIEW,
            RetrievalIntentTag.REFERENCE_BOUNDARY,
        )
    if SemanticIntentTag.ADMINISTRATION_QUESTION in semantic:
        add(RetrievalIntentTag.ADMINISTRATION_REVIEW)
    if SemanticIntentTag.QUANTITY_DISCREPANCY in semantic:
        add(RetrievalIntentTag.ADMINISTRATION_REVIEW)
        add_quality_review()
    if semantic & {
        SemanticIntentTag.PALATABILITY_CONCERN,
        SemanticIntentTag.TRANSDERMAL_SITE_CONCERN,
    }:
        add(RetrievalIntentTag.ADMINISTRATION_REVIEW)

    return RetrievalIntent(tags=tags)


def map_intent_to_search_text(
    concern_text: str,
    intent: RetrievalIntent,
) -> str:
    text = require_text(concern_text)
    terms: list[str] = []
    seen: set[str] = set()
    for tag in intent.tags:
        for term in INTENT_SEARCH_TERMS[tag]:
            normalized = " ".join(term.split()).strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            terms.append(normalized)
    if not terms:
        return text
    return f"{text}\n\nRetrieval concepts: {' '.join(terms)}"


def unmapped_intent_tags(intent: RetrievalIntent) -> list[RetrievalIntentTag]:
    return [tag for tag in intent.tags if tag not in INTENT_SEARCH_TERMS]


def build_nano_intent_prompt(concern_text: str) -> str:
    allowed = ", ".join(tag.value for tag in SemanticIntentTag)
    return f"""Classify the complaint into semantic retrieval intent tags.

Return one JSON object with exactly this shape:
{{"tags": ["controlled_tag"]}}

Allowed semantic tags:
{allowed}

Rules:
- Return only allowed semantic tag values.
- Identify what the narrative means; do not add workflow actions.
- Do not return review, escalation, disclosure, outreach, or reference-policy tags.
- Do not generate search text.
- Preserve reported meaning without deciding causality.
- Hospitalization is a reported semantic fact; policy code handles escalation.
- Do not include names or identifiers.

Complaint:
{concern_text}
"""


def parse_json_object(value: str) -> dict[str, object]:
    text = require_text(value)
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            text = "\n".join(lines[1:-1]).strip()
            if text.lower().startswith("json"):
                text = text[4:].lstrip()
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("nano semantic intent must be a JSON object")
    return payload


def normalize_tag(value: str) -> str:
    return re.sub(
        r"_+",
        "_",
        re.sub(r"[^a-z0-9]+", "_", value.strip().lower()),
    ).strip("_")


def normalize_text(value: str) -> str:
    return " ".join(value.lower().split())


def contains_any_pattern(
    text: str,
    patterns: tuple[re.Pattern[str], ...],
) -> bool:
    return any(pattern.search(text) is not None for pattern in patterns)


def contains_any_phrase(text: str, phrases: tuple[str, ...]) -> bool:
    return any(contains_phrase(text, phrase) for phrase in phrases)


def contains_phrase(text: str, phrase: str) -> bool:
    escaped = re.escape(" ".join(phrase.lower().split()))
    escaped = escaped.replace(r"\ ", r"\s+")
    return re.search(rf"(?<!\w){escaped}(?!\w)", text) is not None


def has_information_request(text: str) -> bool:
    return contains_any_phrase(
        text,
        (
            "who", "what company", "which company", "identify", "tell us",
            "tell me", "wants to know", "want to know", "asking about",
            "asked about", "asks whether", "asked whether", "provide the",
            "specifics",
        ),
    )


def is_supplier_request(text: str) -> bool:
    if contains_any_pattern(text, MANUFACTURER_REPORTING_PATTERNS):
        return False
    return contains_any_pattern(text, SUPPLIER_PATTERNS) and has_information_request(text)


def is_ingredient_request(text: str) -> bool:
    return contains_any_pattern(text, INGREDIENT_PATTERNS) and (
        has_information_request(text)
        or contains_any_phrase(
            text,
            (
                "inactive ingredient", "inactive ingredients", "inactive component",
                "inactive components", "ingredient list", "full ingredient list",
            ),
        )
    )


def is_administration_question(text: str) -> bool:
    if contains_any_pattern(text, ADMINISTRATION_TECHNIQUE_PATTERNS):
        return True
    return (
        contains_any_pattern(text, ADMINISTRATION_TOPIC_PATTERNS)
        and contains_any_pattern(text, QUESTION_REQUEST_PATTERNS)
    )


def is_efficacy_concern(text: str) -> bool:
    return contains_any_pattern(text, EFFICACY_PATTERNS)


def is_bud_question(text: str) -> bool:
    return contains_any_pattern(text, BUD_PATTERNS)


HOSPITALIZATION_PATTERN = re.compile(
    r"\b(?:hospitali[sz](?:ed|ation)|admitted|er visit)\b"
)
HOSPITALIZATION_NEGATION_PATTERN = re.compile(
    r"\b(?:no|not|never|without)\b(?:\W+\w+){0,3}\W*$"
)

GASTROINTESTINAL_PATTERNS = (
    re.compile(r"\bvomit(?:ed|ing|s)?\b"),
    re.compile(r"\bvmtg\b"),
    re.compile(r"\bdiarrhea\b"),
    re.compile(r"\bloose stools?\b"),
    re.compile(r"\bblood(?:y)?\s+stools?\b"),
    re.compile(r"\bgi upset\b"),
)

NEUROLOGIC_PATTERNS = (
    re.compile(r"\bdifficulty walking\b"),
    re.compile(r"\bunable to walk\b"),
    re.compile(r"\bweak(?:ness| legs?)?\b"),
    re.compile(r"\bback legs? seemed weak\b"),
    re.compile(r"\bataxia\b"),
    re.compile(r"\bneurolog(?:ic|ical)\b"),
    re.compile(r"\bwobbl(?:y|ing)\b"),
    re.compile(r"\bfell over\b"),
    re.compile(r"\bwalking like the floor was moving\b"),
    re.compile(r"\bloss of coordination\b"),
)

RESPIRATORY_PATTERNS = (
    re.compile(r"\bshort(?:ness)? of breath\b"),
    re.compile(r"\bdifficulty breathing\b"),
    re.compile(r"\brespiratory distress\b"),
    re.compile(r"\bgag(?:ged|ging)?\b"),
    re.compile(r"\bwinded\b"),
)

INGREDIENT_PATTERNS = (
    re.compile(r"\binactive (?:ingredient|ingredients|component|components)\b"),
    re.compile(r"\bingredient list\b"),
    re.compile(r"\bfull ingredient list\b"),
    re.compile(r"\bwhat (?:is|are) in\b"),
    re.compile(r"\bwhat does .+ contain\b"),
    re.compile(r"\bwhether .+ contains?\b"),
    re.compile(r"\banimal[- ]derived\b"),
    re.compile(r"\bvegan\b"),
    re.compile(r"\bsugar[- ]free\b"),
    re.compile(r"\bformulation (?:information|details)\b"),
)

SUPPLIER_PATTERNS = (
    re.compile(r"\bsuppliers?\b"),
    re.compile(r"\bmanufacturer(?:s|ed|ing)?\b"),
    re.compile(r"\bmanufactures?\b"),
    re.compile(r"\bsource(?:d|s|ing)?\b"),
    re.compile(r"\bvendor\b"),
    re.compile(r"\bwho\b.{0,24}\bmakes\b"),
    re.compile(r"\bwhich company\b.{0,24}\b(?:ships|supplies|makes)\b"),
)

MANUFACTURER_REPORTING_PATTERNS = (
    re.compile(r"\breport(?:ed|ing)? to (?:the )?manufacturer\b"),
    re.compile(r"\bwill not report to (?:the )?manufacturer\b"),
    re.compile(r"\bmanufacturer (?:was )?notified\b"),
    re.compile(r"\bsubmitted to (?:the )?manufacturer\b"),
)

BUD_PATTERNS = (
    re.compile(r"\bbeyond[- ]use\b"),
    re.compile(r"\bafter (?:the )?bud\b"),
    re.compile(r"\bdegradation rate\b"),
    re.compile(r"\bexpired\b"),
    re.compile(r"\bexpiration\b"),
    re.compile(r"\bbud\b"),
)

DEVICE_PATTERNS = (
    re.compile(r"\bpen\b"),
    re.compile(r"\bdevice\b"),
    re.compile(r"\bclick(?:s|ing|ed)?\b"),
    re.compile(r"\bnot dispensing\b"),
    re.compile(r"\bnothing (?:came|comes) out\b"),
    re.compile(r"\bbarely anything (?:came|comes) out\b"),
    re.compile(r"\bplunger\b"),
    re.compile(r"\bleak(?:s|ing|ed)?\b"),
    re.compile(r"\bair bubble\b"),
)

EFFICACY_PATTERNS = (
    re.compile(r"\bnot effective\b"),
    re.compile(r"\bnot working\b"),
    re.compile(r"\bwhether .+ is working\b"),
    re.compile(r"\black of efficacy\b"),
    re.compile(r"\bstill uncontrolled\b"),
    re.compile(r"\btherapeutic levels?\b"),
    re.compile(r"\b(?:values?|bloodwork) .+ wrong direction\b"),
    re.compile(r"\bworsening bloodwork\b"),
)

APPEARANCE_PATTERNS = (
    re.compile(r"\btoo thick\b"),
    re.compile(r"\bthicker\b"),
    re.compile(r"\bviscosity\b"),
    re.compile(r"\bsmells? (?:weird|sour|different)\b"),
    re.compile(r"\bodou?r\b"),
    re.compile(r"\bcolou?r (?:changed|change)\b"),
    re.compile(r"\blooks? darker\b"),
    re.compile(r"\bmilky\b"),
    re.compile(r"\bmore clear\b"),
)

STORAGE_PATTERNS = (
    re.compile(r"\bfridge\b"),
    re.compile(r"\brefrigerat(?:ed|ion)\b"),
    re.compile(r"\bcountertop\b"),
    re.compile(r"\broom temperature\b"),
    re.compile(r"\btemperature excursion\b"),
    re.compile(r"\bstored cold\b"),
    re.compile(r"\bkept cold\b"),
)

QUESTION_REQUEST_PATTERNS = (
    re.compile(r"\bcan\b"),
    re.compile(r"\bshould\b"),
    re.compile(r"\bdoes\b"),
    re.compile(r"\bhow\b"),
    re.compile(r"\bis it (?:okay|ok|safe)\b"),
    re.compile(r"\bwants? to know\b"),
    re.compile(r"\basking whether\b"),
    re.compile(r"\basked whether\b"),
    re.compile(r"\bcorrect way\b"),
)

ADMINISTRATION_TOPIC_PATTERNS = (
    re.compile(r"\bwith food\b"),
    re.compile(r"\bwithout food\b"),
    re.compile(r"\babsorption\b"),
    re.compile(r"\bmix(?:ed|ing)? (?:in|into|with)\b"),
    re.compile(r"\badministration technique\b"),
    re.compile(r"\bcorrect dose\b"),
    re.compile(r"\bcombined in one solution\b"),
    re.compile(r"\bsyringe\b"),
    re.compile(r"\bdraws? up\b"),
)

ADMINISTRATION_TECHNIQUE_PATTERNS = (
    re.compile(r"\breading the syringe from the wrong side\b"),
    re.compile(r"\busing the syringe (?:incorrectly|wrong)\b"),
    re.compile(r"\bwrong syringe markings?\b"),
    re.compile(r"\bincorrect administration technique\b"),
    re.compile(r"\bmeasuring the dose incorrectly\b"),
)

QUANTITY_PATTERNS = (
    re.compile(r"\bshould have lasted\b"),
    re.compile(r"\bshould last\b"),
    re.compile(r"\bbottle (?:looked|looks) low\b"),
    re.compile(r"\bonly (?:a )?small amount remains\b"),
    re.compile(r"\bremaining amount\b"),
    re.compile(r"\bless medication\b"),
    re.compile(r"\bwrong quantity\b"),
    re.compile(r"\bquantity discrepancy\b"),
)

PALATABILITY_PATTERNS = (
    re.compile(r"\brefus(?:ed|es|ing)\b"),
    re.compile(r"\bdoes not like\b"),
    re.compile(r"\bdidn['’]t like\b"),
    re.compile(r"\bspit(?:s|ting)? (?:it|the liquid) out\b"),
    re.compile(r"\bdrool(?:s|ing|ed)?\b"),
    re.compile(r"\bfoaming at the mouth\b"),
    re.compile(r"\bfoaming\b"),
    re.compile(r"\bshak(?:es|ing|ed) (?:his|her|their) head\b"),
    re.compile(r"\bwill not take\b"),
    re.compile(r"\bpalatability\b"),
)

TRANSDERMAL_PATTERNS = (
    re.compile(r"\btransdermal\b"),
    re.compile(r"\bsores? in (?:the )?ears?\b"),
    re.compile(r"\bear sores?\b"),
    re.compile(r"\bapplication site\b"),
    re.compile(r"\bskin irritation\b"),
    re.compile(r"\birritated spots? inside (?:both )?ears?\b"),
)



def has_affirmed_hospitalization(text: str) -> bool:
    for match in HOSPITALIZATION_PATTERN.finditer(text):
        prefix = text[max(0, match.start() - 48):match.start()]
        if HOSPITALIZATION_NEGATION_PATTERN.search(prefix):
            continue
        return True
    return False


def require_text(value: str) -> str:
    text = value.strip()
    if not text:
        raise ValueError("text must not be blank")
    return text
