# Reported Severe Trigger and Clinical Context Policy

Status: confirmed  
Updated: 2026-06-25

This policy defines how reported severe triggers and serious clinical context affect `review_summary.severe_triggers_observed` and final routing.

## Core rule

Final severe escalation routing should use structured severe triggers, not free-text keyword scanning.

Free text can contain negation:

```text
No hospitalization, death, legal threat, contamination, wrong medication concern, or veterinarian allegation was reported.
```

That sentence must not create severe escalation.

## Immediate proposed severe triggers

A listed escalation trigger reported in the complaint may be proposed immediately for reviewer confirmation.

Example:

```text
Complaint: The pet was hospitalized after the first dose.
Investigation: Record review found no discrepancy.
```

Proposed structured finding:

```yaml
severe_triggers_observed:
  - pet_hospitalization
```

The reviewer confirms, removes, or corrects the proposed trigger before final assessment.

## Controlled severe trigger values

- `pet_death`
- `pet_hospitalization`
- `threatened_legal_action`
- `veterinarian_alleges_harm_from_compound`
- `possible_contamination`
- `wrong_patient_or_wrong_medication`
- `repeat_issue_same_lot_or_batch_with_conditions`
- `rare_regulatory_or_compliance_concern`

## Context-only symptoms

Shortness of breath, collapse, falling over, neurologic signs, agitation, and similar clinical descriptions remain clinical context when no existing structured escalation trigger is present.

These facts may support customer outreach, reviewer attention, missing-information questions, conservative ADE review, or non-life-threatening unexpected risk lane. They do not independently force `life_threatening_or_legal`.

## Negation rule

Negated trigger language must not populate `severe_triggers_observed`.

Examples:

```text
No hospitalization was reported.
No death, legal threat, or contamination concern was identified.
The reviewer has not confirmed wrong medication or wrong patient.
```

## Later affirmative override

A later clear affirmative statement can still create the trigger.

```text
No hospitalization or death was reported. Reviewer confirmed possible wrong medication after checking the label image.
```

Expected:

```yaml
severe_triggers_observed:
  - wrong_patient_or_wrong_medication
```

## Combined-product dose-uniformity concerns

When a complaint questions dose uniformity in a combined preparation and links that concern to worsening bloodwork, lack of therapeutic response, or possible harm, the compounding/worksheet record must be reviewed.

Until documented:

```yaml
record_review_result: documentation_incomplete
lot_batch_pattern_summary: unavailable
inventory_inspection_result: not_checked
```

## UI wording expectation

If the UI surfaces complaint-reported severe facts before final assessment, use:

```text
Reported severe trigger requiring reviewer confirmation
```

Avoid implying that the system independently verified the trigger.

## Testing expectations

Keep tests for complaint-reported triggers, negated triggers, coordinated negation lists, later affirmative triggers, context-only symptoms, and confirmed structured-trigger routing.
