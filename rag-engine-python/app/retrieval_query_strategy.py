from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator


StrategyName = Literal[
    "raw",
    "deterministic_expansion",
    "nano_structured",
]


class RetrievalQueryIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    original_text: str = Field(min_length=1)
    search_text: str = Field(min_length=1)
    issue_tags: list[str] = Field(default_factory=list)
    required_topics: list[str] = Field(default_factory=list)
    excluded_topics: list[str] = Field(default_factory=list)
    strategy: StrategyName

    @field_validator(
        "original_text",
        "search_text",
        mode="before",
    )
    @classmethod
    def strip_required_text(cls, value: object) -> str:
        text = str(value).strip()
        if not text:
            raise ValueError("text must not be blank")
        return text

    @field_validator(
        "issue_tags",
        "required_topics",
        "excluded_topics",
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
    intent: RetrievalQueryIntent


class RetrievalQueryStrategy(Protocol):
    name: StrategyName

    def build(self, concern_text: str) -> RetrievalQueryIntent:
        ...


class JsonCompletionClient(Protocol):
    def complete_json(self, prompt: str) -> str:
        ...


class RawQueryStrategy:
    name: StrategyName = "raw"

    def build(self, concern_text: str) -> RetrievalQueryIntent:
        text = require_text(concern_text)
        return RetrievalQueryIntent(
            original_text=text,
            search_text=text,
            strategy=self.name,
        )


class DeterministicExpansionStrategy:
    name: StrategyName = "deterministic_expansion"

    def build(self, concern_text: str) -> RetrievalQueryIntent:
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
                    "device_review",
                    "quality_review",
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

        return RetrievalQueryIntent(
            original_text=text,
            search_text=search_text,
            issue_tags=issue_tags,
            required_topics=required_topics,
            excluded_topics=excluded_topics,
            strategy=self.name,
        )


class NanoStructuredQueryStrategy:
    name: StrategyName = "nano_structured"

    def __init__(
        self,
        client: JsonCompletionClient,
    ) -> None:
        self._client = client

    def build(self, concern_text: str) -> RetrievalQueryIntent:
        text = require_text(concern_text)
        payload = parse_json_object(
            self._client.complete_json(
                build_nano_prompt(text)
            )
        )
        generated_search_text = require_text(
            str(payload["search_text"])
        )

        return RetrievalQueryIntent.model_validate(
            {
                "original_text": text,
                "search_text": (
                    f"{text}\n\nRetrieval concepts: "
                    f"{generated_search_text}"
                ),
                "issue_tags": payload.get("issue_tags", []),
                "required_topics": payload.get(
                    "required_topics",
                    [],
                ),
                "excluded_topics": payload.get(
                    "excluded_topics",
                    [],
                ),
                "strategy": self.name,
            }
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
    ) -> RetrievalQueryIntent | None:
        key = cache_key(
            question_id,
            concern_text,
            model,
        )
        entry = self._entries.get(key)

        if entry is None:
            return None

        return entry.intent

    def put(
        self,
        *,
        question_id: str,
        concern_text: str,
        model: str,
        intent: RetrievalQueryIntent,
    ) -> None:
        entry = CachedRetrievalIntent(
            question_id=question_id,
            input_hash=input_hash(concern_text),
            model=model,
            intent=intent,
        )
        self._entries[
            cache_key(
                question_id,
                concern_text,
                model,
            )
        ] = entry

    def flush(self) -> None:
        self._path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
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


def build_nano_prompt(concern_text: str) -> str:
    return f"""Convert the complaint into retrieval intent.

Return one JSON object with exactly these keys:
- search_text: concise search-oriented text
- issue_tags: controlled snake_case tags
- required_topics: policy topics that relevant SOPs should cover
- excluded_topics: topics that would materially misroute the case

Rules:
- Preserve reported facts without deciding causality.
- Hospitalization is a severe escalation topic.
- Shortness of breath or collapse alone is clinical context, not automatic severe escalation.
- Ingredient-list and supplier-source requests need disclosure-boundary language.
- Do not invent record, lot, inventory, or reference-review findings.
- Do not include customer, clinic, patient, or pet identifiers.
- Keep search_text under 80 words.

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
        raise ValueError("nano retrieval intent must be a JSON object")

    return payload


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
            entry = CachedRetrievalIntent.model_validate_json(
                line
            )
        except ValueError as exc:
            raise ValueError(
                f"{path} line {line_number} "
                "is not a valid cache entry"
            ) from exc

        entries[
            cache_key(
                entry.question_id,
                entry.intent.original_text,
                entry.model,
            )
        ] = entry

    return entries


def input_hash(concern_text: str) -> str:
    return hashlib.sha256(
        require_text(concern_text).encode("utf-8")
    ).hexdigest()


def cache_key(
    question_id: str,
    concern_text: str,
    model: str,
) -> str:
    return "::".join(
        (
            require_text(question_id),
            require_text(model),
            input_hash(concern_text),
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
        normalized = " ".join(
            value.split()
        ).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        output.append(normalized)

    return output


def contains_any(
    text: str,
    terms: tuple[str, ...],
) -> bool:
    return any(term in text for term in terms)


def require_text(value: str) -> str:
    text = value.strip()
    if not text:
        raise ValueError("text must not be blank")
    return text
