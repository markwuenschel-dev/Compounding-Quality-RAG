# Retrieval Holdout Evaluation

Generated: `2026-06-15T22:42:28Z`
Question count: `20`
Top K: `5`

## Summary

| Metric | Score |
|---|---:|
| Hit rate at K | 0.750 |
| Mean reciprocal rank | 0.588 |
| Negative-constraint pass rate | 0.850 |

## Failed expected-source questions

DEV-RET-007-PAIR-0036, DEV-RET-010-PAIR-0093, DEV-RET-011-PAIR-0103, DEV-RET-012-PAIR-0106, DEV-RET-014-PAIR-0157

## Questions with forbidden-source hits

DEV-RET-002-PAIR-0003, DEV-RET-008-PAIR-0054, DEV-RET-010-PAIR-0093

### DEV-RET-002-PAIR-0003

> the customer reports that pen is not at refill mark yet She was asking if she should use 2 clicks instead of 1 She did not report any damage to the pen or that it was broken, just that the clicks weren't pushing out as much medication as before

- Rationale: A dispensing-device concern with another same-lot complaint needs device, quality-review, and trend guidance.
- Expected sources: `SOP-003`, `SOP-006`, `SOP-008`
- Retrieved sources: `SOP-006`, `SOP-005`, `SOP-004`, `SOP-003`
- Forbidden sources: `SOP-005`
- Forbidden hits: `SOP-005`
- Reciprocal rank: 1.000

### DEV-RET-007-PAIR-0036

> for the pet, Fluoxetine HCl Compounded Oral Oil Liquid Chicken Flavored for Dogs & Cats, 15-mg/mL, 30 mL, the reporting customer is reporting and her sister is the customer listed with the clinic and is listed as the the customer at the vet Pet's first dose was on and that is when the pet got sick, , , , there was blood in the stool and was hospitalized on from 8AM to 6PM They took a blood test and everything came out okay but he had some sort of infection that caused vomiting, diarrhea and blood in his stool

- Rationale: Hospitalization and severe GI symptoms require adverse-event and escalation guidance.
- Expected sources: `SOP-005`, `SOP-007`
- Retrieved sources: `SOP-004`
- Forbidden sources: `SOP-002`
- Forbidden hits: None
- Reciprocal rank: 0.000

### DEV-RET-008-PAIR-0054

> long hx of product with us Veterinarian told the customer, therapeutic levels are not adjusting as they would hope

- Rationale: Efficacy and therapeutic-level concerns require administration and reference review rather than a default resolution path.
- Expected sources: `SOP-004`, `SOP-005`
- Retrieved sources: `SOP-004`, `SOP-006`
- Forbidden sources: `SOP-006`
- Forbidden hits: `SOP-006`
- Reciprocal rank: 1.000

### DEV-RET-010-PAIR-0093

> After first dose given around 20 minutes prior to eating Within 1/2 hour of administration pet was having difficulty walking, and general weakness inhibiting normal bodily function Will not report to manufacturer

- Rationale: Difficulty walking and weakness after a dose require adverse-event review.
- Expected sources: `SOP-005`
- Retrieved sources: `SOP-004`, `SOP-002`
- Forbidden sources: `SOP-002`
- Forbidden hits: `SOP-002`
- Reciprocal rank: 0.000

### DEV-RET-011-PAIR-0103

> Did not get specific flavor or strength info, but the customer wants to know what inactive ingredients are in our general ursodiol oral oil suspensions prior to making purchases mentioned to the customer vegan flavoring and sugar free but she is wanting to know specifics

- Rationale: A request for a full inactive-ingredient list requires ingredient and unsupported-information boundaries.
- Expected sources: `SOP-002`, `SOP-005`
- Retrieved sources: `SOP-006`, `SOP-004`
- Forbidden sources: `SOP-007`
- Forbidden hits: None
- Reciprocal rank: 0.000

### DEV-RET-012-PAIR-0106

> New the customer reaching out to ask about where we source the ingredients from for the Ursodiol Capsule 80 mg () Compounding hub details: Ursodeoxycholic Acid, USP I informed her that certain ingredients of our compounds are from USP, but not all

- Rationale: Supplier-source disclosure requires response and public-corpus limitation guidance.
- Expected sources: `SOP-002`, `SOP-005`
- Retrieved sources: `SOP-004`, `SOP-006`, `SOP-001`
- Forbidden sources: `SOP-007`
- Forbidden hits: None
- Reciprocal rank: 0.000

### DEV-RET-014-PAIR-0157

> the customer reported informing the pet was started on Theophylline for chronic bronchitis and the first dose was given the evening of the customer reports the pet was hyper all night and was visibly gagging and looked short of breath Pet was not given another dose and returned back to normal the following day

- Rationale: Shortness of breath after a dose requires adverse-event and escalation-oriented guidance.
- Expected sources: `SOP-005`, `SOP-007`
- Retrieved sources: `SOP-004`, `SOP-006`
- Forbidden sources: `SOP-002`
- Forbidden hits: None
- Reciprocal rank: 0.000

## Interpretation guardrails

- Record the baseline before changing retrieval, SOPs, or chunking.
- A forbidden-source hit means a known irrelevant source entered the top-K results.
- Source-level relevance does not prove that the exact retrieved section is correct.
- Use failed cases to decide whether the bottleneck is corpus coverage, scoring, or chunk boundaries.
