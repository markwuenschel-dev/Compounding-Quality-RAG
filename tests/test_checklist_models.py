import pytest
from pydantic import ValidationError

from app.checklist_models import EvidenceCitation, IntakeChecklist
from app.schemas import ConcernType, RiskLane


def make_evidence(score: float | None = 2.5) -> EvidenceCitation:
    return EvidenceCitation(
        chunk_id="SOP-TEST::purpose",
        source_id="SOP-TEST",
        source_title="Test SOP",
        source_type="sop",
        section_heading="Purpose",
        score=score,
        matched_terms=["test", "evidence"],
        supporting_text="Synthetic supporting text.",
    )


def test_evidence_citation_accepts_float_score() -> None:
    citation = make_evidence(score=2.75)

    assert citation.score == 2.75


def test_evidence_citation_rejects_missing_supporting_text() -> None:
    with pytest.raises(ValidationError):
        EvidenceCitation(
            chunk_id="SOP-TEST::purpose",
            source_id="SOP-TEST",
            source_title="Test SOP",
            source_type="sop",
            section_heading="Purpose",
            score=1.0,
            matched_terms=["test"],
            supporting_text="",
        )


def test_intake_checklist_uses_default_factory_for_review_checks() -> None:
    field_info = IntakeChecklist.model_fields["review_checks"]

    assert field_info.default_factory is list


def test_intake_checklist_defaults_are_independent() -> None:
    first = IntakeChecklist(concern_text="First concern.")
    second = IntakeChecklist(concern_text="Second concern.")

    first.missing_information.append("Only first checklist should have this.")

    assert first.missing_information == ["Only first checklist should have this."]
    assert second.missing_information == []


def test_intake_checklist_forbids_extra_fields() -> None:
    with pytest.raises(ValidationError):
        IntakeChecklist.model_validate(
            {
                "concern_text": "Synthetic concern.",
                "likely_concern_type": ConcernType.PET_REFUSED_FLAVOR,
                "likely_risk_lane": RiskLane.EXPECTED_SELF_LIMITING,
                "unsupported_extra_field": True,
            }
        )