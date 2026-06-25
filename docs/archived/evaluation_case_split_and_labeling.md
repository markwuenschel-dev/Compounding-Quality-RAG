# Evaluation Case Split and Labeling

The 40 selected complaint/investigation pairs are split into:

- 20 development cases for baseline measurement, error analysis, and tuning.
- 20 holdout cases that should remain untouched until the development changes are complete.

## Files

```text
rag-engine-python/data/eval/review_summary_extraction_development.json
rag-engine-python/data/eval/review_summary_extraction_holdout.json
rag-engine-python/data/eval/retrieval_questions_development.json
rag-engine-python/data/eval/retrieval_questions_holdout.json
rag-engine-python/data/eval/candidates/selected_case_adjudication.csv
rag-engine-python/data/eval/candidates/selected_case_adjudication.json
rag-engine-python/tests/test_adjudicated_case_fixtures.py
```

## Labeling rules

- Review-summary labels use the controlled enum contract.
- Missing-information labels follow explicit unresolved investigation items.
- Severe triggers are conservative and include only existing structured trigger values.
- `pet_hospitalization` is expected in the hospitalization case because it is explicit in the paired complaint and not contradicted by the investigation.
- Neurologic signs, respiratory distress, and collapse-like events remain serious context but are not forced into a trigger enum that does not represent them.
- Retrieval expectations identify one or more relevant SOP sources.
- Forbidden sources are used only when a source would materially misroute the case.

## Audit flags

The adjudication files contain `audit_flags` for cases with:

- a canonicalization artifact,
- a complaint fact dropped from the investigation summary,
- an external-reference enum ambiguity,
- incomplete investigation coverage,
- or a weak complaint/investigation hypothesis.

Review those rows before freezing the holdout.

## Run order

From `rag-engine-python`:

```powershell
python -m pytest tests/test_adjudicated_case_fixtures.py
python -m pytest

python -m app.holdout_evaluate extraction `
  --cases data/eval/review_summary_extraction_development.json `
  --report reports/review_summary_extraction_development.md

python -m app.holdout_evaluate retrieval `
  --questions data/eval/retrieval_questions_development.json `
  --report reports/retrieval_development.md
```

Record the development baseline before changing extraction, retrieval, SOPs, or chunking.

After development fixes are complete and the audit flags have been reviewed:

```powershell
python -m app.holdout_evaluate validate
python -m app.holdout_evaluate freeze
python -m app.holdout_evaluate all
```

Do not tune against the holdout results. If an expected label is wrong, document the adjudication correction separately from model tuning.
