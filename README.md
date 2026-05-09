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
