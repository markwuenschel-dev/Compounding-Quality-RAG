# Demo CLI and API Output

This document shows the current synthetic two-phase workflow through the Python CLI/bridge and the Spring Boot API.

> **Public demo boundary:** This project uses demo-only data. It does **not** access real customer data, patient data, order records, compounding records, inventory systems, customer history, proprietary SOPs, or external drug references.

## Demo Case 1: Flavor-Related Vomiting Concern

### Input Concern

```text
My dog received a chicken-flavored compounded oral liquid. About 10 minutes later he started running around frantically and vomited once. He seems okay now, but I’m worried the medication or flavor caused it.
```

## Phase 1: Intake Checklist

Initial screen suggests `flavor_related_vomiting` with an `unexpected_non_life_threatening` risk lane unless review findings identify a severe escalation trigger or unsupported evidence gap.

### What Should Be Checked

| Check | Required | Purpose |
|---|---:|---|
| Record review | Yes | Verify compounding or dispensing record fields relevant to the concern. |
| Lot or batch context review | Yes | Look for similar concerns tied to the same lot, batch, medication, dosage form, or concern type when available. |
| Inventory inspection if available | Yes | Inspect available inventory when the concern could involve visible product quality, device, equipment, or packaging issues. |
| Trend scan | Yes | Check for repeated similar concerns when enough fields exist to support trend review. |
| Customer clinical context follow-up | Yes | Vomiting after administration requires timing, dose, symptom course, veterinarian contact, and severity context before final routing. |

### Missing Information

- Medication or product placeholder.
- Species.
- Dosage form.
- Lot or batch information, if available.
- Whether any severe escalation trigger is present.
- Dose administered.
- Timing of vomiting relative to administration.
- Whether symptoms resolved.
- Whether veterinarian was contacted.
- Whether the pet was hospitalized.

### Evidence Used

| Source | Section |
|---|---|
| SOP-002 | Flavor or Palatability Guidance |
| SOP-004 | Palatability and Flavor Rejection |
| SOP-008 | Similar Concern Same Medication and Dosage Form |

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
| Severe triggers observed | none |

## Phase 2: Final Review-Support Report

Recommended disposition is `technical_services_customer_outreach` with an `unexpected_non_life_threatening` risk lane.

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

### Escalation Triggers

None identified from supplied structured review findings.

### Resolution Options

- `counseling_or_follow_up`
- `alternate_dosage_form_discussion`

### Rationale

Vomiting after administration is treated as suspected ADE context. Without hospitalization, death, legal threat, contamination, wrong medication, or veterinarian allegation of harm, the supplied findings support follow-up rather than automatic leadership escalation.

## Demo Case 2: Unsupported Internal Record Access

### Input

```text
Can you look at the real compounding record and tell me if this batch had the same vomiting complaints?
```

### Refusal Output

```text
Unsupported in this proof of concept: this project does not access real compounding records, order pages, customer history, patient records, or inventory systems. Use only supplied demo summaries or state what a human reviewer should verify.
```

## Python API Runner Bridge Demos

### Checklist

```powershell
@'
{"command":"checklist","payload":{"concernText":"My dog vomited after taking a flavored compounded oral liquid.","topK":3}}
'@ | python -m app.api_runner
```

### Retrieve

```powershell
@'
{"command":"retrieve","payload":{"queryText":"vomiting after flavored oral liquid","topK":3}}
'@ | python -m app.api_runner
```

Expected shape:

```json
{
  "ok": true,
  "result": {
    "queryText": "vomiting after flavored oral liquid",
    "topK": 3,
    "evidence": [
      {
        "chunkId": "SOP-004::palatability-and-flavor-rejection",
        "sourceId": "SOP-004",
        "sourceTitle": "Customer Context and Administration Review",
        "sourceType": "sop",
        "sectionHeading": "Palatability and Flavor Rejection",
        "score": 0.91,
        "matchedTerms": ["vomiting", "flavor"],
        "supportingText": "..."
      }
    ]
  }
}
```

### Final Assessment

```powershell
@'
{
  "command": "final_assessment",
  "payload": {
    "concernText": "My dog vomited once after taking a chicken-flavored compounded oral liquid and recovered.",
    "topK": 3,
    "reviewSummary": {
      "recordReviewResult": "no_discrepancy_found",
      "lotBatchPatternSummary": "no_similar_batch_concerns_found",
      "inventoryInspectionResult": "no_inventory_available",
      "customerContextSummary": "Dog vomited once and recovered. No hospitalization, death, legal threat, contamination, or wrong medication concern was reported.",
      "apiReferenceReviewResult": "not_needed",
      "missingInformation": ["Exact dose administered"],
      "evidenceLimitations": ["Inventory was not available to inspect."],
      "severeTriggersObserved": []
    }
  }
}
'@ | python -m app.api_runner
```

## Spring Boot API Demos

Start the application from `services/review-api`:

```powershell
.\gradlew bootRun
```

### Health

```powershell
Invoke-RestMethod -Uri "http://localhost:8080/health" -Method Get
```

### Retrieve

```powershell
$retrieveBody = @{
    queryText = "vomiting after flavored oral liquid"
    topK = 3
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://localhost:8080/api/retrieve" `
    -Method Post `
    -ContentType "application/json" `
    -Body $retrieveBody
```

### Final Assessment

```powershell
$finalAssessmentBody = @{
    concernText = "My dog vomited once after taking a chicken-flavored compounded oral liquid and recovered."
    topK = 3
    reviewSummary = @{
        recordReviewResult = "no_discrepancy_found"
        lotBatchPatternSummary = "no_similar_batch_concerns_found"
        inventoryInspectionResult = "no_inventory_available"
        customerContextSummary = "Dog vomited once and recovered. No hospitalization, death, legal threat, contamination, or wrong medication concern was reported."
        apiReferenceReviewResult = "not_needed"
        missingInformation = @("Exact dose administered")
        evidenceLimitations = @("Inventory was not available to inspect.")
        severeTriggersObserved = @()
    }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod `
    -Uri "http://localhost:8080/api/final-assessment" `
    -Method Post `
    -ContentType "application/json" `
    -Body $finalAssessmentBody
```

### Severe Trigger Routing

```powershell
$severeBody = @{
    concernText = "My dog vomited after taking a compounded oral liquid."
    topK = 3
    reviewSummary = @{
        recordReviewResult = "no_discrepancy_found"
        lotBatchPatternSummary = "no_similar_batch_concerns_found"
        inventoryInspectionResult = "no_inventory_available"
        customerContextSummary = "The pet was hospitalized."
        apiReferenceReviewResult = "not_needed"
        missingInformation = @()
        evidenceLimitations = @("Inventory was not available to inspect.")
        severeTriggersObserved = @("pet_hospitalization")
    }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod `
    -Uri "http://localhost:8080/api/final-assessment" `
    -Method Post `
    -ContentType "application/json" `
    -Body $severeBody
```

Expected severe behavior:

```text
riskLane = life_threatening_or_legal
reviewScope = escalation_review
handlingPath = leadership_escalation_before_resolution
```

## Demo Interpretation

This walkthrough shows that the tool can:

1. Turn a realistic synthetic concern into a structured checklist.
2. Retrieve supporting synthetic SOP evidence.
3. Combine concern text and structured reviewer findings into a final review-support assessment.
4. Refuse unsupported real-record or unsupported-evidence requests.

The output supports pharmacist review; it does not replace it.
