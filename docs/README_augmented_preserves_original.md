# Compounding-Quality-RAG

## 1. Problem Statement
Technical Services (TS) pharmacists review compounding-related quality signals from two primary workflows:
- Frontline compounding quality related event (QRE) submissions
- Negative customer reviews posted to the customer facing product page
These workflows require repeated document lookup, categorization, and judgment calls across similar but not identical cases, such as formula changes and compounding record review. 

Compounding-Quality-RAG is a retrieval-augmented-generation prototype designed to reduce mechanical review time by retrieving the most relevant ingredient records, SOPs, formula changes, and historical examples for a TS pharmacist. The system is not intended to make final quality or clinical decisions. It's purpose is to surface evidence, summarize context, and support consistent pharmacist review.

## 2. Workflow Context (“What does a TS pharmacist actually do step-by-step before this system exists?”)
A TS pharmacist's reciew starts with a QRE form submission or a moderated customer review gets posted to the website for a compounded prescription product.
1. First, read the review or QRE submission text.
2. Validate submitted information is correct, such as lot number, CID, order number.
3. Review the compounding record of the associated lot and document incident number.
4. Perform an environmental/clinical workup. Timeline, medication side effects, pet behavior changes, storage, dispensing, or shipping issues, and any reported clinic/DVM notes.
5. Determine if the customer needs outreach and whether a refund, replacement, or concession is appropriate.
6. Document call (even if voicemail) to the respective tracker and order page.

## 3. What the System Does (“If I gave this tool to a pharmacist, what changes in their workflow?”)
When the compounding quality RAG functions appropriately, steps 2 - 5 would be greatly reduced. The tool would give context from the medication, the compounding record, the order page in a consistent manner that would help the TS pharmacist determine if a customer outreach is necessary. It may give context on if a refund, replacement, or concession is needed.


## 4. What the System Does Not Do (“Where does this system stop so people don’t overtrust it?”)
- The tool does not mutate any data, it is read only.
- The tool does not replace TS pharmacist review of the compounding record.
- The tool may point out missing sections, notes, deviations, for the TS pharmacist to verify.
- The tool is a decision-support aid. A TS pharmacist may disagree with, ignore, or override its output using professional judgment. Source records remain authoritative.

---

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
