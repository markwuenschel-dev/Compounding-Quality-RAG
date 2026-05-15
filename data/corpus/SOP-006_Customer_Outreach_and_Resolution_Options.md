---
document_id: SOP-006
title: Customer Outreach and Resolution Options
version: "1.0"
effective_date: "2025-01-01"
process_area: customer_outreach_resolution
source_type: sop
synthetic: true
---

# Customer Outreach and Resolution Options

## Purpose

This synthetic SOP defines when customer outreach and customer-facing resolution review may be considered.

This document is synthetic and is not real company policy.

## Outreach Decision Boundary

Customer outreach depends on case context. The RAG system may not know whether outreach is required until it reads the review note or synthetic review summary.

Use null or unknown for customer outreach requirement when the current evidence does not support a definite answer.

## Outreach Generally Supported

Customer outreach may be supported when customer review text reports a quality or safety concern, suspected ADE context requires more information, product defect or device failure is reported, resolution options require customer confirmation, or missing information cannot be resolved from the synthetic record.

## Outreach Not Automatically Expected

Outreach is not automatically expected when a low-star review has no text, no quality or safety concern is identified, the issue is a frontline guidance question, or the synthetic case supports document-only handling.

## Resolution Options

Resolution options are customer-facing or case-closure possibilities. They are separate from handling path.

Allowed resolution options include replacement or reship review, refund or concession review, alternate dosage form discussion, counseling or follow-up, leadership-directed resolution, and no customer-facing resolution.

## Flavor Refusal

Routine flavor refusal usually supports counseling or follow-up and may support alternate dosage form discussion.

Do not assume refund, reship, or concession solely because a pet refused flavor.

## Device or Equipment Concerns

Missing equipment, leaking transdermal pen, or apparent transdermal pen failure may support replacement or reship review when the synthetic case supports unusable product, missing equipment, or device failure.

## Suspected ADE

Suspected ADE may support counseling or follow-up. Replacement, reship, refund, or concession should not be assumed unless separately supported.

## Escalated Cases

When leadership escalation criteria are present, resolution review should follow escalation rather than precede it.

Use `leadership_directed_resolution` only when escalation criteria or synthetic review summary supports it.

## Refusal and Limitation Rules

The assistant must not promise a refund, reship, replacement, concession, or customer contact.

The assistant may say the case supports review of those options.
