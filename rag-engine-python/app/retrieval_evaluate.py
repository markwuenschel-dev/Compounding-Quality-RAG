from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypedDict

from app.retrieval import DEFAULT_CHUNKS_PATH, retrieve


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RETRIEVAL_QUESTIONS_PATH = PROJECT_ROOT / "data" / "eval" / "retrieval_questions.json"


class RetrievalQuestion(TypedDict):
    question_id: str
    query: str
    expected_source_ids: list[str]


class RetrievalQuestionResult(TypedDict):
    question_id: str
    query: str
    expected_source_ids: list[str]
    retrieved_source_ids: list[str]
    hit: bool
    reciprocal_rank: float


class RetrievalEvaluationResult(TypedDict):
    total_questions: int
    top_k: int
    hit_rate_at_k: float
    mean_reciprocal_rank: float
    failed_question_ids: list[str]
    question_results: list[RetrievalQuestionResult]


def load_retrieval_questions(
    questions_path: Path = DEFAULT_RETRIEVAL_QUESTIONS_PATH,
) -> list[RetrievalQuestion]:
    if not questions_path.exists():
        raise FileNotFoundError(
            f"Retrieval questions file does not exist: {questions_path}"
        )

    raw_data = json.loads(questions_path.read_text(encoding="utf-8"))

    if not isinstance(raw_data, list):
        raise ValueError("Retrieval questions file must contain a JSON list")

    questions: list[RetrievalQuestion] = []

    for index, raw_question in enumerate(raw_data):
        questions.append(parse_retrieval_question(raw_question, index))

    if not questions:
        raise ValueError("Retrieval questions file must contain at least one question")

    return questions


def parse_retrieval_question(
    raw_question: object,
    index: int,
) -> RetrievalQuestion:
    if not isinstance(raw_question, dict):
        raise ValueError(f"Retrieval question at index {index} must be an object")

    required_keys = {"question_id", "query", "expected_source_ids"}
    missing_keys = required_keys - raw_question.keys()

    if missing_keys:
        raise ValueError(
            f"Retrieval question at index {index} is missing keys: {sorted(missing_keys)}"
        )

    question_id = str(raw_question["question_id"])
    query = str(raw_question["query"])
    expected_source_ids_raw = raw_question["expected_source_ids"]

    if not question_id:
        raise ValueError(f"Retrieval question at index {index} has empty question_id")

    if not query:
        raise ValueError(f"Retrieval question {question_id} has empty query")

    if not isinstance(expected_source_ids_raw, list):
        raise ValueError(
            f"Retrieval question {question_id} expected_source_ids must be a list"
        )

    expected_source_ids = [str(source_id) for source_id in expected_source_ids_raw]

    if not expected_source_ids:
        raise ValueError(
            f"Retrieval question {question_id} must have at least one expected source"
        )

    return {
        "question_id": question_id,
        "query": query,
        "expected_source_ids": expected_source_ids,
    }


def evaluate_retrieval_questions(
    questions: list[RetrievalQuestion],
    *,
    chunks_path: Path = DEFAULT_CHUNKS_PATH,
    top_k: int = 5,
) -> RetrievalEvaluationResult:
    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    if not questions:
        raise ValueError("questions must contain at least one retrieval question")

    question_results = [
        evaluate_retrieval_question(
            question,
            chunks_path=chunks_path,
            top_k=top_k,
        )
        for question in questions
    ]

    failed_question_ids = [
        result["question_id"]
        for result in question_results
        if not result["hit"]
    ]

    return {
        "total_questions": len(question_results),
        "top_k": top_k,
        "hit_rate_at_k": calculate_hit_rate(question_results),
        "mean_reciprocal_rank": calculate_mean_reciprocal_rank(question_results),
        "failed_question_ids": failed_question_ids,
        "question_results": question_results,
    }


def evaluate_retrieval_question(
    question: RetrievalQuestion,
    *,
    chunks_path: Path = DEFAULT_CHUNKS_PATH,
    top_k: int = 5,
) -> RetrievalQuestionResult:
    search_results = retrieve(
        query=question["query"],
        chunks_path=chunks_path,
        top_k=top_k,
        source_type="sop",
    )

    retrieved_source_ids = unique_in_order(
        [
            result["chunk"]["source_id"]
            for result in search_results
        ]
    )

    reciprocal_rank = calculate_reciprocal_rank(
        retrieved_source_ids=retrieved_source_ids,
        expected_source_ids=question["expected_source_ids"],
    )

    return {
        "question_id": question["question_id"],
        "query": question["query"],
        "expected_source_ids": question["expected_source_ids"],
        "retrieved_source_ids": retrieved_source_ids,
        "hit": reciprocal_rank > 0,
        "reciprocal_rank": reciprocal_rank,
    }


def calculate_hit_rate(
    question_results: list[RetrievalQuestionResult],
) -> float:
    if not question_results:
        raise ValueError("question_results must not be empty")

    hit_count = sum(1 for result in question_results if result["hit"])

    return hit_count / len(question_results)


def calculate_mean_reciprocal_rank(
    question_results: list[RetrievalQuestionResult],
) -> float:
    if not question_results:
        raise ValueError("question_results must not be empty")

    reciprocal_rank_sum = sum(
        result["reciprocal_rank"]
        for result in question_results
    )

    return reciprocal_rank_sum / len(question_results)


def calculate_reciprocal_rank(
    *,
    retrieved_source_ids: list[str],
    expected_source_ids: list[str],
) -> float:
    expected_source_id_set = set(expected_source_ids)

    for index, source_id in enumerate(retrieved_source_ids, start=1):
        if source_id in expected_source_id_set:
            return 1 / index

    return 0.0


def unique_in_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_values: list[str] = []

    for value in values:
        if value in seen:
            continue

        seen.add(value)
        unique_values.append(value)

    return unique_values


def load_and_evaluate_retrieval_questions(
    *,
    questions_path: Path = DEFAULT_RETRIEVAL_QUESTIONS_PATH,
    chunks_path: Path = DEFAULT_CHUNKS_PATH,
    top_k: int = 5,
) -> RetrievalEvaluationResult:
    questions = load_retrieval_questions(questions_path)

    return evaluate_retrieval_questions(
        questions,
        chunks_path=chunks_path,
        top_k=top_k,
    )


def main() -> None:
    result = load_and_evaluate_retrieval_questions()

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()