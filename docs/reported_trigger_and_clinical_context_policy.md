# Reported Severe Trigger and Clinical Context Policy

Status: confirmed

## Immediate severe triggers

A listed escalation trigger reported in the complaint is proposed immediately
as a severe trigger and remains selected for reviewer confirmation.

Example:

```text
Complaint: The pet was hospitalized after the first dose.
Investigation: Record review found no discrepancy.
```

The proposed structured finding includes:

```yaml
severe_triggers_observed:
  - pet_hospitalization
```

The reviewer confirms or corrects the proposed trigger before final assessment.

## Context-only symptoms

Shortness of breath, collapse, falling over, and similar clinical descriptions
remain clinical context when no existing structured escalation trigger is
present.

These details may make customer outreach more likely, but do not independently
force leadership escalation.

## Combined-product dose-uniformity concerns

When a complaint questions dose uniformity in a combined preparation and links
that concern to worsening bloodwork or lack of therapeutic response, the
compounding record must be reviewed.

Until documented:

```yaml
record_review_result: documentation_incomplete
lot_batch_pattern_summary: unavailable
inventory_inspection_result: not_checked
```
