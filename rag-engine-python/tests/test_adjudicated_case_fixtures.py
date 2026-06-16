from __future__ import annotations

import json
from pathlib import Path

from app.holdout_evaluate import load_retrieval_holdout_questions
from app.review_summary_evaluate import load_review_summary_extraction_cases


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = PROJECT_ROOT / "data" / "eval"


def test_development_and_holdout_extraction_fixtures_are_valid_and_disjoint() -> None:
    development = load_review_summary_extraction_cases(
        EVAL_DIR / "review_summary_extraction_development.json"
    )
    holdout = load_review_summary_extraction_cases(
        EVAL_DIR / "review_summary_extraction_holdout.json"
    )

    assert len(development) == 20
    assert len(holdout) == 20

    development_ids = {case["case_id"] for case in development}
    holdout_ids = {case["case_id"] for case in holdout}

    assert development_ids.isdisjoint(holdout_ids)


def test_development_and_holdout_retrieval_fixtures_are_valid_and_disjoint() -> None:
    development = load_retrieval_holdout_questions(
        EVAL_DIR / "retrieval_questions_development.json"
    )
    holdout = load_retrieval_holdout_questions(
        EVAL_DIR / "retrieval_questions_holdout.json"
    )

    assert len(development) == 20
    assert len(holdout) == 20

    development_ids = {question["question_id"] for question in development}
    holdout_ids = {question["question_id"] for question in holdout}

    assert development_ids.isdisjoint(holdout_ids)


def test_retrieval_expectations_use_known_sources_without_overlap() -> None:
    known_sources = {f"SOP-{number:03d}" for number in range(1, 9)}

    for filename in (
        "retrieval_questions_development.json",
        "retrieval_questions_holdout.json",
    ):
        questions = json.loads(
            (EVAL_DIR / filename).read_text(encoding="utf-8")
        )

        for question in questions:
            expected = set(question["expected_source_ids"])
            forbidden = set(question.get("forbidden_source_ids", []))

            assert expected
            assert expected <= known_sources
            assert forbidden <= known_sources
            assert expected.isdisjoint(forbidden)
