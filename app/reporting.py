from __future__ import annotations

from enum import Enum

from app.checklist_models import EvidenceCitation, IntakeChecklist
from app.schemas import ExpectedStructuredOutput


SYNTHETIC_BOUNDARY = (
    "SYNTHETIC PROOF OF CONCEPT — NO REAL RECORD ACCESS, NO REAL CUSTOMER DATA, "
    "AND NO EXTERNAL DRUG-REFERENCE ACCESS."
)


def format_intake_checklist(
    checklist: IntakeChecklist,
    *,
    debug: bool = False,
) -> str:
    lines = [
        "COMPOUNDING QUALITY INTAKE CHECKLIST",
        SYNTHETIC_BOUNDARY,
        "",
        "Concern:",
        checklist.concern_text,
        "",
        "Bottom line:",
        build_checklist_bottom_line(checklist),
        "",
        f"Likely concern type: {enum_value_or_unknown(checklist.likely_concern_type)}",
        f"Likely risk lane: {enum_value_or_unknown(checklist.likely_risk_lane)}",
        "",
        "What should be checked:",
    ]

    for item in checklist.review_checks:
        required = "required" if item.required else "optional"
        lines.append(f"- {item.check_name} ({required}): {item.rationale}")

    lines.extend(["", "Missing information to resolve before final disposition:"])
    lines.extend(format_bullets(checklist.missing_information))

    lines.extend(["", "Severe escalation triggers to rule out:"])
    lines.extend(format_bullets([trigger.value for trigger in checklist.escalation_triggers_to_rule_out]))

    lines.extend(["", "Evidence used for checklist:"])
    lines.extend(format_evidence(checklist.evidence, debug=debug))

    lines.extend(["", "Limitations:"])
    lines.extend(format_bullets(checklist.limitations))

    return "\n".join(lines)


def format_final_assessment(
    output: ExpectedStructuredOutput,
    evidence: list[EvidenceCitation],
    *,
    debug: bool = False,
) -> str:
    assessment = output.derived_assessment
    review_summary = output.review_summary

    lines = [
        "COMPOUNDING QUALITY FINAL CONSISTENCY SUMMARY",
        SYNTHETIC_BOUNDARY,
        "",
        "Bottom line:",
        build_final_bottom_line(output),
        "",
        "Intake:",
        output.raw_intake.concern_narrative,
        "",
        "What was checked:",
        f"- Record review result: {review_summary.record_review_result.value}",
        f"- Lot/batch pattern summary: {review_summary.lot_batch_pattern_summary.value}",
        f"- Inventory inspection result: {review_summary.inventory_inspection_result.value}",
        f"- API/reference review result: {review_summary.api_reference_review_result.value}",
        "",
        "What was not available / still limited:",
    ]

    unavailable_items = list(review_summary.missing_information) + list(review_summary.evidence_limitations)
    lines.extend(format_bullets(unavailable_items))

    lines.extend(
        [
            "",
            "Recommended review disposition:",
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
    )

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
    lines.extend(format_evidence(evidence, debug=debug))

    lines.extend(
        [
            "",
            "Limitations:",
            "- This is a synthetic proof of concept, not production policy.",
            "- The tool does not access real records, inventory, customer history, or external drug references.",
            "- Human pharmacist review remains the final decision point.",
        ]
    )

    return "\n".join(lines)


def build_checklist_bottom_line(checklist: IntakeChecklist) -> str:
    concern_type = enum_value_or_unknown(checklist.likely_concern_type)
    risk_lane = enum_value_or_unknown(checklist.likely_risk_lane)
    return (
        f"Initial screen suggests {concern_type} with {risk_lane} risk unless "
        "review findings identify a severe escalation trigger or unsupported evidence gap."
    )


def build_final_bottom_line(output: ExpectedStructuredOutput) -> str:
    assessment = output.derived_assessment
    return (
        f"Recommended disposition is {assessment.handling_path.value} with "
        f"{assessment.risk_lane.value} risk lane based on the supplied synthetic review findings."
    )


def format_evidence(
    evidence: list[EvidenceCitation],
    *,
    max_items: int = 5,
    debug: bool = False,
) -> list[str]:
    if not evidence:
        return ["- No evidence chunks were retrieved"]

    lines: list[str] = []

    for citation in evidence[:max_items]:
        line = (
            f"- {citation.source_id} | {citation.source_title} | "
            f"{citation.section_heading}"
        )

        if debug:
            line += (
                f" | score={citation.score} | "
                f"matched_terms={', '.join(citation.matched_terms)}"
            )

        lines.append(line)

    return lines


def format_bullets(values: list[str]) -> list[str]:
    if not values:
        return ["- None"]

    return [f"- {value}" for value in values]


def enum_value_or_unknown(value: object | None) -> str:
    if value is None:
        return "unknown"

    if isinstance(value, Enum):
        return str(value.value)

    return str(value)


def enum_value_or_none(value: object | None) -> str:
    if value is None:
        return "None"

    if isinstance(value, Enum):
        return str(value.value)

    return str(value)
