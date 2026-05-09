# SOP-007 Leadership Escalation and Clinic Contact Criteria

Document ID: SOP-007  
Title: Leadership Escalation and Clinic Contact Criteria  
Version: 1.1  
Effective Date: 2026-05-04  
Process Area: leadership escalation  
Source Type: sop  
Synthetic: true
## Purpose

Define global escalation triggers and when leadership escalation should occur before routine outreach or resolution.

## Scope

This SOP applies to life-threatening, legal, serious ADE, veterinarian-harm allegation, possible contamination, wrong-patient/wrong-medication, and rare regulatory/compliance concerns.

## Escalation Triggers

- `pet_death`
- `pet_hospitalization`
- `threatened_legal_action`
- `veterinarian_alleges_harm_from_compound`
- `possible_contamination`
- `wrong_patient_or_wrong_medication`
- `repeat_issue_same_lot_or_batch_with_conditions`
- `rare_regulatory_or_compliance_concern`

## Review Procedure

1. Screen the concern narrative for global escalation triggers.
2. If a global escalation trigger is present, assign `risk_lane: life_threatening_or_legal` unless reviewer evidence supports a different lane.
3. Use `handling_path: leadership_escalation_before_resolution` when leadership review should occur before routine outreach or resolution.
4. Consider clinic or veterinarian contact when the synthetic narrative includes veterinarian allegation of harm or clinical details requiring clarification.
5. Do not delay escalation solely because record review is incomplete.

## Notes and Limitations

This SOP does not define legal reporting obligations. It defines synthetic workflow escalation behavior for an evidence-assistant project.
