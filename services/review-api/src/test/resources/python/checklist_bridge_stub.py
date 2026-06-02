import json
import sys


def main() -> int:
    raw_stdin = sys.stdin.read()

    if not raw_stdin.strip():
        write_error("EMPTY_STDIN", "No JSON request was provided.")
        return 0

    try:
        request = json.loads(raw_stdin)
    except json.JSONDecodeError:
        write_error("INVALID_JSON", "Request stdin was not valid JSON.")
        return 0

    if request.get("command") != "checklist":
        write_error("UNKNOWN_COMMAND", "Only the checklist command is supported by this bridge stub.")
        return 0

    payload = request.get("payload") or {}
    concern_text = payload.get("concernText")
    top_k = payload.get("topK")

    if not concern_text:
        write_error("MISSING_CONCERN_TEXT", "payload.concernText is required.")
        return 0

    if top_k != 3:
        write_error("UNEXPECTED_TOP_K", "This smoke test expects topK to be 3.")
        return 0

    response = {
        "ok": True,
        "result": {
            "concernType": "flavor_related_vomiting",
            "riskLane": "unexpected_non_life_threatening",
            "reviewScope": "full_quality_review",
            "initialTakeaway": (
                "Initial screen suggests flavor-related vomiting with an "
                "unexpected non-life-threatening risk lane unless review findings "
                "identify a severe escalation trigger."
            ),
            "requiredChecks": [
                {
                    "key": "record_review",
                    "label": "Record review",
                    "required": True,
                    "reason": "Verify compounding or dispensing record fields relevant to the concern.",
                },
                {
                    "key": "trend_scan",
                    "label": "Trend scan",
                    "required": True,
                    "reason": "Check for repeated similar concerns when enough fields exist to support trend review.",
                },
                {
                    "key": "customer_context_follow_up",
                    "label": "Customer clinical context follow-up",
                    "required": True,
                    "reason": "Vomiting after administration requires timing, dose, symptom course, and severity context.",
                },
                
            ],
            "missingInformation": [
                "Dose administered",
                "Whether symptoms resolved",
                "Whether veterinarian was contacted",
            ],
            "escalationTriggersToRuleOut": [
                "pet_death",
                "pet_hospitalization",
                "threatened_legal_action",
            ],
            "evidence": [
                {
                    "chunkId": "SOP-004::palatability-and-flavor-rejection",
                    "sourceId": "SOP-004",
                    "sourceTitle": "Customer Context and Administration Review",
                    "sourceType": "sop",
                    "sectionHeading": "Palatability and Flavor Rejection",
                    "score": 0.91,
                    "matchedTerms": ["vomiting", "flavor", "administration"],
                    "supportingText": (
                        "Palatability and flavor concerns require customer context when "
                        "vomiting occurs after administration."
                    ),
                }
            ],
            "limitations": [
                "Demo-only bridge response.",
                "This smoke test does not call the real RAG engine.",
            ],
        },
    }

    json.dump(response, sys.stdout)
    return 0


def write_error(code: str, message: str) -> None:
    json.dump(
        {
            "ok": False,
            "error": {
                "code": code,
                "message": message,
            },
        },
        sys.stdout,
    )


if __name__ == "__main__":
    raise SystemExit(main())