# SOP-008 Trend and Pattern Monitoring Rules

Document ID: SOP-008  
Title: Trend and Pattern Monitoring Rules  
Version: 1.1  
Effective Date: 2026-05-04  
Process Area: trend monitoring  
Source Type: sop  
Synthetic: true
## Purpose

Define how the synthetic workflow models trend and pattern monitoring without overclaiming access to complete operational systems.

## Scope

This SOP applies to repeated concerns involving similar medication placeholders, dosage forms, concern types, batch/lot context, and customer-review patterns.

## Review Procedure

1. Determine whether trend review is required for the record.
2. If trend review is required, use only fields available in synthetic inquiry records or synthetic review summaries.
3. Do not claim complete API-level trend detection unless the synthetic corpus explicitly supports it.
4. Treat trend monitoring as a flag or review finding, not as a final handling path.
5. Escalation triggers override trend-only handling.

## Synthetic Trend Thresholds

- Three similar concerns within 30 days using medication placeholder, dosage form, and concern type.
- Five similar concerns within 90 days using medication placeholder, dosage form, and concern type.
- Two serious concerns tied to the same lot or batch.

## Frontline Pharmacist Question Trend Tracking

Frontline pharmacist questions may be tracked for operational volume and support trends. This does not mean they require full quality review. Use `submitter_role`, `submission_purpose`, and `review_scope` to count these records separately from customer-reported concerns.

## Notes and Limitations

Synthetic trend review is intentionally limited. It is designed to test retrieval, metadata filtering, and failure analysis, not to represent full production analytics.
