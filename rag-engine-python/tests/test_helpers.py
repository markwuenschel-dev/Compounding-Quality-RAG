from __future__ import annotations

import json
from copy import deepcopy
from enum import StrEnum
from pathlib import Path
from typing import Any

from app.schemas import (
    ApiReferenceReviewResult,
    DosageForm,
    EscalationTrigger,
    ExpectedStructuredOutput,
    FormalCategory,
    FormalClassification,
    FormalSubcategory,
    HandlingPath,
    IntakeSource,
    InventoryInspectionResult,
    LotBatchPatternSummary,
    RecordReviewResult,
    ResolutionOption,
    ReviewScope,
    RiskLane,
    Species,
    SubmitterRole,
    SubmissionPurpose,
)


SCALAR_ENUM_FIELDS: dict[tuple[str, ...], type[StrEnum]] = {
    ("raw_intake", "intake_source"): IntakeSource,
    ("raw_intake", "submitter_role"): SubmitterRole,
    ("raw_intake", "submission_purpose"): SubmissionPurpose,
    ("raw_intake", "submitter_selected_classification"): FormalClassification,
    ("product_context", "species"): Species,
    ("product_context", "dosage_form"): DosageForm,
    ("review_summary", "record_review_result"): RecordReviewResult,
    ("review_summary", "lot_batch_pattern_summary"): LotBatchPatternSummary,
    ("review_summary", "inventory_inspection_result"): InventoryInspectionResult,
    ("review_summary", "api_reference_review_result"): ApiReferenceReviewResult,
    ("derived_assessment", "reviewer_assigned_classification"): FormalClassification,
    ("derived_assessment", "reviewer_assigned_category"): FormalCategory,
    ("derived_assessment", "reviewer_assigned_subcategory"): FormalSubcategory,
    ("derived_assessment", "concern_type"): __import__("app.schemas", fromlist=["ConcernType"]).ConcernType,
    ("derived_assessment", "risk_lane"): RiskLane,
    ("derived_assessment", "review_scope"): ReviewScope,
    ("derived_assessment", "handling_path"): HandlingPath,
}

LIST_ENUM_FIELDS: dict[tuple[str, ...], type[StrEnum]] = {
    ("review_summary", "severe_triggers_observed"): EscalationTrigger,
    ("derived_assessment", "escalation_triggers"): EscalationTrigger,
    ("derived_assessment", "resolution_options"): ResolutionOption,
}


def load_expected_output_normalized(path: Path) -> ExpectedStructuredOutput:
    return ExpectedStructuredOutput.model_validate(load_normalized_payload(path))


def load_normalized_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return normalize_payload_to_schema_enums(payload)


def write_normalized_expected_output(source_path: Path, target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / source_path.name
    payload = load_normalized_payload(source_path)
    target_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return target_path


def write_normalized_expected_outputs_dir(source_dir: Path, target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)

    for source_path in source_dir.glob("*.json"):
        write_normalized_expected_output(source_path, target_dir)

    return target_dir


def normalize_payload_to_schema_enums(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(payload)

    for path, enum_cls in SCALAR_ENUM_FIELDS.items():
        normalize_scalar_field(normalized, path, enum_cls)

    for path, enum_cls in LIST_ENUM_FIELDS.items():
        normalize_list_field(normalized, path, enum_cls)

    return normalized


def normalize_scalar_field(
    payload: dict[str, Any],
    path: tuple[str, ...],
    enum_cls: type[StrEnum],
) -> None:
    parent = get_parent(payload, path)

    if parent is None:
        return

    field_name = path[-1]

    if field_name not in parent:
        return

    parent[field_name] = normalize_enum_value(parent[field_name], enum_cls)


def normalize_list_field(
    payload: dict[str, Any],
    path: tuple[str, ...],
    enum_cls: type[StrEnum],
) -> None:
    parent = get_parent(payload, path)

    if parent is None:
        return

    field_name = path[-1]
    value = parent.get(field_name)

    if value is None:
        parent[field_name] = []
        return

    if not isinstance(value, list):
        return

    parent[field_name] = [
        normalize_enum_value(item, enum_cls)
        for item in value
    ]


def normalize_enum_value(value: Any, enum_cls: type[StrEnum]) -> Any:
    if value is None:
        return None

    if isinstance(value, enum_cls):
        return value.value

    if not isinstance(value, str):
        return value

    value_key = value.lower()
    by_value = {member.value.lower(): member.value for member in enum_cls}
    by_name = {member.name.lower(): member.value for member in enum_cls}

    return by_value.get(value_key) or by_name.get(value_key) or value


def get_parent(payload: dict[str, Any], path: tuple[str, ...]) -> dict[str, Any] | None:
    current: Any = payload

    for key in path[:-1]:
        if not isinstance(current, dict):
            return None

        current = current.get(key)

    return current if isinstance(current, dict) else None