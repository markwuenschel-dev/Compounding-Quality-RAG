---
document_id: SOP-008
title: Trend and Pattern Monitoring Rules
version: "1.0"
effective_date: "2025-01-01"
process_area: trend_monitoring
source_type: sop
synthetic: true
---

# Trend and Pattern Monitoring Rules

## Purpose

This synthetic SOP defines how the public RAG project should discuss trend and pattern review.

This document is synthetic. It does not represent complete operational surveillance.

## Trend Review Boundary

Trend monitoring is a review condition, not a final handling path.

The public RAG system can identify that trend review is relevant or reason over supplied synthetic trend summaries. It cannot claim complete surveillance of real records.

## Required Fields for Trend Review

Trend review may require medication or product placeholder, dosage form, concern type, date range, batch or lot if relevant, site or source if supplied, and synthetic record count.

If these fields are missing, the assistant should state the limitation.

## Synthetic Thresholds

Synthetic thresholds for this project may include three similar concerns within 30 days using medication, dosage form, and concern type; five similar concerns within 90 days using medication, dosage form, and concern type; or two serious concerns tied to the same lot or batch.

These thresholds are artificial and exist only for the public synthetic project.

## Similar Concern Same Batch

If similar concerns appear tied to the same lot or batch, the case may require higher attention, inventory inspection if available, and possible escalation depending on severity.

## Similar Concern Same Medication and Dosage Form

Similar concerns involving the same medication and dosage form may support pattern review, but they do not automatically prove a product defect.

## No Similar Concerns Found

A synthetic summary of no similar concerns found may support routine handling when no other escalation triggers are present.

Do not state that no real-world trend exists.

## Trend Threshold Met

If the synthetic trend threshold is met, the assistant should flag the pattern and recommend review according to the relevant SOP.

Trend threshold alone does not determine refund, reship, or clinical causality.

## Refusal and Limitation Rules

Allowed language includes that the supplied synthetic review summary states no similar batch concerns were found, the public corpus does not support complete API-level surveillance, and trend review is limited by available synthetic fields.

Do not say no other customers reported the issue, there is no trend in production data, or the batch is confirmed defective.
