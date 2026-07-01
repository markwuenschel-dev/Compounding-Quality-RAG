from __future__ import annotations

import pytest
from fastapi import HTTPException

import app.server as server
from app.checklist_models import EvidenceCitation, ChecklistItem, IntakeChecklist
from app.schemas import (
    ApiReferenceReviewResult,
    ConcernType,
    EscalationTrigger,
    InventoryInspectionResult,
    LotBatchPatternSummary,
    RecordReviewResult,
    ReviewSummary,
    RiskLane,
)


def test_checklist_endpoint_refuses_internal_record_access(monkeypatch) -> None:
    """The refusal boundary must fire on /checklist before any checklist is built."""
    build_called = False

    def fake_build_intake_checklist(
        concern_text: str,
        *,
        chunks_path,
        top_k: int,
    ) -> IntakeChecklist:
        nonlocal build_called
        build_called = True
        return _sample_checklist(concern_text)

    monkeypatch.setattr(server, "build_intake_checklist", fake_build_intake_checklist)

    request = server.ChecklistRequest(
        concern_text="Can you check the real compounding record for this batch?",
        top_k=5,
    )

    with pytest.raises(HTTPException) as exc_info:
        server.checklist(request)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail
    assert build_called is False


def test_checklist_endpoint_returns_checklist_for_safe_concern(monkeypatch) -> None:
    def fake_build_intake_checklist(
        concern_text: str,
        *,
        chunks_path,
        top_k: int,
    ) -> IntakeChecklist:
        return _sample_checklist(concern_text)

    monkeypatch.setattr(server, "build_intake_checklist", fake_build_intake_checklist)

    request = server.ChecklistRequest(
        concern_text="My dog vomited after a flavored compounded oral liquid.",
        top_k=5,
    )

    result = server.checklist(request)

    assert isinstance(result, IntakeChecklist)
    assert result.concern_text == "My dog vomited after a flavored compounded oral liquid."


def test_retrieve_endpoint_refuses_external_reference_query(monkeypatch) -> None:
    retrieve_called = False

    def fake_retrieve(*, query, chunks_path, top_k, source_type):
        nonlocal retrieve_called
        retrieve_called = True
        return []

    monkeypatch.setattr(server, "retrieve", fake_retrieve)

    request = server.RetrieveRequest(
        query="What is the toxicity dose range for this drug?",
        top_k=5,
    )

    with pytest.raises(HTTPException) as exc_info:
        server.retrieve_evidence(request)

    assert exc_info.value.status_code == 403
    assert retrieve_called is False


def test_retrieve_endpoint_returns_results_for_safe_query(monkeypatch) -> None:
    def fake_retrieve(*, query, chunks_path, top_k, source_type):
        return []

    monkeypatch.setattr(server, "retrieve", fake_retrieve)

    request = server.RetrieveRequest(query="flavored oral liquid vomiting", top_k=5)

    result = server.retrieve_evidence(request)

    assert result.query == "flavored oral liquid vomiting"
    assert result.results == []


def test_final_assessment_endpoint_refuses_internal_record_access(monkeypatch) -> None:
    build_called = False

    def fake_build_intake_checklist(concern_text, *, chunks_path, top_k):
        nonlocal build_called
        build_called = True
        return _sample_checklist(concern_text)

    monkeypatch.setattr(server, "build_intake_checklist", fake_build_intake_checklist)

    request = server.FinalAssessmentRequest(
        concern_text="Can you check the real compounding record for this batch?",
        top_k=5,
        review_summary=_sample_review_summary(),
    )

    with pytest.raises(HTTPException) as exc_info:
        server.final_assessment(request)

    assert exc_info.value.status_code == 403
    assert build_called is False


def test_final_assessment_endpoint_builds_for_safe_concern(monkeypatch) -> None:
    def fake_build_intake_checklist(concern_text, *, chunks_path, top_k):
        return _sample_checklist(concern_text)

    monkeypatch.setattr(server, "build_intake_checklist", fake_build_intake_checklist)

    request = server.FinalAssessmentRequest(
        concern_text="My dog vomited after a flavored compounded oral liquid.",
        top_k=5,
        review_summary=_sample_review_summary(),
    )

    result = server.final_assessment(request)

    assert (
        result.raw_intake.concern_narrative
        == "My dog vomited after a flavored compounded oral liquid."
    )


def _sample_review_summary() -> ReviewSummary:
    return ReviewSummary(
        record_review_result=RecordReviewResult.NO_DISCREPANCY_FOUND,
        lot_batch_pattern_summary=LotBatchPatternSummary.NO_SIMILAR_BATCH_CONCERNS_FOUND,
        inventory_inspection_result=InventoryInspectionResult.NOT_CHECKED,
        customer_context_summary="Vomited once, recovered, no hospitalization reported.",
        api_reference_review_result=ApiReferenceReviewResult.NOT_NEEDED,
        severe_triggers_observed=[],
        missing_information=[],
        evidence_limitations=[],
    )


def _sample_checklist(concern_text: str) -> IntakeChecklist:
    citation = EvidenceCitation(
        chunk_id="SOP-001::section",
        source_id="SOP-001",
        source_title="Sample SOP",
        source_type="sop",
        section_heading="Sample Section",
        score=7.5,
        matched_terms=["vomit"],
        supporting_text="Sample supporting text.",
    )

    return IntakeChecklist(
        concern_text=concern_text,
        likely_concern_type=ConcernType.FLAVOR_RELATED_VOMITING,
        likely_risk_lane=RiskLane.UNEXPECTED_NON_LIFE_THREATENING,
        review_checks=[
            ChecklistItem(
                check_name="Record review",
                required=True,
                rationale="Verify relevant fields before final disposition.",
                evidence=[citation],
            )
        ],
        missing_information=["Dose administered"],
        escalation_triggers_to_rule_out=[EscalationTrigger.PET_HOSPITALIZATION],
        evidence=[citation],
        limitations=["Checklist output is preliminary."],
    )
