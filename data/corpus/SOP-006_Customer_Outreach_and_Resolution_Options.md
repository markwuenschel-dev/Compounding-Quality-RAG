---
document_id: SOP-006
title: Customer Outreach and Resolution Options
version: "1.1"
effective_date: "2025-01-01"
process_area: customer_outreach_resolution
source_type: sop
synthetic: true
---

# Customer Outreach and Resolution Options

## Purpose

This synthetic SOP defines when customer outreach, document-only handling, frontline guidance handling, and customer-facing resolution review may be considered.

This document is synthetic and is not real company policy.

## Outreach Decision Boundary

Customer outreach depends on case context. The RAG system may not know whether outreach is required until it reads the review note or synthetic review summary.

Use null or unknown for customer outreach requirement when the current evidence does not support a definite answer.

## Outreach Generally Supported

Customer outreach may be supported when customer review text reports a quality or safety concern, suspected ADE context requires more information, product defect or device failure is reported, resolution options require customer confirmation, or missing information cannot be resolved from the synthetic record.

## Outreach Not Automatically Expected

Outreach is not automatically expected when a low-star review has no text, no quality or safety concern is identified, the issue is a frontline guidance question, or the synthetic case supports document-only handling.

## Low-Star Reviews With No Review Text

One-star and two-star customer reviews, and three-star customer reviews with no review text, may be documented without Technical Services outreach when no quality concern, safety concern, suspected ADE, product defect, wrong medication, wrong patient, contamination, or other escalation trigger is identified.

A blank or low-star review does not by itself establish a product quality issue, adverse event, dispensing error, product defect, contamination concern, or need for customer-facing Technical Services outreach.

Use document-only handling when the synthetic case supports no customer-facing outreach, no additional review requirement, and no severe escalation trigger.

## Document-Only and Frontline Guidance Handling

Document-only handling may be appropriate when a review contains no customer narrative, no quality or safety concern, no suspected ADE, no product defect, no dispensing error, and no severe escalation trigger.

Frontline guidance questions that do not require Technical Services outreach may be routed back to the frontline pharmacist with the applicable limitation, missing-information statement, or unsupported-evidence boundary.

Do not create Technical Services outreach solely from a low-star rating, blank review text, or unsupported product-specific question when no customer-facing quality concern is described.

## Resolution Options

Resolution options are customer-facing or case-closure possibilities. They are separate from handling path.

Allowed resolution options include replacement or reship review, refund or concession review, alternate dosage form discussion, counseling or follow-up, leadership-directed resolution, and no customer-facing resolution.

## Flavor Refusal

Routine flavor refusal usually supports counseling or follow-up and may support alternate dosage form discussion.

Do not assume refund, reship, or concession solely because a pet refused flavor.

## Flavor refusal vs vomiting	
Actual vomiting after administration routes suspected ADE; refusal/spit-out routes flavor refusal; unclear retching is insufficient info.

## Temperature excursion	
Frontline guidance; no TS outreach for temp excursion alone; product-specific stability outside 72-hour window unsupported.

## Ingredient/formula question	
Delegate/respond to frontline; public demo cannot answer formula-specific content.
Suspected ADE risk	Unexpected non-life-threatening unless severe trigger is confirmed.
Severe triggers	Override every routine route.
General question with customer outreach	Needs explicit handling-path distinction.

## Device or Equipment Concerns

Missing equipment, leaking transdermal pen, or apparent transdermal pen failure may support replacement or reship review when the synthetic case supports unusable product, missing equipment, or device failure.

## Suspected ADE

Suspected ADE may support counseling or follow-up. Replacement, reship, refund, or concession should not be assumed unless separately supported.

### Suspected ADE risk	
Unexpected non-life-threatening unless severe trigger is confirmed.

## Escalated Cases

When leadership escalation criteria are present, resolution review should follow escalation rather than precede it.
Severe triggers override every routine route.

Use `leadership_directed_resolution` only when escalation criteria or synthetic review summary supports it.

## Refusal and Limitation Rules

The assistant must not promise a refund, reship, replacement, concession, customer contact, or Technical Services outreach.

The assistant may say the case supports review of those options when the supplied synthetic facts support them.
