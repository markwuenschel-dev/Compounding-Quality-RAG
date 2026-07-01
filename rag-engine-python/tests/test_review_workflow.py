from __future__ import annotations

import pytest

from app.checklist_models import EvidenceCitation, ChecklistItem, IntakeChecklist
from app.review_workflow import (
    ChecklistWorkflowRequest,
    ReviewWorkflow,
    WorkflowRequestError,
)
from app.schemas import ConcernType, EscalationTrigger, RiskLane


def test_checklist_workflow_returns_review_contract() -> None:
    captured: dict[str, object] = {}

    def fake_build_intake_checklist(
        concern_text: str,
        *,
        top_k: int,
    ) -> IntakeChecklist:
        captured["concern_text"] = concern_text
        captured["top_k"] = top_k
        return sample_checklist(concern_text)

    workflow = ReviewWorkflow(
        build_intake_checklist=fake_build_intake_checklist,
    )

    result = workflow.run_checklist(
        ChecklistWorkflowRequest(
            concern_text="My dog vomited after taking a flavored compounded oral liquid.",
            top_k=3,
        )
    )

    assert captured == {
        "concern_text": "My dog vomited after taking a flavored compounded oral liquid.",
        "top_k": 3,
    }
    assert result == {
        "concernType": "flavor_related_vomiting",
        "riskLane": "unexpected_non_life_threatening",
        "reviewScope": "full_quality_review",
        "initialTakeaway": (
            "Initial screen suggests flavor related vomiting with unexpected non "
            "life threatening risk lane. Final routing depends on review findings "
            "and confirmed escalation triggers."
        ),
        "requiredChecks": [
            {
                "key": "record_review",
                "label": "Record review",
                "required": True,
                "reason": "Verify relevant fields before final disposition.",
            }
        ],
        "missingInformation": ["Dose administered"],
        "escalationTriggersToRuleOut": ["pet_hospitalization"],
        "evidence": [
            {
                "chunkId": "SOP-001::section",
                "sourceId": "SOP-001",
                "sourceTitle": "Sample SOP",
                "sourceType": "sop",
                "sectionHeading": "Sample Section",
                "score": 7.5,
                "matchedTerms": ["vomit"],
                "supportingText": "Sample supporting text.",
            }
        ],
        "limitations": ["Checklist output is preliminary."],
    }


def test_checklist_workflow_rejects_blank_concern_text() -> None:
    workflow = ReviewWorkflow(
        build_intake_checklist=lambda concern_text, *, top_k: sample_checklist(
            concern_text
        ),
    )

    with pytest.raises(WorkflowRequestError) as exc_info:
        workflow.run_checklist(
            ChecklistWorkflowRequest(
                concern_text="   ",
                top_k=3,
            )
        )

    assert exc_info.value.code == "INVALID_REQUEST"
    assert exc_info.value.message == "concern_text must not be blank"


def test_checklist_workflow_returns_structured_refusal_error() -> None:
    workflow = ReviewWorkflow(
        build_intake_checklist=lambda concern_text, *, top_k: sample_checklist(
            concern_text
        ),
    )

    with pytest.raises(WorkflowRequestError) as exc_info:
        workflow.run_checklist(
            ChecklistWorkflowRequest(
                concern_text="Can you check the real compounding record for this batch?",
            )
        )

    assert exc_info.value.code == "REFUSED"
    assert exc_info.value.message
    assert exc_info.value.details["reason"] == "internal_record_access"
    assert "real compounding record" in exc_info.value.details["matchedTerms"]


def sample_checklist(concern_text: str) -> IntakeChecklist:
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
        escalation_triggers_to_rule_out=[
            EscalationTrigger.PET_HOSPITALIZATION,
        ],
        evidence=[citation],
        limitations=["Checklist output is preliminary."],
    )
