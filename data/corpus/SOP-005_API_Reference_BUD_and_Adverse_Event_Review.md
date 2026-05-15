---
document_id: SOP-005
title: API Reference, BUD, and Adverse Event Review
version: "1.0"
effective_date: "2025-01-01"
process_area: api_reference_bud_ade
source_type: sop
synthetic: true
---

# API Reference, BUD, and Adverse Event Review

## Purpose

This synthetic SOP defines the boundary for adverse event, API reference, interaction, and beyond-use-date questions.

This document does not contain real external drug-reference content and does not provide clinical decision support.

## Synthetic API Reference Boundary

The public corpus may include synthetic API reference documents. Those documents can support limited synthetic plausibility examples only.

If no synthetic API reference exists for a claim, the assistant must not invent exact adverse effects, contraindications, interactions, toxicity risks, or species-specific conclusions.

## Suspected ADE Review

Use suspected adverse-event review when the inquiry reports possible clinical symptoms after administration.

Examples include vomiting after administration, lethargy, diarrhea, hospitalization, death, and veterinarian allegation of harm.

Flavor-related vomiting should be routed as suspected ADE rather than routine flavor refusal.

## BUD Questions

A BUD question asks whether a product is within its beyond-use date or what date fields are needed to assess BUD status.

A BUD question is different from a days-supply question.

Needed synthetic fields may include preparation date, assigned beyond-use date, review date or dispense date, dosage form, storage conditions if relevant, and whether BUD is present in the synthetic record summary.

The assistant must not invent a real product-specific BUD.

## Risk Lane Guidance

Routine BUD clarification without harm or defect is usually expected self-limiting.

Suspected ADE without severe criteria is generally unexpected non-life-threatening.

Use life-threatening or legal routing when the case includes hospitalization, death, veterinarian allegation of harm, legal threat, contamination, wrong medication, or wrong patient.

## Reference Review Result

Use `not_needed` when API/reference review is not relevant.

Use `external_reference_needed` when the case would require external drug-reference review in a real workflow but no synthetic reference exists.

Use `not_supported_by_public_corpus` when the question asks for a claim that the public corpus cannot support.

## Refusal and Limitation Rules

Allowed responses include that the public corpus does not include a supported synthetic API reference for exact adverse-effect claims, that the case should be treated as a suspected adverse event based on reported vomiting, or that BUD status cannot be determined without assigned BUD and review date.

Do not claim exact Plumb's content, real compound BUD status, or medication causality.
