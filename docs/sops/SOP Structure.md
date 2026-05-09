# SOP Structure

This template defines the preferred structure for synthetic SOP-like Markdown files in the Compounding Quality RAG project. SOPs are authority-bearing process documents. They should be structured enough for heading-based chunking and citation preservation.

## Metadata

```yaml
Document ID: SOP-###
Title: Synthetic SOP Title
Version: 1.0
Effective Date: YYYY-MM-DD
Process Area: short process area name
Source Type: sop
Synthetic: true
```

## Purpose

State what this synthetic SOP controls or explains. Keep the purpose short and specific.

## Scope

Describe which synthetic situations are covered and which situations are outside the SOP boundary.

The scope should avoid implying access to real internal systems, real customer records, real compounding records, licensed drug-information content, or proprietary operational data.

## Raw Intake Fields

List the fields that may be available before Technical Services review begins.

Examples:

- intake source
- submitter role
- submission purpose
- concern narrative
- star rating for customer reviews
- review text presence for customer reviews
- submitter-selected classification, if present
- known product or dosage-form context, if present

Raw intake fields are not the same as reviewer conclusions.

## Review Checklist

List what the reviewer should check or consider.

Examples:

- whether frontline guidance applies
- whether record review is required
- whether lot or batch review is required
- whether customer outreach is required
- whether escalation triggers are present
- whether the public synthetic corpus supports an answer

The checklist may describe what a reviewer should check, but it should not claim the RAG system directly accessed operational systems.

## Investigation Requirements

When useful, define checklist flags that can be represented in synthetic inquiry records.

Examples:

```yaml
investigation_requirements:
  record_review_required: true
  lot_batch_review_required: true
  inventory_inspection_required: false
  trend_scan_required: true
  customer_outreach_required: true
  frontline_guidance_lookup_required: false
  technical_services_response_required: true
```

## Derived Outputs

List the fields or assessments that may be produced after review.

Examples:

- reviewer-assigned classification
- reviewer-assigned category and subcategory
- concern type
- review scope
- risk lane
- escalation triggers
- handling path
- resolution review requirement
- resolution options
- missing information
- evidence limitations

Derived outputs should not be treated as raw intake fields.

## Risk-Lane or Escalation Criteria

Define when a case remains expected/self-limiting, becomes unexpected/non-life-threatening, or enters a life-threatening/legal escalation lane.

Escalation criteria should be explicit and conservative.

## Customer Outreach / Resolution Notes

Describe when customer outreach is expected and which resolution options may be reviewed.

Resolution options are separate from handling path.

Examples:

- counseling or follow-up
- replacement or reship review
- refund or concession review
- alternate dosage form discussion
- leadership-directed resolution
- no customer-facing resolution

## Authority and Evidence Rules

State what kind of evidence this SOP can support.

Examples:

- SOPs can support process guidance.
- Synthetic inquiries can support examples only.
- Synthetic API references can support limited adverse-effect plausibility examples only.
- If authoritative evidence is missing, the system should refuse or state that the corpus does not support the answer.

## Limitations

Describe what the SOP does not cover. Include public-safety limitations.

Examples:

- This synthetic SOP is not real policy.
- It does not contain proprietary SOP text.
- It does not use real customer or patient data.
- It does not replace pharmacist judgment.
- It does not provide clinical decision support.
- It does not claim direct access to compounding records, inventory systems, lot-tracing systems, Snowflake, or external drug-information resources.
