from pathlib import Path

import pytest

from app.retrieval_evaluate import (
    DEFAULT_RETRIEVAL_QUESTIONS_PATH,
    RetrievalQuestion,
    RetrievalQuestionResult,
    calculate_hit_rate,
    calculate_mean_reciprocal_rank,
    calculate_reciprocal_rank,
    evaluate_retrieval_question,
    evaluate_retrieval_questions,
    load_and_evaluate_retrieval_questions,
    load_retrieval_questions,
    parse_retrieval_question,
    unique_in_order,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHUNKS_PATH = PROJECT_ROOT / "data" / "index" / "chunks.jsonl"


def test_retrieval_questions_file_exists() -> None:
    assert DEFAULT_RETRIEVAL_QUESTIONS_PATH.exists()


def test_load_retrieval_questions_returns_questions() -> None:
    questions = load_retrieval_questions(DEFAULT_RETRIEVAL_QUESTIONS_PATH)

    assert questions
    assert questions[0]["question_id"]
    assert questions[0]["query"]
    assert questions[0]["expected_source_ids"]


def test_parse_retrieval_question_rejects_missing_required_key() -> None:
    raw_question = {
        "question_id": "RET-BAD",
        "query": "missing expected sources",
    }

    with pytest.raises(ValueError, match="missing keys"):
        parse_retrieval_question(raw_question, index=0)


def test_parse_retrieval_question_rejects_empty_expected_sources() -> None:
    raw_question = {
        "question_id": "RET-BAD",
        "query": "empty expected sources",
        "expected_source_ids": [],
    }

    with pytest.raises(ValueError, match="at least one expected source"):
        parse_retrieval_question(raw_question, index=0)


def test_unique_in_order_removes_duplicates_without_reordering() -> None:
    values = ["SOP-001", "SOP-002", "SOP-001", "SOP-003", "SOP-002"]

    result = unique_in_order(values)

    assert result == ["SOP-001", "SOP-002", "SOP-003"]


@pytest.mark.parametrize(
    ("retrieved_source_ids", "expected_source_ids", "expected_rr"),
    [
        (["SOP-001", "SOP-002"], ["SOP-001"], 1.0),
        (["SOP-003", "SOP-002"], ["SOP-002"], 0.5),
        (["SOP-003", "SOP-004"], ["SOP-999"], 0.0),
    ],
)
def test_calculate_reciprocal_rank(
    retrieved_source_ids: list[str],
    expected_source_ids: list[str],
    expected_rr: float,
) -> None:
    reciprocal_rank = calculate_reciprocal_rank(
        retrieved_source_ids=retrieved_source_ids,
        expected_source_ids=expected_source_ids,
    )

    assert reciprocal_rank == expected_rr


def test_calculate_hit_rate() -> None:
    question_results: list[RetrievalQuestionResult] = [
        {
            "question_id": "RET-001",
            "query": "query one",
            "expected_source_ids": ["SOP-001"],
            "retrieved_source_ids": ["SOP-001"],
            "hit": True,
            "reciprocal_rank": 1.0,
        },
        {
            "question_id": "RET-002",
            "query": "query two",
            "expected_source_ids": ["SOP-999"],
            "retrieved_source_ids": ["SOP-001"],
            "hit": False,
            "reciprocal_rank": 0.0,
        },
    ]

    assert calculate_hit_rate(question_results) == 0.5


def test_calculate_mean_reciprocal_rank() -> None:
    question_results: list[RetrievalQuestionResult] = [
        {
            "question_id": "RET-001",
            "query": "query one",
            "expected_source_ids": ["SOP-001"],
            "retrieved_source_ids": ["SOP-001"],
            "hit": True,
            "reciprocal_rank": 1.0,
        },
        {
            "question_id": "RET-002",
            "query": "query two",
            "expected_source_ids": ["SOP-002"],
            "retrieved_source_ids": ["SOP-001", "SOP-002"],
            "hit": True,
            "reciprocal_rank": 0.5,
        },
        {
            "question_id": "RET-003",
            "query": "query three",
            "expected_source_ids": ["SOP-999"],
            "retrieved_source_ids": ["SOP-001"],
            "hit": False,
            "reciprocal_rank": 0.0,
        },
    ]

    assert calculate_mean_reciprocal_rank(question_results) == 0.5


def test_evaluate_retrieval_question_returns_result() -> None:
    question: RetrievalQuestion = {
        "question_id": "RET-TEST",
        "query": "pet refuses flavored oral liquid palatability flavor concern",
        "expected_source_ids": ["SOP-001", "SOP-004", "SOP-006"],
    }

    result = evaluate_retrieval_question(
        question,
        chunks_path=CHUNKS_PATH,
        top_k=5,
    )

    assert result["question_id"] == "RET-TEST"
    assert result["query"] == question["query"]
    assert result["expected_source_ids"] == question["expected_source_ids"]
    assert result["retrieved_source_ids"]
    assert isinstance(result["hit"], bool)
    assert 0 <= result["reciprocal_rank"] <= 1


def test_evaluate_retrieval_questions_returns_metrics() -> None:
    questions = load_retrieval_questions(DEFAULT_RETRIEVAL_QUESTIONS_PATH)

    result = evaluate_retrieval_questions(
        questions,
        chunks_path=CHUNKS_PATH,
        top_k=5,
    )

    assert result["total_questions"] == len(questions)
    assert result["top_k"] == 5
    assert 0 <= result["hit_rate_at_k"] <= 1
    assert 0 <= result["mean_reciprocal_rank"] <= 1
    assert len(result["question_results"]) == len(questions)


def test_load_and_evaluate_retrieval_questions_runs_end_to_end() -> None:
    result = load_and_evaluate_retrieval_questions(
        questions_path=DEFAULT_RETRIEVAL_QUESTIONS_PATH,
        chunks_path=CHUNKS_PATH,
        top_k=5,
    )

    assert result["total_questions"] > 0
    assert 0 <= result["hit_rate_at_k"] <= 1
    assert 0 <= result["mean_reciprocal_rank"] <= 1


def test_evaluate_retrieval_questions_rejects_empty_questions() -> None:
    with pytest.raises(ValueError, match="at least one"):
        evaluate_retrieval_questions([], chunks_path=CHUNKS_PATH)


def test_evaluate_retrieval_questions_rejects_invalid_top_k() -> None:
    questions = load_retrieval_questions(DEFAULT_RETRIEVAL_QUESTIONS_PATH)

    with pytest.raises(ValueError, match="top_k"):
        evaluate_retrieval_questions(
            questions,
            chunks_path=CHUNKS_PATH,
            top_k=0,
        )


def test_evaluation_reports_failed_question_ids_for_impossible_expected_source() -> None:
    questions: list[RetrievalQuestion] = [
        {
            "question_id": "RET-IMPOSSIBLE",
            "query": "pet refuses flavored oral liquid",
            "expected_source_ids": ["SOP-DOES-NOT-EXIST"],
        }
    ]

    result = evaluate_retrieval_questions(
        questions,
        chunks_path=CHUNKS_PATH,
        top_k=5,
    )

    assert result["hit_rate_at_k"] == 0
    assert result["mean_reciprocal_rank"] == 0
    assert result["failed_question_ids"] == ["RET-IMPOSSIBLE"]