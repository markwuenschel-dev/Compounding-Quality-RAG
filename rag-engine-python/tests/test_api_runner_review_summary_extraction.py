import json

from app import api_runner


class FakeClient:
    def complete_json(self, prompt: str) -> str:
        return json.dumps(
            {
                "record_review_result": "no_discrepancy_found",
                "lot_batch_pattern_summary": "no_similar_batch_concerns_found",
                "inventory_inspection_result": "no_inventory_available",
                "customer_context_summary": "Dog vomited once and recovered.",
                "api_reference_review_result": "not_needed",
                "missing_information": ["Exact dose administered"],
                "evidence_limitations": [],
                "severe_triggers_observed": [],
            }
        )


def test_bridge_extracts_review_summary(monkeypatch) -> None:
    monkeypatch.setattr(
        api_runner,
        "openai_json_client_from_env",
        lambda: FakeClient(),
    )

    result = api_runner.run_bridge(
        json.dumps(
            {
                "command": "extract_review_summary",
                "payload": {
                    "concernText": "Dog vomited after medication.",
                    "pharmacistNotes": (
                        "Worksheet review found no discrepancy. "
                        "No similar lot concerns. "
                        "No inventory available. "
                        "Dog recovered. No hospitalization."
                    ),
                },
            }
        )
    )

    assert result.exit_code == 0
    response = json.loads(result.stdout)
    assert response["ok"] is True
    assert (
        response["result"]["reviewSummary"]["recordReviewResult"]
        == "no_discrepancy_found"
    )
    assert response["result"]["fieldEvidence"]
