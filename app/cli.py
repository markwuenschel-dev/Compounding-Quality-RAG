from __future__ import annotations

from enum import Enum
from typing import TypeVar

from app.checklist import build_intake_checklist
from app.final_assessment import build_final_assessment
from app.reporting import format_final_assessment, format_intake_checklist
from app.schemas import (
    ApiReferenceReviewResult,
    InventoryInspectionResult,
    LotBatchPatternSummary,
    RecordReviewResult,
    ReviewSummary,
    EscalationTrigger
)
from app.llm_client import LLMClientError, openai_json_client_from_env
from app.review_summary_extraction import (
    ReviewSummaryExtractionError,
    extract_review_summary,
)

EnumType = TypeVar("EnumType", bound=Enum)


def main() -> None:
    print("Compounding Quality RAG CLI Demo")
    print("Synthetic proof of concept only. Do not enter real customer, patient, or proprietary data.")
    print()

    concern_text = input("Enter concern text: ").strip()
    checklist = build_intake_checklist(concern_text)

    print()
    print(format_intake_checklist(checklist))
    print()

    proceed = input("Enter investigation findings for final review summary? [y/N]: ").strip().lower()

    if proceed != "y":
        print("Stopping after Phase 1 checklist.")
        return

    mode = choose_phase_two_input_mode()

    if mode == "manual":
        review_summary = collect_review_summary()
    else:
        review_summary = collect_review_summary_with_llm()

    final_output = build_final_assessment(checklist=checklist, review_summary=review_summary)

    print()
    print(format_final_assessment(final_output, checklist.evidence))

def collect_review_summary() -> ReviewSummary:
    record_review_result = choose_enum(
        "Record review result",
        RecordReviewResult,
    )
    lot_batch_pattern_summary = choose_enum(
        "Lot/batch pattern summary",
        LotBatchPatternSummary,
    )
    inventory_inspection_result = choose_enum(
        "Inventory inspection result",
        InventoryInspectionResult,
    )
    api_reference_review_result = choose_enum(
        "API/reference review result",
        ApiReferenceReviewResult,
    )
    severe_triggers_observed = choose_multiple_enum(
        "Severe escalation triggers observed",
        EscalationTrigger,
    )

    customer_context_summary = input(
        "Customer context summary, if available: "
    ).strip() or None

    missing_information = collect_list("Missing information item")
    evidence_limitations = collect_list("Evidence limitation")

    return ReviewSummary(
        record_review_result=record_review_result,
        lot_batch_pattern_summary=lot_batch_pattern_summary,
        inventory_inspection_result=inventory_inspection_result,
        customer_context_summary=customer_context_summary,
        api_reference_review_result=api_reference_review_result,
        severe_triggers_observed=severe_triggers_observed,
        missing_information=missing_information,
        evidence_limitations=evidence_limitations,
    )

def choose_phase_two_input_mode() -> str:
    while True:
        print()
        print("How do you want to enter Phase 2 findings?")
        print("1. Controlled menu fields")
        print("2. Free-text reviewer note through OpenAI extraction")

        choice = input("Select number: ").strip()

        if choice == "1":
            return "manual"

        if choice == "2":
            return "llm"

        print("Please enter 1 or 2.")


def collect_review_summary_with_llm() -> ReviewSummary:
    reviewer_note = collect_multiline_reviewer_note()
    client = openai_json_client_from_env()

    try:
        return extract_review_summary(reviewer_note, client)
    except (LLMClientError, ReviewSummaryExtractionError) as exc:
        raise RuntimeError(
            "Unable to extract a valid review summary from the reviewer note."
        ) from exc


def collect_multiline_reviewer_note() -> str:
    print()
    print("Paste synthetic reviewer note. Leave a blank line when done.")

    lines: list[str] = []

    while True:
        line = input("> ").rstrip()

        if not line:
            break

        lines.append(line)

    note = "\n".join(lines).strip()

    if not note:
        raise ValueError("reviewer_note must not be empty")

    return note

def choose_enum(prompt: str, enum_type: type[EnumType]) -> EnumType:
    values = list(enum_type)

    while True:
        print()
        print(f"{prompt}:")
        for index, value in enumerate(values, start=1):
            print(f"{index}. {value.value}")

        raw_choice = input("Select number: ").strip()

        if not raw_choice.isdigit():
            print("Please enter a number.")
            continue

        choice = int(raw_choice)

        if 1 <= choice <= len(values):
            return values[choice - 1]

        print("Choice out of range.")

def choose_multiple_enum(prompt: str, enum_type):
    values = list(enum_type)

    while True:
        print()
        print(f"{prompt}:")
        print("0. none")

        for index, value in enumerate(values, start=1):
            print(f"{index}. {value.value}")

        raw_choices = input("Select comma-separated numbers: ").strip()

        if raw_choices in {"", "0"}:
            return []

        selected_values = []
        valid = True

        for raw_choice in raw_choices.split(","):
            raw_choice = raw_choice.strip()

            if not raw_choice.isdigit():
                valid = False
                break

            choice = int(raw_choice)

            if not 1 <= choice <= len(values):
                valid = False
                break

            selected_values.append(values[choice - 1])

        if valid:
            return selected_values

        print("Please enter valid comma-separated numbers, or 0 for none.")

def collect_list(prompt: str) -> list[str]:
    print()
    print(f"Enter {prompt.lower()}s one at a time. Leave blank when done.")

    values: list[str] = []

    while True:
        value = input(f"{prompt}: ").strip()

        if not value:
            return values

        values.append(value)


if __name__ == "__main__":
    main()
