from pathlib import Path

import pytest

from app.checklist import (
    build_intake_checklist,
    build_missing_information,
    infer_likely_concern_type,
    infer_likely_risk_lane,
)
from app.schemas import ConcernType, EscalationTrigger, RiskLane


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHUNKS_PATH = PROJECT_ROOT / "data" / "index" / "chunks.jsonl"


def test_build_intake_checklist_identifies_flavor_related_vomiting() -> None:
    checklist = build_intake_checklist(
        "My dog got chicken flavored oral liquid and threw up.",
        chunks_path=CHUNKS_PATH,
        top_k=5,
    )

    assert checklist.likely_concern_type == ConcernType.FLAVOR_RELATED_VOMITING
    assert checklist.likely_risk_lane == RiskLane.UNEXPECTED_NON_LIFE_THREATENING
    assert checklist.review_checks
    assert checklist.missing_information
    assert checklist.evidence


def test_build_intake_checklist_respects_top_k() -> None:
    checklist = build_intake_checklist(
        "Dog vomited after chicken flavored oral liquid.",
        chunks_path=CHUNKS_PATH,
        top_k=2,
    )

    assert len(checklist.evidence) <= 2


def test_build_intake_checklist_retrieves_only_sop_evidence() -> None:
    checklist = build_intake_checklist(
        "Transdermal pen is leaking and has air bubbles.",
        chunks_path=CHUNKS_PATH,
        top_k=5,
    )

    assert checklist.evidence

    for citation in checklist.evidence:
        assert citation.source_type == "sop"


def test_build_intake_checklist_rejects_blank_concern() -> None:
    with pytest.raises(ValueError, match="concern_text must not be empty"):
        build_intake_checklist("   ", chunks_path=CHUNKS_PATH)


def test_infer_likely_concern_type_identifies_bud_question() -> None:
    concern_type = infer_likely_concern_type(
        "Frontline pharmacist asks whether the product is within BUD."
    )

    assert concern_type == ConcernType.BUD_QUESTION


def test_infer_likely_concern_type_identifies_transdermal_device_issue() -> None:
    concern_type = infer_likely_concern_type(
        "The transdermal pen leaks after two clicks and has air bubbles."
    )

    assert concern_type == ConcernType.SYRINGE_OR_DEVICE_ISSUE


def test_infer_likely_risk_lane_escalates_wrong_medication() -> None:
    risk_lane = infer_likely_risk_lane("Possible wrong medication for wrong patient.")

    assert risk_lane == RiskLane.LIFE_THREATENING_OR_LEGAL


def test_vomiting_missing_information_includes_clinical_context() -> None:
    missing_information = build_missing_information(
        "Dog vomited after chicken flavored oral liquid."
    )

    assert "Timing of vomiting relative to administration" in missing_information
    assert "Whether veterinarian was contacted" in missing_information
    assert "Whether the pet was hospitalized" in missing_information


def test_checklist_includes_standard_escalation_triggers_to_rule_out() -> None:
    checklist = build_intake_checklist(
        "Dog vomited after chicken flavored oral liquid.",
        chunks_path=CHUNKS_PATH,
        top_k=3,
    )

    assert EscalationTrigger.PET_DEATH in checklist.escalation_triggers_to_rule_out
    assert EscalationTrigger.PET_HOSPITALIZATION in checklist.escalation_triggers_to_rule_out
    assert EscalationTrigger.THREATENED_LEGAL_ACTION in checklist.escalation_triggers_to_rule_out