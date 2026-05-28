---
document_id: SOP-001
title: Intake Classification and Risk Lane Assignment
version: "1.0"
effective_date: "2025-01-01"
process_area: intake_classification
source_type: sop
synthetic: true
---

# Intake Classification and Risk Lane Assignment

## Purpose

This synthetic SOP defines how compounding quality inquiries should be classified and routed in the public Compounding Quality RAG project.

This document is synthetic. It is not real company policy and does not contain proprietary workflow instructions.

## Intake Source Rules

An inquiry may come from a QRE/general-question form or from a customer review.

A QRE/general-question form usually contains more operational structure than a customer review. When product fields are populated, dosage form should usually be available. Use `unknown` only when the synthetic record intentionally omits the product context or describes an incomplete/newer product record.

A customer review must include star rating and whether review text is present. A customer review can have a star rating with blank review text.

## Formal Classification

Use `qre` when the inquiry fits a formal quality-related bucket such as customer service related, equipment or device related, medication related, suspected adverse drug event, or dispensing error.

Use `general_question` when the inquiry asks for clarification or guidance without a reported product quality failure, harm, wrong item, defect, or escalation trigger.

## Concern Type

Concern type describes what actually happened or what was asked.

Examples include `pet_refused_flavor`, `flavor_related_vomiting`, `bud_question`, `syringe_or_device_issue`, and `wrong_patient_or_wrong_medication`.

## Risk Lane Criteria

Use `expected_self_limiting` when the issue is routine, low severity, and does not include harm or global escalation triggers.

Use `unexpected_non_life_threatening` when the issue includes a possible adverse event or unexpected product concern without severe escalation criteria.

Use `life_threatening_or_legal` when the inquiry includes death, hospitalization, threatened legal action, veterinarian allegation of harm from the compound, possible contamination, wrong patient, wrong medication, or rare regulatory/compliance concern.

## Review Scope

`full_quality_review` means the case generally follows the quality review spine: record review, lot/batch review, inventory inspection if available, trend scan when possible, and review of available customer context.

`guidance_only` means the case is a simple guidance or clarification request where the public corpus can explain what information is needed but should not claim a full operational review occurred.

`customer_review_record_check` means the inquiry is anchored in a customer review and should consider review text, rating, available synthetic record context, and whether outreach may be needed.

`escalation_review` means a global escalation trigger or severe risk lane controls the handling path.

`insufficient_information` means required facts are missing and the assistant should ask for or list missing information.

## Public-System Boundary

The public RAG system does not access real compounding records, real inventory, real customer history, Snowflake, Smartsheet, or external drug references.

The assistant may say a reviewer should perform a check, or that a supplied synthetic review summary indicates a result. It must not claim direct access to real systems.

## Missing Information Logic

List missing information when it affects classification, risk lane, handling path, or resolution review.

Common missing fields include dosage form, medication or product placeholder, species, batch or lot information, BUD information, symptom details, administration status, veterinarian contact, and review text presence.
