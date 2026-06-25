# Review-Summary Extraction Engineering Notes

Updated: 2026-06-25

## What this layer solves

The user supplies:

- original concern text with messy customer language, product strengths, package quantities, symptoms, severe facts, and possible unsupported record-access requests;
- reviewer/investigation notes describing what was checked and what remains unresolved.

The system must turn those narratives into a controlled `ReviewSummary` without inventing record access, missing negation, treating strength as dose, or confusing omitted checks with completed checks.

This is constrained information extraction plus workflow policy, not pure summarization.

## Current architecture

```text
complaint + reviewer note
-> LLM candidate extraction
-> Pydantic schema validation
-> deterministic grounding
-> review-scope defaults
-> unresolved-question generation
-> field evidence + evaluation
```

## Why hybrid instead of LLM-only

The LLM handles language variation. Deterministic code handles high-impact workflow semantics:

- negation;
- same-lot patterns;
- worksheet/record review aliases;
- completed vs needed references;
- non-disclosure boundaries;
- missing investigation steps;
- device-failure context;
- administered-dose context;
- severe triggers.

Interview phrase:

> I used the LLM for semantic normalization, then constrained it with typed validation and deterministic domain policy so high-impact workflow fields did not depend on prompt behavior alone.

## Important mechanisms

### Pydantic validation

Pydantic rejects malformed enum values, missing fields, and structurally invalid output before downstream workflow logic can use it.

### Deterministic grounding

Examples:

- `No external reference needed` must not become `external_reference_needed`.
- `One additional quality complaint was identified for the lot` maps to `similar_concern_same_batch_found`.
- `Worksheet review found no discrepancy` is an explicit record-review result.
- `Confirm`, `Clarify`, and `Determine whether` introduce unresolved information.
- Supplier/manufacturer/proprietary non-disclosure maps to `not_supported_by_public_corpus`.
- Product strength/package size is not administered dose without administration context.
- Device terms require actual device-failure context.

### Scope defaults

| Field | Guidance only | Full investigation |
|---|---|---|
| Record result absent | `not_applicable` | `documentation_incomplete` |
| Lot result absent | `not_applicable` | `unavailable` |
| Inventory result absent | `not_applicable` | `not_checked` |
| Reference result absent | `not_needed` | `not_needed` |

## Lessons from repairs

### Negation precedence

Positive phrase matching inside negated phrases created false labels.

**Lesson:** specific negation rules must run before broad positive patterns.

### Coordinated negation

`No hospitalization, death, legal threat, contamination, wrong medication concern, or veterinarian allegation was reported` requires list-level negation.

**Lesson:** escalation extraction cannot rely on a short local window only.

### Device and dose context

`pen` can appear inside `suspension`, and `clicks` can be dose instruction rather than failure.

**Lesson:** use word boundaries and require failure/administration context.

### Presence versus value

Detecting that lot information exists is not the same as normalizing it to a controlled lot-pattern value.

**Lesson:** presence detection and value extraction need separate tests.

## Evaluation method

The selected paired cases were split into:

- 20 development cases for error analysis and tuning;
- 20 holdout cases reserved for unbiased evaluation.

Development extraction reached:

- scalar accuracy: `1.0`;
- missing-information precision/recall: `1.0 / 1.0`;
- severe-trigger precision/recall: `1.0 / 1.0`;
- unresolved-question precision/recall: `1.0 / 1.0`.

This is a development result, not production accuracy.

## Current relationship to retrieval

Extraction and retrieval are measured separately.

Retrieval-intent ablation later established Nano semantic intent as the strongest measured frozen-holdout query-interpretation path, with rule intent as deterministic fallback and keyword retrieval as the unchanged retriever after vocabulary mapping.

Retrieval experimentation is closed for the current product milestone. Further Nano latency/cost/cache optimization belongs in a later performance milestone.

## Current product emphasis

- GitHub Actions;
- container health/readiness smoke tests;
- `.env.example`;
- runbook maintenance;
- structured operation logs beyond request correlation.

## Honest limitations

- Benchmark is small.
- Perfect extraction performance is development-set only.
- Canonicalized investigations are cleaner than unrestricted production notes.
- Regex-based policy needs regression coverage.
- Public project does not access real records, internal systems, proprietary SOPs, or licensed references.
- Tool supports human review; it does not make final clinical/legal/quality/customer-resolution decisions.

## When to reopen extraction work

Reopen this layer when:

- holdout/regression cases expose a concrete extraction failure;
- schema changes;
- reviewer UI requires new evidence or unresolved-question fields;
- larger corpus introduces new language patterns.
