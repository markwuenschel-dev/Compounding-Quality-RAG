from __future__ import annotations

from enum import Enum

from app.checklist_models import EvidenceCitation, IntakeChecklist
from app.schemas import ExpectedStructuredOutput


def format_intake_checklist(checklist: IntakeChecklist) -> str:
    lines = [
        "COMPOUNDING QUALITY INTAKE CHECKLIST",
        "",
        "Concern:",
        checklist.concern_text,
        "",
        f"Likely concern type: {enum_value_or_unknown(checklist.likely_concern_type)}",
        f"Likely risk lane: {enum_value_or_unknown(checklist.likely_risk_lane)}",
        "",
        "Review checks:",
    ]

    for item in checklist.review_checks:
        required = "required" if item.required else "optional"
        lines.append(f"- {item.check_name} ({required}): {item.rationale}")

    lines.extend(["", "Missing information:"])
    lines.extend(format_bullets(checklist.missing_information))

    lines.extend(["", "Escalation triggers to rule out:"])
    lines.extend(format_bullets([trigger.value for trigger in checklist.escalation_triggers_to_rule_out]))

    lines.extend(["", "Evidence:"])
    lines.extend(format_evidence(checklist.evidence))

    lines.extend(["", "Limitations:"])
    lines.extend(format_bullets(checklist.limitations))

    return "\n".join(lines)


def format_final_assessment(output: ExpectedStructuredOutput, evidence: list[EvidenceCitation]) -> str:
    assessment = output.derived_assessment
    review_summary = output.review_summary

    lines = [
        "COMPOUNDING QUALITY FINAL CONSISTENCY SUMMARY",
        "",
        "Intake:",
        output.raw_intake.concern_narrative,
        "",
        "Reviewer findings:",
        f"- Record review result: {review_summary.record_review_result.value}",
        f"- Lot/batch pattern summary: {review_summary.lot_batch_pattern_summary.value}",
        f"- Inventory inspection result: {review_summary.inventory_inspection_result.value}",
        f"- API/reference review result: {review_summary.api_reference_review_result.value}",
        "",
        "Final structured assessment:",
        f"- Classification: {assessment.reviewer_assigned_classification.value}",
        f"- Category: {enum_value_or_none(assessment.reviewer_assigned_category)}",
        f"- Subcategory: {enum_value_or_none(assessment.reviewer_assigned_subcategory)}",
        f"- Concern type: {assessment.concern_type.value}",
        f"- Risk lane: {assessment.risk_lane.value}",
        f"- Review scope: {assessment.review_scope.value}",
        f"- Handling path: {assessment.handling_path.value}",
        f"- Resolution review required: {assessment.resolution_review_required}",
        "",
        "Escalation triggers:",
    ]

    if assessment.escalation_triggers:
        lines.extend(format_bullets([trigger.value for trigger in assessment.escalation_triggers]))
    else:
        lines.append("- None identified from supplied review findings")

    lines.extend(["", "Resolution options:"])
    if assessment.resolution_options:
        lines.extend(format_bullets([option.value for option in assessment.resolution_options]))
    else:
        lines.append("- None")

    lines.extend(["", "Rationale:", assessment.rationale])

    lines.extend(["", "Evidence used:"])
    lines.extend(format_evidence(evidence))

    lines.extend(
        [
            "",
            "Limitations:",
            "- This is a synthetic proof of concept, not production policy.",
            "- The tool does not access real records, inventory, customer history, or external drug references.",
            "- Human pharmacist review remains the final decision point.",
        ]
    )
    separator = ''
    return separator.join(lines)


def format_evidence(evidence: list[EvidenceCitation], *, max_items: int = 5) -> list[str]:
    if not evidence:
        return ["- No evidence chunks were retrieved"]

    lines: list[str] = []

    for citation in evidence[:max_items]:
        lines.append(
            f"- {citation.source_id} | {citation.source_title} | "
            f"{citation.section_heading} | score={citation.score}"
        )

    return lines


def format_bullets(values: list[str]) -> list[str]:
    if not values:
        return ["- None"]

    return [f"- {value}" for value in values]


def enum_value_or_unknown(value: Enum | None) -> str:
    if value is None:
        return "unknown"
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


def enum_value_or_none(value: Enum | None) -> str:
    if value is None:
        return "None"
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)
