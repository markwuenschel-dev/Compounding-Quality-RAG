from __future__ import annotations

import json

import app.api_runner as api_runner
from app.api_runner import EXIT_SUCCESS, EXIT_UNEXPECTED_FAILURE, run_bridge
from app.checklist_models import EvidenceCitation, ChecklistItem, IntakeChecklist
from app.schemas import ConcernType, EscalationTrigger, RiskLane


def test_checklist_command_returns_successful_bridge_response(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_build_intake_checklist(
        concern_text: str,
        *,
        top_k: int,
    ) -> IntakeChecklist:
        captured["concern_text"] = concern_text
        captured["top_k"] = top_k
        return sample_checklist(concern_text)

    monkeypatch.setattr(
        api_runner,
        "build_intake_checklist",
        fake_build_intake_checklist,
    )

    request = {
        "command": "checklist",
        "payload": {
            "concernText": "My dog vomited after taking a flavored compounded oral liquid.",
            "topK": 3,
        },
    }

    result = run_bridge(json.dumps(request))
    response = json.loads(result.stdout)

    assert result.exit_code == EXIT_SUCCESS
    assert result.stderr == ""
    assert captured == {
        "concern_text": "My dog vomited after taking a flavored compounded oral liquid.",
        "top_k": 3,
    }
    assert response["ok"] is True
    assert response["result"]["concernType"] == "flavor_related_vomiting"
    assert response["result"]["riskLane"] == "unexpected_non_life_threatening"
    assert response["result"]["reviewScope"] == "full_quality_review"
    assert response["result"]["initialTakeaway"]
    assert response["result"]["requiredChecks"] == [
        {
            "key": "record_review",
            "label": "Record review",
            "required": True,
            "reason": "Verify relevant fields before final disposition.",
        }
    ]
    assert response["result"]["missingInformation"] == ["Dose administered"]
    assert response["result"]["escalationTriggersToRuleOut"] == ["pet_hospitalization"]
    assert response["result"]["evidence"][0]["chunkId"] == "SOP-001::section"
    assert response["result"]["evidence"][0]["sourceId"] == "SOP-001"
    assert response["result"]["evidence"][0]["matchedTerms"] == ["vomit"]
    assert response["result"]["limitations"] == ["Checklist output is preliminary."]


def test_refused_request_returns_handled_bridge_error() -> None:
    request = {
        "command": "checklist",
        "payload": {
            "concernText": "Can you check the real compounding record for this batch?"
        },
    }

    result = run_bridge(json.dumps(request))
    response = json.loads(result.stdout)

    assert result.exit_code == EXIT_SUCCESS
    assert result.stderr == ""
    assert response["ok"] is False
    assert response["error"]["code"] == "REFUSED"
    assert response["error"]["message"]
    assert response["error"]["details"]["reason"] == "internal_record_access"
    assert "real compounding record" in response["error"]["details"]["matchedTerms"]


def test_blank_concern_text_returns_handled_error() -> None:
    request = {
        "command": "checklist",
        "payload": {
            "concernText": "   "
        },
    }

    result = run_bridge(json.dumps(request))
    response = json.loads(result.stdout)

    assert result.exit_code == EXIT_SUCCESS
    assert result.stderr == ""
    assert response == {
        "ok": False,
        "error": {
            "code": "INVALID_REQUEST",
            "message": "payload.concernText must not be blank",
        },
    }


def test_missing_concern_text_returns_handled_error() -> None:
    request = {
        "command": "checklist",
        "payload": {},
    }

    result = run_bridge(json.dumps(request))
    response = json.loads(result.stdout)

    assert result.exit_code == EXIT_SUCCESS
    assert result.stderr == ""
    assert response == {
        "ok": False,
        "error": {
            "code": "INVALID_REQUEST",
            "message": "payload.concernText must be a string",
        },
    }


def test_invalid_top_k_returns_handled_error() -> None:
    request = {
        "command": "checklist",
        "payload": {
            "concernText": "My dog vomited once.",
            "topK": 0,
        },
    }

    result = run_bridge(json.dumps(request))
    response = json.loads(result.stdout)

    assert result.exit_code == EXIT_SUCCESS
    assert result.stderr == ""
    assert response == {
        "ok": False,
        "error": {
            "code": "INVALID_REQUEST",
            "message": "payload.topK must be at least 1",
        },
    }


def test_unknown_command_returns_handled_error() -> None:
    request = {
        "command": "not_a_real_command",
        "payload": {},
    }

    result = run_bridge(json.dumps(request))
    response = json.loads(result.stdout)

    assert result.exit_code == EXIT_SUCCESS
    assert result.stderr == ""
    assert response == {
        "ok": False,
        "error": {
            "code": "UNKNOWN_COMMAND",
            "message": "Unsupported command: not_a_real_command",
        },
    }


def test_invalid_json_returns_handled_error() -> None:
    result = run_bridge("{not valid json")
    response = json.loads(result.stdout)

    assert result.exit_code == EXIT_SUCCESS
    assert result.stderr == ""
    assert response["ok"] is False
    assert response["error"]["code"] == "INVALID_JSON"
    assert "Invalid JSON" in response["error"]["message"]


def test_empty_stdin_returns_handled_error() -> None:
    result = run_bridge("")
    response = json.loads(result.stdout)

    assert result.exit_code == EXIT_SUCCESS
    assert result.stderr == ""
    assert response == {
        "ok": False,
        "error": {
            "code": "INVALID_JSON",
            "message": "stdin must contain a JSON request object",
        },
    }


def test_unexpected_exception_returns_json_and_nonzero_exit_code(monkeypatch) -> None:
    def broken_build_intake_checklist(
        concern_text: str,
        *,
        top_k: int,
    ) -> IntakeChecklist:
        raise RuntimeError("boom")

    monkeypatch.setattr(
        api_runner,
        "build_intake_checklist",
        broken_build_intake_checklist,
    )

    request = {
        "command": "checklist",
        "payload": {
            "concernText": "My dog vomited after taking a flavored compounded oral liquid."
        },
    }

    result = run_bridge(json.dumps(request))
    response = json.loads(result.stdout)

    assert result.exit_code == EXIT_UNEXPECTED_FAILURE
    assert response == {
        "ok": False,
        "error": {
            "code": "ENGINE_FAILURE",
            "message": "RAG engine failed while processing the request.",
        },
    }
    assert "RuntimeError: boom" in result.stderr


def sample_checklist(concern_text: str) -> IntakeChecklist:
    citation = EvidenceCitation(
        chunk_id="SOP-001::section",
        source_id="SOP-001",
        source_title="Sample SOP",
        source_type="sop",
        section_heading="Sample Section",
        score=7.5,
        matched_terms=["vomit"],
        supporting_text="Sample supporting text.",
    )

    return IntakeChecklist(
        concern_text=concern_text,
        likely_concern_type=ConcernType.FLAVOR_RELATED_VOMITING,
        likely_risk_lane=RiskLane.UNEXPECTED_NON_LIFE_THREATENING,
        review_checks=[
            ChecklistItem(
                check_name="Record review",
                required=True,
                rationale="Verify relevant fields before final disposition.",
                evidence=[citation],
            )
        ],
        missing_information=["Dose administered"],
        escalation_triggers_to_rule_out=[
            EscalationTrigger.PET_HOSPITALIZATION,
        ],
        evidence=[citation],
        limitations=["Checklist output is preliminary."],
    )