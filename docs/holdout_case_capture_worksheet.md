# Holdout Case Capture Worksheet

Updated: 2026-06-25

Use one copy of this section per candidate. Keep candidate notes outside active JSON fixtures until the expected answer is adjudicated.

Do not run the model against a candidate before expected outputs are written and reviewed.

---

## Candidate ID

`CANDIDATE-___`

## Evaluation lane

- [ ] Narrative extraction
- [ ] Retrieval relevance
- [ ] Retrieval intent labeling
- [ ] Both extraction and retrieval

## Data boundary check

- [ ] Synthetic or fully de-identified text only
- [ ] No customer identifiers
- [ ] No patient identifiers
- [ ] No veterinarian identifiers
- [ ] No prescription/order identifiers
- [ ] No compounding-record or inventory details from real systems
- [ ] No proprietary SOP text
- [ ] No licensed drug-reference content
- [ ] No internal screenshots or system names

## Synthetic customer concern

> Paste the synthetic or fully de-identified customer concern here.

## Synthetic pharmacist/reviewer investigation note

> Paste the messy synthetic or fully de-identified pharmacist/reviewer note here.

## Why this case is useful

Describe the ambiguity, shorthand, contradiction, retrieval trap, policy boundary, or safety-sensitive detail being tested.

Examples:

- negated hospitalization;
- complaint-reported severe trigger;
- dose vs concentration confusion;
- device directions without device failure;
- supplier/manufacturer non-disclosure;
- external reference consulted vs still needed;
- same-lot pattern wording;
- guidance-only silence vs incomplete full investigation.

## Expected narrative extraction

| Field | Expected value | Evidence from note or complaint | Policy rationale |
|---|---|---|---|
| `record_review_result` |  |  |  |
| `lot_batch_pattern_summary` |  |  |  |
| `inventory_inspection_result` |  |  |  |
| `api_reference_review_result` |  |  |  |
| `customer_context_summary` |  |  |  |

### Expected missing information

- 

### Expected evidence limitations

- 

### Expected severe triggers observed

- 

### Expected unresolved field names

- 

## Expected retrieval

### Expected source IDs

- 

### Forbidden source IDs

- 

### Retrieval rationale

Explain why each expected source is relevant and why each forbidden source would be materially misleading.

Do not forbid a source merely because another source is better.

## Optional expected semantic intent

Use only if this case is intended to evaluate semantic intent labels.

### Expected semantic intent tags

- 

### Expected derived intent tags

- 

### Intent rationale

Explain which tags describe semantic facts from the complaint and which tags are deterministic workflow consequences.

## Ambiguity review

- [ ] Expected answer is clear under current policy
- [ ] Ambiguity is intentional and documented
- [ ] Case should be excluded or held for discussion

Notes:

> 

## Adjudication

- [ ] Expected answer written before running the model
- [ ] Expected answer reviewed for ambiguity
- [ ] No real or protected data included
- [ ] Added to development fixture
- [ ] Added to frozen holdout fixture
- [ ] Added to regression/challenge fixture
- [ ] Holdout manifest updated after fixture change

## Failure classification after first run

If the model/evaluator fails after the case is frozen, classify the failure before changing code:

- [ ] extraction prompt failure
- [ ] deterministic grounding failure
- [ ] review-scope default failure
- [ ] unresolved-question generation failure
- [ ] schema or contract failure
- [ ] retrieval scoring/ranking failure
- [ ] semantic intent detection failure
- [ ] deterministic workflow derivation failure
- [ ] vocabulary mapping failure
- [ ] cache/fallback provenance failure
- [ ] missing corpus guidance
- [ ] chunk-boundary failure
- [ ] ambiguous or incorrect expected answer
- [ ] public-boundary/refusal failure

Notes:

>
