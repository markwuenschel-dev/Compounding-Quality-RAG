# Review-Summary Extraction Engineering Notes

## What problem this layer solves

The user supplies two different kinds of text:

- the original concern, which may contain messy customer language, abbreviations, product strengths, package quantities, symptoms, and reported escalation facts;
- the investigation note, which describes what the pharmacist or reviewer checked and what remains unresolved.

The system must turn those narratives into a controlled `ReviewSummary` without inventing record access, missing negation, or confusing an omitted check with a completed check.

This is not a pure summarization task. It is constrained information extraction plus workflow policy.

## Final extraction architecture

```text
complaint + investigation
          |
          v
LLM candidate extraction
          |
          v
Pydantic schema validation
          |
          v
deterministic grounding
          |
          v
review-scope defaults
          |
          v
unresolved-question generation
          |
          v
field evidence + evaluation
```

### 1. LLM candidate extraction

The LLM handles flexible language and produces a candidate object with controlled fields:

- record-review result
- lot/batch pattern
- inventory result
- reference-review result
- missing information
- evidence limitations
- severe triggers

The LLM is treated as an extraction dependency, not the final decision-maker.

### 2. Pydantic validation

Pydantic rejects malformed enum values, missing fields, and structurally invalid output before downstream workflow logic can use it.

This converts an unreliable text-generation interface into a typed application boundary.

### 3. Deterministic grounding

Rules correct facts that are too important to leave to probabilistic behavior.

Examples:

- `No external reference needed` must not match `external reference needed`.
- `One additional quality complaint was identified for the lot` maps to `similar_concern_same_batch_found`.
- `No additional quality complaints were identified` maps to `no_similar_batch_concerns_found`.
- `Worksheet review found no discrepancy` is an explicit record-review result.
- `Confirm`, `Clarify`, and `Determine whether` introduce unresolved information.
- A complaint-reported hospitalization is proposed as `pet_hospitalization` for reviewer confirmation.
- Supplier/manufacturer non-disclosure maps to `not_supported_by_public_corpus`.

### 4. Review-scope defaults

Silence has different meaning depending on the case.

For a guidance-only question, record review may genuinely be irrelevant. For an adverse event or product-quality investigation, an absent result usually means the required check was not documented.

The policy therefore infers either:

```text
guidance_only
full_investigation
```

Then it applies conservative defaults.

| Field | Guidance only | Full investigation |
|---|---|---|
| Record result absent | `not_applicable` | `documentation_incomplete` |
| Lot result absent | `not_applicable` | `unavailable` |
| Inventory result absent | `not_applicable` | `not_checked` |
| Reference result absent | `not_needed` | `not_needed` |

This prevents the LLM from inventing completed work.

### 5. Unresolved-question generation

Unresolved questions are generated separately from the scalar summary. This keeps two concepts distinct:

- what the investigation currently says;
- what still needs to be confirmed before disposition.

The generator uses bounded, context-specific matching. For example, the word `clicks` in a dosing instruction does not create a device-failure question unless failure language is also present.

### 6. Field evidence

The system attaches supporting text to extracted fields. Reviewer-note evidence is preferred. Complaint evidence may support reported severe triggers that require confirmation.

This makes the output more auditable than a summary with no traceable source.

## Why the system is hybrid instead of LLM-only

An LLM is useful for messy natural language, but safety-relevant workflow facts need deterministic guarantees.

The hybrid design gives:

- flexibility for real-world phrasing;
- strict controlled outputs;
- explicit negation handling;
- conservative defaults;
- repeatable evaluation;
- human confirmation of high-impact fields.

A useful interview phrase is:

> I used the LLM for semantic normalization, then constrained it with typed validation and deterministic domain policy so high-impact workflow fields did not depend on prompt behavior alone.

## What the Python patch and repair scripts were doing

The scripts were one-time repository codemods, similar to small source migrations.

Each script generally:

1. located an exact known code block;
2. refused to continue if the expected block was absent or appeared multiple times;
3. replaced the block with the new implementation;
4. compiled the changed Python files;
5. added or updated regression tests;
6. printed success only after structural verification.

This was useful because the assistant could not directly edit the local repository. The script expressed a reproducible transformation instead of asking for manual line edits.

### What went wrong with the first scripts

Some packages copied fixtures and tests but left runtime edits behind an application step. That created a state where new tests existed before the implementation had changed.

The repair sequence exposed several engineering lessons:

- application and verification must be atomic;
- a patch should fail closed when the repository shape is unexpected;
- complete file replacement is cleaner when only a few files change;
- repeated small repair scripts create unnecessary migration complexity;
- regression tests should accompany the exact failure mechanism.

The later fixes used complete replacement files for small, isolated changes.

## Important failures and what they taught

### Positive phrase matched inside a negated phrase

`No external reference needed` was classified as `external_reference_needed`.

**Lesson:** rule precedence matters. Specific negation rules must run before broad positive patterns.

### Device question generated from unrelated text

`pen` could match inside `suspension`, and `clicks` in a dose instruction could look like a device failure.

**Lesson:** use word boundaries and require failure context, not keyword presence alone.

### Strength or package size mistaken for administered dose

Values such as `15 mg/mL` and `30 mL` are not the administered dose.

**Lesson:** entity type depends on context. Dose detection needs administration verbs or per-dose phrasing.

### Explicit record review overwritten as incomplete

`Worksheet review found no discrepancy` was not recognized by the policy matcher.

**Lesson:** domain language has aliases. Add representative regression cases rather than making a generic regex broader without evidence.

### Explicit lot pattern left as unavailable

The policy knew a lot result was mentioned but did not normalize its meaning.

**Lesson:** presence detection and value extraction are separate problems.

## Evaluation method

The 40 selected paired cases were split into:

- 20 development cases used for error analysis and tuning;
- 20 holdout cases reserved for later unbiased evaluation.

The development extraction benchmark progressed from low scalar consistency and weak missing-information recall to:

- scalar accuracy: `1.0`
- missing-information precision/recall: `1.0 / 1.0`
- severe-trigger precision/recall: `1.0 / 1.0`
- unresolved-question precision/recall: `1.0 / 1.0`

This means the development cases now match the adjudicated expected outputs. It does not prove production accuracy or holdout generalization.

## How to explain this in an interview

### Thirty-second version

> I built a hybrid review-summary extraction layer for messy pharmacy-quality narratives. An LLM proposes a typed summary, Pydantic validates it, and deterministic policy handles negation, missing checks, reference-review states, lot patterns, device context, and severe triggers. I created paired development and holdout cases, used failure analysis to isolate mechanisms rather than prompt-tune blindly, and brought the 20-case development extraction benchmark to 100% across scalar fields, missing information, severe triggers, and unresolved questions.

### Ninety-second version

> The hard part was not calling an LLM. It was making the output trustworthy enough for workflow support. Customer complaints and investigation notes contain messy abbreviations, negation, product strengths, package quantities, and incomplete review steps. I separated semantic extraction from policy. The LLM normalizes the narrative into a candidate `ReviewSummary`; Pydantic enforces the contract; then deterministic grounding handles high-impact cases like `no external reference needed`, same-lot complaints, complaint-reported hospitalization, and supplier non-disclosure. I added a scope policy so silence means `not_applicable` for guidance-only work but `documentation_incomplete`, `unavailable`, or `not_checked` for a full investigation. I evaluated against adjudicated paired cases, fixed mechanisms one at a time, and added regression tests for each failure. The development extraction set now passes 20 out of 20, while the holdout remains untouched. Retrieval is still weaker, which is useful because it shows I am measuring components separately instead of presenting one blended accuracy number.

## Honest limitations

- The benchmark is small.
- The perfect result is on the development set.
- Canonicalized investigations are cleaner than unrestricted production notes.
- The holdout has not yet been used as the final estimate.
- Retrieval remains below the extraction layer.
- The project does not access real records or licensed references.
- Regex-based policy requires regression coverage and careful change control.

## Next technical work

1. Correct retrieval expectations that conflict with confirmed workflow policy.
2. Add adverse-event query expansion and reranking.
3. Improve ingredient-list and supplier-disclosure retrieval.
4. Change SOP text only when the policy is actually absent.
5. Rerun development retrieval.
6. Freeze and run the holdout after development behavior stabilizes.
