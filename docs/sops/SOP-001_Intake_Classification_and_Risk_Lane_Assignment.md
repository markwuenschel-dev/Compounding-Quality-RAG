# SOP-001 Intake Classification and Risk Lane Assignment

Document ID: SOP-001  
Title: Intake Classification and Risk Lane Assignment  
Version: 1.1  
Effective Date: 2026-05-04  
Process Area: intake classification  
Source Type: sop  
Synthetic: true
## Purpose

Define how synthetic QRE/general-question submissions and customer reviews are initially classified, risk-laned, and routed for review.

## Scope

This SOP applies to synthetic records created from two intake sources: the QRE/general-question form and customer reviews. Frontline pharmacist questions are not a separate intake source; they are modeled as QRE/general-question form submissions with `submitter_role: frontline_pharmacist` and `submission_purpose: frontline_pharmacist_question`.

## Raw Intake Fields

Raw intake may include the concern narrative, intake source, submitter role, submission purpose, star rating for customer reviews, whether review text is present, and a submitter-selected classification when available.

Submitters may select `qre` or `general_question`. Submitters do not assign formal category or subcategory in this synthetic workflow. Category and subcategory are reviewer-assigned fields.

## Review Procedure

1. Read the raw concern narrative.
2. Identify the intake source as `qre_general_question_form` or `customer_review`.
3. Identify the submitter role and submission purpose.
4. Determine whether the record is a customer-reported concern, customer-review follow-up, escalation request, documentation update, or frontline pharmacist question.
5. Assign a preliminary risk lane based on the narrative: expected/self-limiting, unexpected/non-life-threatening, or life-threatening/legal.
6. Determine whether the record requires full quality review, customer-review record check, escalation review, guidance-only review, or cannot be assessed because information is insufficient.
7. Do not infer a final handling path until required review findings are available or the record clearly falls into guidance-only scope.

## Frontline Pharmacist Questions

A frontline pharmacist question usually remains a general question and usually maps to `review_scope: guidance_only`. It does not normally require compounding-record review, lot/batch review, inventory inspection, trend scan, or customer outreach.

A frontline pharmacist question should move out of guidance-only scope if the narrative includes a product-quality concern, suspected ADE, dispensing error, escalation trigger, or unresolved customer safety issue.

## Escalation Overrides

Potential pet death, pet hospitalization, threatened legal action, veterinarian allegation of harm, possible contamination, or wrong patient/wrong medication concerns override routine classification and should be evaluated under the escalation SOP.

## Notes and Limitations

This SOP does not decide whether a real event is reportable or legally significant. It defines synthetic workflow routing for a public learning artifact.
