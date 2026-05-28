---
document_id: SOP-003
title: Record Review, Lot/Batch Context, and Inventory Inspection
version: "1.0"
effective_date: "2025-01-01"
process_area: record_review
source_type: sop
synthetic: true
---

# Record Review, Lot/Batch Context, and Inventory Inspection

## Purpose

This synthetic SOP defines the standard quality-review spine for compounding quality inquiries.

This document is synthetic. It does not provide access to real compounding records, batch records, inventory, or operational systems.

## Standard Review Spine

For most QRE-style inquiries, the reviewer should consider record review, lot or batch context review, inventory inspection if possible, trend or pattern scan when sufficient fields are present, review of customer or submitter context, and missing-information assessment.

These checks are part of a full quality review. Do not describe a case as not a full quality review if these checks are performed.

## Record Review

Record review may consider whether available synthetic information suggests no discrepancy found, documentation incomplete, documentation discrepancy found, or not applicable.

The public RAG system may reason over a supplied synthetic review summary. It must not claim direct access to real records.

## Lot or Batch Context

Lot or batch review considers whether similar concerns appear tied to the same batch, lot, medication, dosage form, or concern type.

Allowed synthetic summary values include no similar batch concerns found, similar concern same batch found, similar concern same medication/dosage form found, trend threshold met, unavailable, and not applicable.

## Inventory Inspection

Inventory inspection may be required when physical product or packaging review could clarify the concern.

Inventory inspection may be impossible or unavailable. Use `not_checked`, `not_applicable`, or `no_inventory_available` when the synthetic case does not support a stronger statement.

Do not claim that real inventory was inspected unless the synthetic review summary explicitly says so.

## Trend Scan

Trend scan depends on available synthetic fields and should be presented as limited.

Synthetic trend review may use medication or product placeholder, dosage form, concern type, batch or lot, and date range if supplied.

The assistant must not claim complete operational surveillance.

## Investigation Requirements

Some investigation requirements are nullable because the RAG system may not know the answer before review.

Inventory inspection may be required if inventory is available. Trend scan depends on available record fields. Customer outreach depends on review text and case context. Technical Services response depends on the review summary and routing rules.

Use null or unknown rather than inventing a false certainty.

## Refusal and Limitation Rules

The assistant may say the reviewer should check the record, the supplied synthetic review summary says no discrepancy was found, or inventory inspection is not known from the current evidence.

The assistant must not say it checked the compounding record, inspected inventory, or confirmed no other customers reported an issue unless the synthetic evidence supports that exact claim.
