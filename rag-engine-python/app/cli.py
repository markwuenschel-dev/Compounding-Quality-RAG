from __future__ import annotations

from enum import Enum
import shutil
import textwrap
from typing import TypeVar

from app.checklist import build_intake_checklist
from app.final_assessment import build_final_assessment
from app.llm_client import LLMClientError, openai_json_client_from_env
from app.extract_intake_understanding import (
    IntakeUnderstandingExtractionError,
    extract_intake_understanding,
)
from app.refusal import evaluate_refusal, build_refusal_message
from app.reporting import format_final_assessment, format_intake_checklist
from app.review_summary_extraction import (
    ReviewSummaryExtractionError,
    extract_review_summary,
)
from app.schemas import (
    ApiReferenceReviewResult,
    EscalationTrigger,
    InventoryInspectionResult,
    LotBatchPatternSummary,
    RecordReviewResult,
    ReviewSummary,
)

EnumType = TypeVar("EnumType", bound=Enum)


DEMO_TITLE = "Compounding Quality Review Assistant"
DEMO_SUBTITLE = "Synthetic two-phase RAG workflow demo"


def terminal_width(default: int = 96) -> int:
    return shutil.get_terminal_size((default, 20)).columns


def print_header() -> None:
    width = terminal_width()
    print()
    print("=" * width)
    print(DEMO_TITLE.center(width))
    print(DEMO_SUBTITLE.center(width))
    print("=" * width)
    print_wrapped(
        "Demo boundary: use synthetic concerns only. This tool does not access real "
        "customer data, patient data, order records, compounding records, inventory "
        "systems, customer history, proprietary SOPs, or external drug references."
    )


def print_step(number: int, title: str) -> None:
    width = terminal_width()
    label = f" STEP {number}: {title.upper()} "
    print()
    print(label.center(width, "-"))


def print_status(message: str) -> None:
    print(f"\n[working] {message}")


def print_wrapped(text: str, indent: int = 0) -> None:
    width = terminal_width()
    prefix = " " * indent
    print(
        textwrap.fill(
            text,
            width=max(50, width - indent),
            initial_indent=prefix,
            subsequent_indent=prefix,
        )
    )


def print_block(text: str, indent: int = 2) -> None:
    prefix = " " * indent
    for line in text.splitlines():
        print(f"{prefix}{line}" if line.strip() else "")


def prompt(text: str) -> str:
    print()
    return input(f"> {text} ").strip()


def main() -> None:
    print_header()

    print_step(1, "Capture intake concern")
    concern_text = prompt("Paste synthetic concern text:")

    refusal = evaluate_refusal(concern_text)
    if refusal.refused:
        print_step(2, "Review stopped")
        print_wrapped(
            refusal.message or "[BUG: refusal was true but no message was provided]",
            indent=2,
        )
        return
    
    intake_understanding = None

    try:
        print("Understanding intake facts")
        intake_understanding = extract_intake_understanding(
            concern_text,
            openai_json_client_from_env(),
        )
    except IntakeUnderstandingExtractionError as exc:
        print("Intake understanding unavailable")
        print_wrapped(
            "Continuing with deterministic checklist generation only. "
            f"Reason: {exc}",
            indent=2,
        )

    if (
        intake_understanding is not None
        and intake_understanding.possible_boundary_issue is not None
    ):
        print("Review stopped")
        print_wrapped(
            build_refusal_message(intake_understanding.possible_boundary_issue),
            indent=2,
        )

        if intake_understanding.boundary_supporting_phrase:
            print()
            print_wrapped(
                f"Boundary phrase: {intake_understanding.boundary_supporting_phrase}",
                indent=2,
            )

        return

    print_status("Building the intake checklist from retrieved synthetic evidence...")
    checklist = build_intake_checklist(concern_text)

    print_step(2, "Phase 1 intake checklist")
    print_block(format_intake_checklist(checklist))

    proceed = prompt("Continue to Phase 2 final review summary? [y/N]:").lower()
    if proceed != "y":
        print_step(3, "Demo stopped")
        print_wrapped("Stopping after the Phase 1 checklist.", indent=2)
        return

    print_step(3, "Enter investigation findings")
    mode = choose_phase_two_input_mode()

    if mode == "manual":
        review_summary = collect_review_summary()
    else:
        review_summary = collect_review_summary_with_llm()

    print_status("Building the final review-support assessment...")
    final_output = build_final_assessment(
        checklist=checklist,
        review_summary=review_summary,
    )

    print_step(4, "Phase 2 final review-support summary")
    print_block(format_final_assessment(final_output, checklist.evidence))


def collect_review_summary() -> ReviewSummary:
    print_wrapped(
        "Use these controlled fields to represent what a human reviewer found. "
        "The tool is not claiming it checked real systems."
    )

    record_review_result = choose_enum("Record review result", RecordReviewResult)
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

    customer_context_summary = prompt(
        "Customer context summary, if available:"
    ) or None
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
        print("Choose Phase 2 input mode:")
        print("  1. Controlled menu fields — best for a predictable manager demo")
        print("  2. Free-text reviewer note — uses OpenAI extraction")

        choice = input("> Select 1 or 2: ").strip()

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
    print("Paste a synthetic reviewer note. Leave a blank line when done.")

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


def choose_enum(prompt_text: str, enum_type: type[EnumType]) -> EnumType:
    values = list(enum_type)

    while True:
        print()
        print(f"{prompt_text}:")
        for index, value in enumerate(values, start=1):
            print(f"  {index}. {humanize_enum(value)}")

        raw_choice = input("> Select number: ").strip()

        if not raw_choice.isdigit():
            print("Please enter a number.")
            continue

        choice = int(raw_choice)

        if 1 <= choice <= len(values):
            selected = values[choice - 1]
            print(f"  Selected: {humanize_enum(selected)}")
            return selected

        print("Choice out of range.")


def choose_multiple_enum(prompt_text: str, enum_type: type[EnumType]) -> list[EnumType]:
    values = list(enum_type)

    while True:
        print()
        print(f"{prompt_text}:")
        print("  0. None")

        for index, value in enumerate(values, start=1):
            print(f"  {index}. {humanize_enum(value)}")

        raw_choices = input("> Select comma-separated numbers: ").strip()

        if raw_choices in {"", "0"}:
            print("  Selected: None")
            return []

        selected_values: list[EnumType] = []
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
            selected_text = ", ".join(humanize_enum(value) for value in selected_values)
            print(f"  Selected: {selected_text}")
            return selected_values

        print("Please enter valid comma-separated numbers, or 0 for none.")


def collect_list(prompt_text: str) -> list[str]:
    print()
    print(f"Enter {prompt_text.lower()}s one at a time. Leave blank when done.")

    values: list[str] = []

    while True:
        value = input(f"> {prompt_text}: ").strip()

        if not value:
            return values

        values.append(value)


def humanize_enum(value: Enum) -> str:
    return str(value.value).replace("_", " ").capitalize()


if __name__ == "__main__":
    main()
