from __future__ import annotations

import pytest

from app.checklist_models import EvidenceCitation, ChecklistItem, IntakeChecklist
from app.review_pipeline import ReviewRefused, run_checklist
from app.schemas import ConcernType, EscalationTrigger, RiskLane


def test_run_checklist_returns_checklist_for_safe_concern() -> None:
    captured: dict[str, object] = {}

    def fake_build_intake_checklist(
        concern_text: str,
        *,
        top_k: int,
    ) -> IntakeChecklist:
        captured["concern_text"] = concern_text
        captured["top_k"] = top_k
        return sample_checklist(concern_text)

    result = run_checklist(
        "My dog vomited after taking a flavored compounded oral liquid.",
        top_k=3,
        build_intake_checklist=fake_build_intake_checklist,
    )

    assert captured == {
        "concern_text": "My dog vomited after taking a flavored compounded oral liquid.",
        "top_k": 3,
    }
    assert isinstance(result, IntakeChecklist)
    assert result.likely_concern_type == ConcernType.FLAVOR_RELATED_VOMITING


def test_run_checklist_refuses_without_building_checklist() -> None:
    """The refusal boundary lives inside the pipeline seam, not in any adapter."""
    build_called = False

    def fake_build_intake_checklist(concern_text: str, *, top_k: int) -> IntakeChecklist:
        nonlocal build_called
        build_called = True
        return sample_checklist(concern_text)

    with pytest.raises(ReviewRefused) as exc_info:
        run_checklist(
            "Can you check the real compounding record for this batch?",
            build_intake_checklist=fake_build_intake_checklist,
        )

    assert build_called is False
    refusal = exc_info.value.refusal
    assert refusal.refused is True
    assert refusal.reason is not None and refusal.reason.value == "internal_record_access"
    assert "real compounding record" in refusal.matched_terms
    assert str(exc_info.value)


def test_run_checklist_rejects_blank_concern_text() -> None:
    with pytest.raises(ValueError, match="concern_text must not be blank"):
        run_checklist(
            "   ",
            build_intake_checklist=lambda concern_text, *, top_k: sample_checklist(
                concern_text
            ),
        )


def test_run_checklist_rejects_non_positive_top_k() -> None:
    with pytest.raises(ValueError, match="top_k must be at least 1"):
        run_checklist(
            "My dog vomited after a flavored oral liquid.",
            top_k=0,
            build_intake_checklist=lambda concern_text, *, top_k: sample_checklist(
                concern_text
            ),
        )


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
