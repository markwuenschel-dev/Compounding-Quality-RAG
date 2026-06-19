from collections.abc import Iterator

import pytest

from app import cli
from app.schemas import (
    ApiReferenceReviewResult,
    EscalationTrigger,
    InventoryInspectionResult,
    LotBatchPatternSummary,
    RecordReviewResult,
    ReviewSummary,
)

def disable_intake_understanding(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "openai_json_client_from_env", lambda: object())

    def fake_extract_intake_understanding(concern_text, client):
        return None

    monkeypatch.setattr(cli, "extract_intake_understanding", fake_extract_intake_understanding)

def input_iterator(values: list[str]) -> Iterator[str]:
    yield from values


def test_choose_enum_returns_selected_enum_member(monkeypatch: pytest.MonkeyPatch) -> None:
    inputs = input_iterator(["1"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    result = cli.choose_enum("Record review result", RecordReviewResult)

    assert result == RecordReviewResult.NO_DISCREPANCY_FOUND


def test_choose_enum_reprompts_after_invalid_input(monkeypatch: pytest.MonkeyPatch) -> None:
    inputs = input_iterator(["not-a-number", "99", "2"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    result = cli.choose_enum("Record review result", RecordReviewResult)

    assert result == RecordReviewResult.DOCUMENTATION_INCOMPLETE


def test_collect_list_returns_values_until_blank(monkeypatch: pytest.MonkeyPatch) -> None:
    inputs = input_iterator(["first item", "second item", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    result = cli.collect_list("Missing information item")

    assert result == ["first item", "second item"]


def test_collect_review_summary_builds_review_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    inputs = input_iterator(
        [
            "1",
            "1",
            "4",
            "1",
            "0",  # severe_triggers_observed: none
            "Dog vomited once and recovered.",
            "Timing from dose to vomiting",
            "",
            "No external reference available",
            "",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    review_summary = cli.collect_review_summary()

    assert review_summary.record_review_result == RecordReviewResult.NO_DISCREPANCY_FOUND
    assert (
        review_summary.lot_batch_pattern_summary
        == LotBatchPatternSummary.NO_SIMILAR_BATCH_CONCERNS_FOUND
    )
    assert review_summary.inventory_inspection_result == InventoryInspectionResult.NOT_CHECKED
    assert review_summary.api_reference_review_result == ApiReferenceReviewResult.NOT_NEEDED
    assert review_summary.customer_context_summary == "Dog vomited once and recovered."
    assert review_summary.missing_information == ["Timing from dose to vomiting"]
    assert review_summary.evidence_limitations == ["No external reference available"]


def test_main_can_stop_after_phase_one(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    disable_intake_understanding(monkeypatch)

    inputs = input_iterator(
        [
            "Dog vomited after chicken flavored oral liquid.",
            "n",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    cli.main()

    captured = capsys.readouterr()

    assert "DEMO" in captured.out
    assert "PHASE 1" in captured.out
    assert "INTAKE CHECKLIST" in captured.out
    assert "Stopping after the Phase 1 checklist." in captured.out


def test_main_runs_phase_two_with_controlled_findings(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    disable_intake_understanding(monkeypatch)

    inputs = input_iterator(
        [
            "Dog vomited after chicken flavored oral liquid.",
            "y",
            "1",
            "1",
            "1",
            "4",
            "1",
            "0",
            "Vomited once and recovered. No hospitalization.",
            "",
            "",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    cli.main()

    captured = capsys.readouterr()

    assert "PHASE 2" in captured.out
    assert "FINAL REVIEW" in captured.out


def test_choose_multiple_enum_returns_empty_list_for_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = input_iterator(["0"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    result = cli.choose_multiple_enum(
        "Severe escalation triggers observed",
        EscalationTrigger,
    )

    assert result == []

def test_main_runs_phase_two_with_llm_findings(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    inputs = input_iterator(
        [
            "Dog vomited after chicken flavored oral liquid.",
            "y",
            "2",
            "I reviewed the record and found no discrepancy.",
            "No similar batch complaints were found.",
            "Inventory was not available.",
            "Dog vomited once and recovered.",
            "No hospitalization, death, legal threat, contamination, wrong medication concern, or vet allegation was reported.",
            "",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    def fake_extract_review_summary(reviewer_note, client):
        return ReviewSummary(
            record_review_result=RecordReviewResult.NO_DISCREPANCY_FOUND,
            lot_batch_pattern_summary=LotBatchPatternSummary.NO_SIMILAR_BATCH_CONCERNS_FOUND,
            inventory_inspection_result=InventoryInspectionResult.NO_INVENTORY_AVAILABLE,
            api_reference_review_result=ApiReferenceReviewResult.NOT_NEEDED,
            customer_context_summary="Dog vomited once and recovered.",
            severe_triggers_observed=[],
            missing_information=[],
            evidence_limitations=["Inventory was not available to inspect."],
        )

    monkeypatch.setattr(cli, "openai_json_client_from_env", lambda: object())

    def fake_extract_intake_understanding(concern_text, client):
        return None


    monkeypatch.setattr(cli, "extract_review_summary", fake_extract_review_summary)

    cli.main()

    capsys.readouterr()
