# Demo CLI Output

This document shows the current two-phase command-line workflow for the Compounding Quality RAG proof of concept.

> **Public demo boundary:** This project uses demo-only data. It does **not** access real customer data, patient data, order records, compounding records, inventory systems, customer history, proprietary SOPs, or external drug references.

---

## Demo Case 1: Flavor-Related Vomiting Concern

### Input Concern

```text
My dog received a chicken-flavored compounded oral liquid. About 10 minutes later he started running around frantically and vomited once. He seems okay now, but I’m worried the medication or flavor caused it.
```

---

## Phase 1: Intake Checklist

### Initial Review Takeaway

Initial screen suggests **flavor-related vomiting** with an **unexpected non-life-threatening** risk lane unless review findings identify a severe escalation trigger or unsupported evidence gap.

| Field | Output |
|---|---|
| Likely concern type | `flavor_related_vomiting` |
| Likely risk lane | `unexpected_non_life_threatening` |

### What Should Be Checked

| Check | Required | Purpose |
|---|---:|---|
| Record review | Yes | Verify the compounding or dispensing record fields relevant to the concern. |
| Lot or batch context review | Yes | Look for similar concerns tied to the same lot, batch, medication, dosage form, or concern type when available. |
| Inventory inspection if available | Yes | Inspect available inventory when the concern could involve visible product quality, device, equipment, or packaging issues. |
| Trend scan | Yes | Check for repeated similar concerns when enough fields exist to support trend review. |
| Customer clinical context follow-up | Yes | Vomiting after administration requires timing, dose, symptom course, veterinarian contact, and severity context before final routing. |

### Missing Information to Resolve Before Final Disposition

- Medication or product placeholder
- Species
- Dosage form
- Lot or batch information, if available
- Whether any severe escalation trigger is present
- Dose administered
- Timing of vomiting relative to administration
- Whether symptoms resolved
- Whether veterinarian was contacted
- Whether the pet was hospitalized

### Severe Escalation Triggers to Rule Out

- `pet_death`
- `pet_hospitalization`
- `threatened_legal_action`
- `veterinarian_alleges_harm_from_compound`
- `possible_contamination`
- `wrong_patient_or_wrong_medication`

### Evidence Used for Checklist

| Source | Section |
|---|---|
| SOP-002 — Frontline Guidance, Delegate-Back, and Response Rules | Oral Liquid Shortage |
| SOP-004 — Customer Context and Administration Review | Oral Liquid Shortage Context |
| SOP-002 — Frontline Guidance, Delegate-Back, and Response Rules | Flavor or Palatability Guidance |
| SOP-004 — Customer Context and Administration Review | Palatability and Flavor Rejection |
| SOP-008 — Trend and Pattern Monitoring Rules | Similar Concern Same Medication and Dosage Form |

### Phase 1 Limitations

- This proof of concept does not access real compounding records, inventory, customer history, or external drug references.
- Phase 1 output is a review checklist, not a final clinical or legal conclusion.
- Causality should not be inferred from the intake narrative alone.

---

## Reviewer Findings Entered for Phase 2

| Review Field | Entered Finding |
|---|---|
| Record review result | `no_discrepancy_found` |
| Lot/batch pattern summary | `no_similar_batch_concerns_found` |
| Inventory inspection result | `no_inventory_available` |
| API/reference review result | `not_needed` |
| Customer context summary | Dog vomited once about 10 minutes after administration and recovered. No hospitalization, no death, no legal threat, no contamination concern, no wrong medication concern, and veterinarian was not contacted. |
| Missing information | Exact dose administered by customer. |
| Evidence limitation | Inventory was not available to inspect. |

---

## Phase 2: Final Review-Support Report

### Final Review Takeaway

Recommended disposition is **Technical Services customer outreach** with an **unexpected non-life-threatening** risk lane based on the supplied review findings.

### Recommended Review Disposition

| Field | Output |
|---|---|
| Classification | `qre` |
| Category | `suspected_ade` |
| Subcategory | `flavor_related_ade` |
| Concern type | `flavor_related_vomiting` |
| Risk lane | `unexpected_non_life_threatening` |
| Review scope | `full_quality_review` |
| Handling path | `technical_services_customer_outreach` |
| Resolution review required | `true` |

### What Was Checked

- Record review result: `no_discrepancy_found`
- Lot/batch pattern summary: `no_similar_batch_concerns_found`
- Inventory inspection result: `no_inventory_available`
- API/reference review result: `not_needed`

### What Was Not Available / Still Limited

- Exact dose administered by customer.
- Inventory was not available to inspect.

### Escalation Triggers

None identified from the supplied review findings.

### Resolution Options

- `counseling_or_follow_up`
- `alternate_dosage_form_discussion`

### Rationale

Vomiting after administration is treated as a suspected adverse event. Without hospitalization, death, legal threat, contamination, wrong medication, or veterinarian allegation of harm, it supports follow-up rather than automatic leadership escalation.

### Evidence Used

| Source | Section |
|---|---|
| SOP-002 — Frontline Guidance, Delegate-Back, and Response Rules | Oral Liquid Shortage |
| SOP-004 — Customer Context and Administration Review | Oral Liquid Shortage Context |
| SOP-002 — Frontline Guidance, Delegate-Back, and Response Rules | Flavor or Palatability Guidance |
| SOP-004 — Customer Context and Administration Review | Palatability and Flavor Rejection |
| SOP-008 — Trend and Pattern Monitoring Rules | Similar Concern Same Medication and Dosage Form |

### Final Limitations

- This is a public proof of concept, not production policy.
- The tool does not access real records, inventory, customer history, or external drug references.
- Human pharmacist review remains the final decision point.

---

## Demo Case 2: Unsupported Internal Record Access

### Input Question

```text
Can you look at the real compounding record and tell me if this batch had the same vomiting complaints?
```

### Refusal Output

```text
Unsupported in this proof of concept: this project does not access real compounding records, order pages, customer history, patient records, or inventory systems. Use only supplied demo summaries or state what a human reviewer should verify.
```

### Why This Refuses

This question asks the tool to access real operational records and determine whether a real batch had similar complaints. The public demo does not have that access, so the correct behavior is to refuse the record-access request rather than imply that records were checked.

---

## Demo Interpretation

This walkthrough shows two key behaviors:

1. The tool can turn a realistic concern into a structured review checklist and final review-support summary.
2. The tool refuses requests that require real record access or unsupported evidence.

The output is intended to support pharmacist review, not replace it.


---

## API Runner Bridge Smoke Test

The same checklist behavior can also be exercised through the legacy `api_runner` stdin/stdout runner. Spring Boot itself now calls the engine over HTTP (`server.py`); this runner is retained for local/CLI use.

### Input

```powershell
@'
{"command":"checklist","payload":{"concernText":"My dog vomited after taking a flavored compounded oral liquid."}}
'@ | python -m app.api_runner
```

### Expected Response Shape

```json
{
  "ok": true,
  "result": {
    "concernType": "flavor_related_vomiting",
    "riskLane": "unexpected_non_life_threatening",
    "reviewScope": "full_quality_review",
    "initialTakeaway": "...",
    "requiredChecks": [],
    "missingInformation": [],
    "escalationTriggersToRuleOut": [],
    "evidence": [],
    "limitations": []
  }
}
```

### Handled Error Example

```powershell
@'
{"command":"checklist","payload":{"concernText":"   "}}
'@ | python -m app.api_runner
```

```json
{
  "ok": false,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "payload.concernText must not be blank"
  }
}
```

The bridge contract keeps stdout reserved for JSON so a Java process client can parse it safely. Diagnostics and tracebacks belong on stderr.

---

## Spring API Error Contract Smoke Tests

The Spring Boot API shell now has centralized JSON error handling through `GlobalExceptionHandler` and `ApiErrorResponse`.

### Invalid Request Body Validation

Targeted test:

```powershell
./gradlew test --tests "*GlobalExceptionHandlerTest.returnsValidationErrorShapeForInvalidRequestBody"
```

Expected response shape:

```json
{
  "timestamp": "...",
  "status": 400,
  "error": "Bad Request",
  "message": "Validation failed",
  "path": "/test/validate",
  "requestId": "...",
  "fieldErrors": [
    {
      "field": "concernText",
      "rejectedValue": "",
      "message": "concernText is required"
    }
  ]
}
```

### Generic Fallback Error

For an unexpected controller exception, the API returns a generic 500 response instead of leaking the internal exception message.

```json
{
  "timestamp": "...",
  "status": 500,
  "error": "Internal Server Error",
  "message": "Unexpected server error",
  "path": "/test/error",
  "requestId": "...",
  "fieldErrors": []
}
```

### Current Verification

```powershell
./gradlew clean test
```

passes from `services/review-api`.
