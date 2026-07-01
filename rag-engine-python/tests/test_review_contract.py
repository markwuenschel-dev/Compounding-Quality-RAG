from __future__ import annotations

from app.checklist_models import EvidenceCitation, ChecklistItem, IntakeChecklist
from app.review_contract import checklist_to_review_contract
from app.schemas import ConcernType, EscalationTrigger, RiskLane


def test_checklist_to_review_contract_maps_domain_to_camel_case() -> None:
    contract = checklist_to_review_contract(
        sample_checklist("My dog vomited after taking a flavored compounded oral liquid.")
    )

    assert contract == {
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


def test_review_scope_reflects_risk_and_concern() -> None:
    escalation = sample_checklist(
        "x", risk_lane=RiskLane.LIFE_THREATENING_OR_LEGAL
    )
    assert checklist_to_review_contract(escalation)["reviewScope"] == "escalation_review"

    guidance = sample_checklist("x", concern_type=ConcernType.BUD_QUESTION)
    assert checklist_to_review_contract(guidance)["reviewScope"] == "guidance_only"


def sample_checklist(
    concern_text: str,
    *,
    concern_type: ConcernType = ConcernType.FLAVOR_RELATED_VOMITING,
    risk_lane: RiskLane = RiskLane.UNEXPECTED_NON_LIFE_THREATENING,
) -> IntakeChecklist:
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
        likely_concern_type=concern_type,
        likely_risk_lane=risk_lane,
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
