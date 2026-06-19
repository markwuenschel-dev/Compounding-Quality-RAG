from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.retrieval_intent import (
    INTENT_SCHEMA_VERSION,
    NanoIntentDetector,
    RetrievalIntent,
    RetrievalIntentDetector,
    SemanticRetrievalIntent,
    RuleIntentDetector,
    derive_retrieval_intent,
    map_intent_to_search_text,
)


StrategyName = Literal[
    "raw",
    "deterministic_expansion",
    "rule_intent",
    "nano_intent",
]


class BuiltRetrievalQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    original_text: str = Field(min_length=1)
    search_text: str = Field(min_length=1)
    strategy: StrategyName
    semantic_intent: SemanticRetrievalIntent | None = None
    intent: RetrievalIntent | None = None
    legacy_issue_tags: list[str] = Field(default_factory=list)
    legacy_required_topics: list[str] = Field(default_factory=list)
    legacy_excluded_topics: list[str] = Field(default_factory=list)

    @field_validator("original_text", "search_text", mode="before")
    @classmethod
    def strip_required_text(cls, value: object) -> str:
        text = str(value).strip()
        if not text:
            raise ValueError("text must not be blank")
        return text

    @field_validator(
        "legacy_issue_tags",
        "legacy_required_topics",
        "legacy_excluded_topics",
        mode="before",
    )
    @classmethod
    def normalize_terms(cls, value: object) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise TypeError("term collections must be lists")

        output: list[str] = []
        seen: set[str] = set()
        for raw_term in value:
            term = normalize_term(str(raw_term))
            if not term or term in seen:
                continue
            seen.add(term)
            output.append(term)
        return output


class CachedRetrievalIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(min_length=1)
    input_hash: str = Field(min_length=64, max_length=64)
    model: str = Field(min_length=1)
    intent_schema_version: str = Field(min_length=1)
    semantic_intent: SemanticRetrievalIntent


class RetrievalQueryStrategy(Protocol):
    @property
    def name(self) -> StrategyName:
        ...

    def build(self, concern_text: str) -> BuiltRetrievalQuery:
        ...


class RawQueryStrategy:
    name: Literal["raw"] = "raw"

    def build(self, concern_text: str) -> BuiltRetrievalQuery:
        text = require_text(concern_text)
        return BuiltRetrievalQuery(
            original_text=text,
            search_text=text,
            strategy=self.name,
        )


class DeterministicExpansionStrategy:
    name: Literal["deterministic_expansion"] = "deterministic_expansion"

    def build(self, concern_text: str) -> BuiltRetrievalQuery:
        text = require_text(concern_text)
        normalized = text.lower()
        search_terms: list[str] = []
        issue_tags: list[str] = []
        required_topics: list[str] = []
        excluded_topics: list[str] = []

        def add(
            *,
            terms: tuple[str, ...] = (),
            tags: tuple[str, ...] = (),
            required: tuple[str, ...] = (),
            excluded: tuple[str, ...] = (),
        ) -> None:
            search_terms.extend(terms)
            issue_tags.extend(tags)
            required_topics.extend(required)
            excluded_topics.extend(excluded)

        if contains_any(
            normalized,
            (
                "hospitalized",
                "hospitalised",
                "hospitalization",
                "hospitalisation",
                "emergency hospital",
                "admitted",
                "er visit",
            ),
        ):
            add(
                terms=(
                    "hospitalization",
                    "adverse event",
                    "severe escalation",
                ),
                tags=(
                    "adverse_event",
                    "pet_hospitalization",
                ),
                required=(
                    "adverse_event_review",
                    "severe_escalation",
                ),
            )

        if contains_any(
            normalized,
            (
                "blood in the stool",
                "bloody stool",
                "vomit",
                "vomiting",
                "diarrhea",
            ),
        ):
            add(
                terms=(
                    "gastrointestinal adverse event",
                    "vomiting",
                    "diarrhea",
                    "blood in stool",
                ),
                tags=(
                    "adverse_event",
                    "gastrointestinal",
                ),
                required=("adverse_event_review",),
            )

        if contains_any(
            normalized,
            (
                "difficulty walking",
                "unable to walk",
                "weakness",
                "ataxia",
                "neurologic",
                "neurological",
            ),
        ):
            add(
                terms=(
                    "neurologic adverse event",
                    "difficulty walking",
                    "weakness",
                    "ataxia",
                ),
                tags=(
                    "adverse_event",
                    "neurologic_signs",
                ),
                required=("adverse_event_review",),
                excluded=("routine_frontline_guidance",),
            )

        if contains_any(
            normalized,
            (
                "short of breath",
                "shortness of breath",
                "difficulty breathing",
                "respiratory distress",
                "gagging",
            ),
        ):
            add(
                terms=(
                    "respiratory adverse event",
                    "shortness of breath",
                    "pharmacist outreach",
                ),
                tags=(
                    "adverse_event",
                    "respiratory_context",
                ),
                required=(
                    "adverse_event_review",
                    "pharmacist_outreach",
                ),
                excluded=("automatic_severe_escalation",),
            )

        if contains_any(
            normalized,
            (
                "inactive ingredient",
                "inactive ingredients",
                "full ingredient list",
                "proprietary formula",
                "specific ingredients",
            ),
        ):
            add(
                terms=(
                    "inactive ingredient disclosure",
                    "proprietary formula",
                    "unsupported information boundary",
                    "frontline pharmacist response",
                ),
                tags=(
                    "ingredient_question",
                    "disclosure_boundary",
                ),
                required=(
                    "ingredient_guidance",
                    "public_corpus_boundary",
                ),
                excluded=("leadership_escalation",),
            )

        if contains_any(
            normalized,
            (
                "where we source",
                "where are ingredients sourced",
                "supplier",
                "manufacturer",
                "source the ingredients",
                "ingredient source",
            ),
        ):
            add(
                terms=(
                    "supplier manufacturer disclosure",
                    "source information boundary",
                    "unsupported public corpus",
                    "frontline pharmacist response",
                ),
                tags=(
                    "supplier_question",
                    "disclosure_boundary",
                ),
                required=(
                    "public_corpus_boundary",
                    "frontline_pharmacist_response",
                ),
                excluded=("leadership_escalation",),
            )

        if contains_any(
            normalized,
            (
                "beyond-use",
                "beyond use",
                "after bud",
                "degradation rate",
                "expired",
                "expiration",
            ),
        ) or re.search(r"\bbud\b", normalized):
            add(
                terms=(
                    "beyond use date",
                    "stability limitation",
                    "external reference boundary",
                ),
                tags=("bud_question",),
                required=(
                    "bud_guidance",
                    "reference_boundary",
                ),
            )

        if contains_any(
            normalized,
            (
                "pen",
                "click",
                "clicks",
                "not dispensing",
                "nothing came out",
                "less medication",
                "air bubble",
                "leaking",
            ),
        ):
            add(
                terms=(
                    "dispensing device",
                    "pen function",
                    "quality review",
                    "replacement",
                ),
                tags=("device_concern",),
                required=(
                    "quality_review",
                    "trend_review",
                ),
            )

        if contains_any(
            normalized,
            (
                "therapeutic levels",
                "not adjusting",
                "not effective",
                "not working",
                "lack of efficacy",
                "worsening bloodwork",
            ),
        ):
            add(
                terms=(
                    "lack of efficacy",
                    "therapeutic response",
                    "dose administration review",
                    "external reference",
                ),
                tags=("efficacy_concern",),
                required=(
                    "administration_review",
                    "reference_review",
                ),
                excluded=("routine_resolution",),
            )

        expanded_terms = unique_terms(search_terms)
        search_text = text
        if expanded_terms:
            search_text = (
                f"{text}\n\nRetrieval concepts: "
                f"{' '.join(expanded_terms)}"
            )

        return BuiltRetrievalQuery(
            original_text=text,
            search_text=search_text,
            strategy=self.name,
            legacy_issue_tags=issue_tags,
            legacy_required_topics=required_topics,
            legacy_excluded_topics=excluded_topics,
        )


class RuleIntentQueryStrategy:
    name: Literal["rule_intent"] = "rule_intent"

    def __init__(
        self,
        detector: RetrievalIntentDetector | None = None,
    ) -> None:
        self._detector = detector or RuleIntentDetector()

    def build(self, concern_text: str) -> BuiltRetrievalQuery:
        text = require_text(concern_text)
        semantic_intent = self._detector.detect(text)
        return build_query_from_semantic_intent(
            text,
            semantic_intent,
            strategy=self.name,
        )


class NanoIntentQueryStrategy:
    name: Literal["nano_intent"] = "nano_intent"

    def __init__(self, detector: NanoIntentDetector) -> None:
        self._detector = detector

    def build(self, concern_text: str) -> BuiltRetrievalQuery:
        text = require_text(concern_text)
        semantic_intent = self._detector.detect(text)
        return build_query_from_semantic_intent(
            text,
            semantic_intent,
            strategy=self.name,
    )


def build_query_from_intent(
    concern_text: str,
    intent: RetrievalIntent,
    *,
    strategy: Literal["rule_intent", "nano_intent"],
) -> BuiltRetrievalQuery:
    text = require_text(concern_text)
    return BuiltRetrievalQuery(
        original_text=text,
        search_text=map_intent_to_search_text(text, intent),
        strategy=strategy,
        intent=intent,
    )

def build_query_from_semantic_intent(
    concern_text: str,
    semantic_intent: SemanticRetrievalIntent,
    *,
    strategy: Literal["rule_intent", "nano_intent"],
) -> BuiltRetrievalQuery:
    text = require_text(concern_text)
    intent = derive_retrieval_intent(semantic_intent)

    return BuiltRetrievalQuery(
        original_text=text,
        search_text=map_intent_to_search_text(text, intent),
        strategy=strategy,
        semantic_intent=semantic_intent,
        intent=intent,
    )


class RetrievalIntentCache:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._entries = load_cache_entries(path)

    def get(
        self,
        *,
        question_id: str,
        concern_text: str,
        model: str,
        intent_schema_version: str = INTENT_SCHEMA_VERSION,
    ) -> SemanticRetrievalIntent | None:
        key = cache_key(
            question_id,
            concern_text,
            model,
            intent_schema_version,
        )
        entry = self._entries.get(key)
        if entry is None:
            return None
        return entry.semantic_intent

    def put(
        self,
        *,
        question_id: str,
        concern_text: str,
        model: str,
        semantic_intent: SemanticRetrievalIntent,
        intent_schema_version: str = INTENT_SCHEMA_VERSION,
    ) -> None:
        entry = CachedRetrievalIntent(
            question_id=question_id,
            input_hash=input_hash(concern_text),
            model=model,
            intent_schema_version=intent_schema_version,
            semantic_intent=semantic_intent,
        )
        self._entries[
            cache_key(
                question_id,
                concern_text,
                model,
                intent_schema_version,
            )
        ] = entry

    def flush(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self._path.with_suffix(
            self._path.suffix + ".tmp"
        )
        lines = [
            entry.model_dump_json()
            for _, entry in sorted(self._entries.items())
        ]
        temporary_path.write_text(
            "\n".join(lines) + ("\n" if lines else ""),
            encoding="utf-8",
        )
        temporary_path.replace(self._path)


def load_cache_entries(
    path: Path,
) -> dict[str, CachedRetrievalIntent]:
    if not path.exists():
        return {}

    entries: dict[str, CachedRetrievalIntent] = {}
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not line.strip():
            continue
        try:
            entry = CachedRetrievalIntent.model_validate_json(line)
        except ValueError as exc:
            raise ValueError(
                f"{path} line {line_number} is not a valid cache entry"
            ) from exc

        entries[
            cache_key(
                entry.question_id,
                entry.input_hash,
                entry.model,
                entry.intent_schema_version,
                input_is_hash=True,
            )
        ] = entry
    return entries


def input_hash(concern_text: str) -> str:
    return hashlib.sha256(
        require_text(concern_text).encode("utf-8")
    ).hexdigest()


def cache_key(
    question_id: str,
    concern_text_or_hash: str,
    model: str,
    intent_schema_version: str,
    *,
    input_is_hash: bool = False,
) -> str:
    hashed = (
        concern_text_or_hash
        if input_is_hash
        else input_hash(concern_text_or_hash)
    )
    return "::".join(
        (
            require_text(question_id),
            require_text(model),
            require_text(intent_schema_version),
            hashed,
        )
    )


def normalize_term(value: str) -> str:
    return re.sub(
        r"_+",
        "_",
        re.sub(
            r"[^a-z0-9]+",
            "_",
            value.strip().lower(),
        ),
    ).strip("_")


def unique_terms(values: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = " ".join(value.split()).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        output.append(normalized)
    return output


def contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def require_text(value: str) -> str:
    text = value.strip()
    if not text:
        raise ValueError("text must not be blank")
    return text
