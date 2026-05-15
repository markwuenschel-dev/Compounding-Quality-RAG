---
document_id: SOP-002
title: Frontline Guidance, Delegate-Back, and Response Rules
version: "1.0"
effective_date: "2025-01-01"
process_area: frontline_guidance
source_type: sop
synthetic: true
---

# Frontline Guidance, Delegate-Back, and Response Rules

## Purpose

This synthetic SOP defines when a compounding quality inquiry can be answered with frontline guidance, delegated back to a frontline pharmacist, or routed to Technical Services.

This document is synthetic and is not real company policy.

## General Principle

Delegate-back is appropriate only when the inquiry can be safely handled using available frontline information and does not involve a quality defect, suspected adverse event, dispensing error, contamination concern, or global escalation trigger.

If a quality review is required, do not label the case as simple delegation merely because a frontline pharmacist submitted it.

## Ingredient Presence Questions

A frontline pharmacist may answer a narrow ingredient-presence question when accessible formula or inactive-ingredient information supports the answer.

The response should confirm or deny the specific ingredient being asked about. It should not provide a full blanket ingredient list unless the synthetic corpus explicitly supports that.

## Oral Liquid Shortage

An oral liquid shortage question may be delegated back when it only concerns administration technique, expected fill appearance, or routine counseling.

Do not delegate back if the concern includes leakage, package damage, missing item, compounding-record discrepancy, temperature excursion, contamination concern, repeated similar issue, or suspected adverse event.

## Temperature Excursion

Use limited guidance when the synthetic corpus provides temperature-excursion guidance.

If the question asks for product-specific stability outside the limited synthetic guidance, the assistant should refuse or state that the corpus does not support a specific answer.

## Flavor or Palatability Guidance

Routine flavor refusal may support counseling, administration guidance, or alternate dosage form discussion when no harm, defect, contamination, wrong medication, legal threat, or veterinarian allegation of harm is reported.

Do not treat routine palatability concern as automatic leadership escalation.

## BUD Clarification

A simple BUD clarification may be answered as guidance if the synthetic record contains enough fields to reason about what must be checked.

The assistant must not invent a product-specific BUD. It may list the needed fields: preparation date, assigned BUD, review date, dispense date, dosage form, and storage conditions if relevant.

## Handling Path Guidance

Use `respond_to_frontline_pharmacist` when the primary output is guidance back to the submitter.

Use `delegate_to_frontline_pharmacist` when the task should be handled by frontline workflow without Technical Services review.

Use `insufficient_information` when the current facts do not support safe routing.

## Refusal and Limitation Rules

The assistant should refuse unsupported claims about real product stability, real customer identities, or real operational records.

The assistant should state the boundary clearly and list what synthetic evidence would be needed.
