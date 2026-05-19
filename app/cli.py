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
)

EnumType = TypeVar("EnumType", bound=Enum)


def main() -> None:
    print("Compounding Quality RAG CLI Demo")
    print("Synthetic proof of concept only. Do not enter real customer, patient, or proprietary data.")
    print()

    concern_text = input("Enter synthetic concern text: ").strip()
    checklist = build_intake_checklist(concern_text)

    print()
    print(format_intake_checklist(checklist))
    print()

    proceed = input("Enter reviewer findings now? [y/N]: ").strip().lower()

    if proceed != "y":
        print("Stopping after Phase 1 checklist.")
        return

    review_summary = collect_review_summary()
    final_output = build_final_assessment(checklist=checklist, review_summary=review_summary)

    print()
    print(format_final_assessment(final_output, checklist.evidence))


def collect_review_summary() -> ReviewSummary:
    record_review_result = choose_enum("Record review result", RecordReviewResult)
    lot_batch_pattern_summary = choose_enum("Lot/batch pattern summary", LotBatchPatternSummary)
    inventory_inspection_result = choose_enum("Inventory inspection result", InventoryInspectionResult)
    api_reference_review_result = choose_enum("API/reference review result", ApiReferenceReviewResult)

    customer_context_summary = input("Customer context summary, if available: ").strip() or None
    missing_information = collect_list("Missing information item")
    evidence_limitations = collect_list("Evidence limitation")

    return ReviewSummary(
        record_review_result=record_review_result,
        lot_batch_pattern_summary=lot_batch_pattern_summary,
        inventory_inspection_result=inventory_inspection_result,
        customer_context_summary=customer_context_summary,
        api_reference_review_result=api_reference_review_result,
        missing_information=missing_information,
        evidence_limitations=evidence_limitations,
    )


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
