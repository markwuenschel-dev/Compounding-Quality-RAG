# Suggested README Additions

These sections are written as optional append-only material. They are not intended to replace the existing README text.

## Proposed Section: Data Boundary and Synthetic Corpus

This repository uses synthetic SOP-like guidance and synthetic inquiry records. The workflow shape is based on domain understanding, but the public corpus does not include real customer records, patient information, proprietary SOP language, internal screenshots, real compounding records, real customer reviews, licensed drug-information content, or direct internal system/API names.

The synthetic records are designed to test whether the system can separate raw intake, reviewer-entered findings, source-cited guidance, and final pharmacist judgment.

## Proposed Section: Workflow Model

The workflow separates several concepts that are easy to collapse:

- `intake_source`: where the record came from, such as the QRE/general-question form or a customer review.
- `submitter_role`: who submitted or triggered the record.
- `submission_purpose`: why the submission exists.
- `review_scope`: how much investigation is required.
- `handling_path`: the operational response after review.

A frontline pharmacist question is not a separate intake source. It is modeled as a QRE/general-question form submission with `submitter_role: frontline_pharmacist` and `submission_purpose: frontline_pharmacist_question`.

## Proposed Section: Two Operating Modes

The project supports two intended modes:

1. Intake/checklist mode: given raw intake text, identify what should be checked, what information is missing, and what SOP guidance applies.
2. Review-summary mode: given reviewer-entered findings, identify what handling path is supported, whether escalation or outreach is indicated, and what evidence supports the conclusion.

The system should not silently finalize review fields. It may draft structured fields from narrative, but reviewer confirmation is required.

## Proposed Section: Authority Rules

SOP-like documents can support process guidance. Synthetic inquiry records can support examples and pattern recognition only. Synthetic inquiry examples cannot override SOP guidance. If the corpus lacks authoritative evidence for a process claim, the system should refuse or state that the available corpus does not support the answer.

## Proposed Section: Current Build Stage

Current stage: corpus and schema design.

Next implementation milestone: load SOP Markdown files and synthetic inquiry YAML files into typed Python objects, validate required fields, and make invalid records fail clearly before moving to chunking or embeddings.

## Prompts for Mark to Rewrite in His Own Words

1. Why is a frontline pharmacist question tracked separately from a customer-reported concern even though it comes through the same form?
2. Why is `respond_to_frontline_pharmacist` different from `delegate_to_frontline_pharmacist`?
3. What should the system do when a submission is guidance-only and does not require compounding-record review?
4. Why should review-summary fields require reviewer confirmation?
5. What would be unsafe to claim in a public synthetic version of this project?
