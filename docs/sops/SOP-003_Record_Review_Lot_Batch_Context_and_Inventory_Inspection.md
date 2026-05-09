# SOP-003 Record Review, Lot/Batch Context, and Inventory Inspection

Document ID: SOP-003  
Title: Record Review, Lot/Batch Context, and Inventory Inspection  
Version: 1.1  
Effective Date: 2026-05-04  
Process Area: record review  
Source Type: sop  
Synthetic: true
## Purpose

Define when synthetic records require compounding-record review, lot/batch context review, or inventory inspection.

## Scope

This SOP applies to customer-reported concerns, customer reviews, suspected documentation issues, possible product-quality concerns, and QRE-like events. It usually does not apply to guidance-only frontline pharmacist questions unless the narrative alleges a product concern.

## Review Procedure

1. Determine whether the review scope requires record review.
2. If record review is required, the reviewer should verify whether the associated synthetic compounding-record summary indicates no discrepancy, incomplete documentation, or documentation discrepancy.
3. If lot/batch context is relevant, review available synthetic lot/batch pattern summaries.
4. If remaining inventory is available in the synthetic scenario, document whether visual inspection found no concern, found a concern, or was not possible.
5. Do not claim that the RAG system directly inspected physical inventory or queried real compounding records.

## Record Review Result Values

- `no_discrepancy_found`
- `documentation_incomplete`
- `documentation_discrepancy_found`
- `not_applicable`

## Lot/Batch Pattern Summary Values

- `no_similar_batch_concerns_found`
- `similar_concern_same_batch_found`
- `similar_concern_same_medication_dosage_form_found`
- `trend_threshold_met`
- `unavailable`
- `not_applicable`

## Inventory Inspection Values

- `no_inventory_available`
- `no_visual_concern_found`
- `visual_concern_found`
- `not_checked`
- `not_applicable`

## Notes and Limitations

Synthetic lot/batch review is limited to fields present in synthetic inquiry records. It should not be presented as complete API-level or enterprise-wide trend surveillance.
