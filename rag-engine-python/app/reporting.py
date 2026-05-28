from __future__ import annotations

from enum import Enum
import textwrap

from app.checklist_models import EvidenceCitation, IntakeChecklist
from app.schemas import ExpectedStructuredOutput

DISPLAY_ACRONYMS = {
    "qre": "QRE",
    "ade": "ADE",
    "api": "API",
    "bud": "BUD",
}

SYNTHETIC_BOUNDARY = (
    "Demo boundary: synthetic proof of concept only. No real record access, "
    "no real customer or patient data, and no external drug-reference access."
)


def format_intake_checklist(
    checklist: IntakeChecklist,
    *,
    debug: bool = False,
) -> str:
    lines = [
        "PHASE 1 — INTAKE CHECKLIST",
        SYNTHETIC_BOUNDARY,
        "",
        "INITIAL SUMMARY",
        wrap(build_checklist_bottom_line(checklist)),
        "",
        "CONCERN RECEIVED",
        quote_block(checklist.concern_text),
        "",
        "INITIAL CLASSIFICATION",
        format_field("Concern type", humanize(checklist.likely_concern_type)),
        format_field("Risk lane", humanize(checklist.likely_risk_lane)),
        "",
        "REVIEW CHECKLIST",
    ]

    for index, item in enumerate(checklist.review_checks, start=1):
        required = "Required" if item.required else "Optional"
        lines.append(f"{index}. {item.check_name} [{required}]")
        lines.append(wrap(item.rationale, indent=3))

    lines.extend(
        [
            "",
            "MISSING INFORMATION",
            *format_bullets(checklist.missing_information),
            "",
            "ESCALATION TRIGGERS TO RULE OUT",
            *format_bullets(
                [humanize(trigger) for trigger in checklist.escalation_triggers_to_rule_out]
            ),
            "",
            "EVIDENCE USED",
            *format_evidence(checklist.evidence, debug=debug),
            "",
            "LIMITATIONS",
            *format_bullets(checklist.limitations),
        ]
    )

    return "\n".join(lines)


def format_final_assessment(
    output: ExpectedStructuredOutput,
    evidence: list[EvidenceCitation],
    *,
    debug: bool = False,
) -> str:
    assessment = output.derived_assessment
    review_summary = output.review_summary
    unavailable_items = list(review_summary.missing_information) + list(
        review_summary.evidence_limitations
    )

    lines = [
        "PHASE 2 — FINAL REVIEW-SUPPORT SUMMARY",
        SYNTHETIC_BOUNDARY,
        "",
        "FINAL SUMMARY",
        wrap(build_final_bottom_line(output)),
        "",
        "INTAKE",
        quote_block(output.raw_intake.concern_narrative),
        "",
        "REVIEW FINDINGS ENTERED",
        format_field("Record review", humanize(review_summary.record_review_result)),
        format_field("Lot/batch pattern", humanize(review_summary.lot_batch_pattern_summary)),
        format_field("Inventory inspection", humanize(review_summary.inventory_inspection_result)),
        format_field("API/reference review", humanize(review_summary.api_reference_review_result)),
        "",
        "RECOMMENDED DISPOSITION",
        format_field("Classification", humanize(assessment.reviewer_assigned_classification)),
        format_field("Category", humanize_or_none(assessment.reviewer_assigned_category)),
        format_field("Subcategory", humanize_or_none(assessment.reviewer_assigned_subcategory)),
        format_field("Concern type", humanize(assessment.concern_type)),
        format_field("Risk lane", humanize(assessment.risk_lane)),
        format_field("Review scope", humanize(assessment.review_scope)),
        format_field("Handling path", humanize(assessment.handling_path)),
        format_field("Resolution review required", yes_no(assessment.resolution_review_required)),
        "",
        "WHAT WAS NOT AVAILABLE / STILL LIMITED",
        *format_bullets(unavailable_items),
        "",
        "ESCALATION TRIGGERS",
    ]

    if assessment.escalation_triggers:
        lines.extend(format_bullets([humanize(trigger) for trigger in assessment.escalation_triggers]))
    else:
        lines.append("• None identified from supplied review findings")

    lines.extend(["", "RESOLUTION OPTIONS"])
    if assessment.resolution_options:
        lines.extend(format_bullets([humanize(option) for option in assessment.resolution_options]))
    else:
        lines.append("• None")

    lines.extend(
        [
            "",
            "RATIONALE",
            wrap(assessment.rationale),
            "",
            "EVIDENCE USED",
            *format_evidence(evidence, debug=debug),
            "",
            "FINAL LIMITATIONS",
            "• Synthetic proof of concept, not production policy.",
            "• No access to real records, inventory, customer history, or external drug references.",
            "• Human pharmacist review remains the final decision point.",
        ]
    )

    return "\n".join(lines)


def build_checklist_bottom_line(checklist: IntakeChecklist) -> str:
    concern_type = humanize(checklist.likely_concern_type)
    risk_lane = humanize(checklist.likely_risk_lane)
    return (
        f"Initial screen suggests {concern_type} with {risk_lane} risk. "
        "This is a checklist, not a final conclusion; final routing depends on "
        "review findings and confirmed escalation triggers."
    )


def build_final_bottom_line(output: ExpectedStructuredOutput) -> str:
    assessment = output.derived_assessment
    return (
        f"Recommended path: {humanize(assessment.handling_path)}. "
        f"Risk lane: {humanize(assessment.risk_lane)}. "
        "Recommendation is based only on the supplied synthetic review findings."
    )


def format_evidence(
    evidence: list[EvidenceCitation],
    *,
    max_items: int = 5,
    debug: bool = False,
) -> list[str]:
    if not evidence:
        return ["• No evidence chunks were retrieved"]

    lines: list[str] = []

    for index, citation in enumerate(evidence[:max_items], start=1):
        lines.append(
            f"{index}. {citation.source_id} — {citation.source_title}"
        )
        lines.append(f"   Section: {citation.section_heading}")

        if debug:
            lines.append(
                "   Debug: "
                f"score={citation.score}; matched_terms={', '.join(citation.matched_terms)}"
            )

    if len(evidence) > max_items:
        lines.append(f"• {len(evidence) - max_items} additional evidence item(s) hidden")

    return lines


def format_bullets(values: list[str]) -> list[str]:
    if not values:
        return ["• None"]

    return [f"• {value}" for value in values]


def format_field(label: str, value: str) -> str:
    return f"{label + ':':<30} {value}"


def humanize_or_none(value: object | None) -> str:
    if value is None:
        return "None"

    return humanize(value)


def humanize(value: object | None) -> str:
    if value is None:
        return "Unknown"

    raw_value = str(value.value) if isinstance(value, Enum) else str(value)
    words = raw_value.replace("_", " ").strip().split()

    return " ".join(
        DISPLAY_ACRONYMS.get(word.lower(), word.capitalize())
        for word in words
    )


def yes_no(value: bool) -> str:
    return "Yes" if value else "No"


def wrap(text: str, *, indent: int = 0, width: int = 96) -> str:
    prefix = " " * indent
    return textwrap.fill(
        text,
        width=width,
        initial_indent=prefix,
        subsequent_indent=prefix,
    )


def quote_block(text: str) -> str:
    wrapped = wrap(text, indent=2)
    return "\n".join(f"| {line[2:]}" if line.startswith("  ") else f"| {line}" for line in wrapped.splitlines())
