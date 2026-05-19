from __future__ import annotations

from pydantic import Field

from app.schemas import ConcernType, EscalationTrigger, RiskLane, StrictBaseModel


class EvidenceCitation(StrictBaseModel):
    chunk_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    source_title: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    section_heading: str = Field(min_length=1)
    score: float | None = None
    matched_terms: list[str] = Field(default_factory=list)
    supporting_text: str = Field(min_length=1)


class ChecklistItem(StrictBaseModel):
    check_name: str = Field(min_length=1)
    required: bool
    rationale: str = Field(min_length=1)
    evidence: list[EvidenceCitation] = Field(default_factory=list)


class IntakeChecklist(StrictBaseModel):
    concern_text: str = Field(min_length=1)
    likely_concern_type: ConcernType | None = None
    likely_risk_lane: RiskLane | None = None
    review_checks: list[ChecklistItem] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    escalation_triggers_to_rule_out: list[EscalationTrigger] = Field(default_factory=list)
    evidence: list[EvidenceCitation] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
