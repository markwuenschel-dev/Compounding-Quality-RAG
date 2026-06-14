package com.compoundingquality.reviewapi.rag;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;

import java.nio.file.Path;
import java.time.Duration;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import tools.jackson.databind.json.JsonMapper;

class PythonChecklistBridgeContractTest {

    @TempDir
    Path workingDirectory;

    @Test
    void mapsTheObservedVomitingChecklistResponse() {
        PythonProcessRagEngineClient client = new PythonProcessRagEngineClient(
                JsonMapper.builder().build(),
                new PythonProcessRagEngineProperties(
                        List.of("python", "-m", "app.api_runner"),
                        workingDirectory,
                        Duration.ofSeconds(10)
                ),
                (properties, stdinJson) ->
                        new PythonProcessRagEngineClient.ProcessResult(
                                0,
                                OBSERVED_RESPONSE,
                                ""
                        )
        );

        RagChecklistResult result = client.createChecklist(
                new RagChecklistRequest(
                        "My dog received a chicken-flavored compounded oral liquid. About 10 minutes later he vomited once but seems okay now.",
                        5
                )
        );

        assertEquals("flavor_related_vomiting", result.concernType());
        assertEquals(
                "unexpected_non_life_threatening",
                result.riskLane()
        );
        assertEquals("full_quality_review", result.reviewScope());
        assertEquals(5, result.requiredChecks().size());
        assertEquals(5, result.evidence().size());
        assertFalse(result.initialTakeaway().isBlank());
        assertEquals("SOP-002", result.evidence().get(0).sourceId());
    }

    private static final String OBSERVED_RESPONSE = """
            {
              "ok": true,
              "result": {
                "concernType": "flavor_related_vomiting",
                "riskLane": "unexpected_non_life_threatening",
                "reviewScope": "full_quality_review",
                "initialTakeaway": "Initial screen suggests flavor related vomiting with unexpected non life threatening risk lane. Final routing depends on review findings and confirmed escalation triggers.",
                "requiredChecks": [
                  {
                    "key": "record_review",
                    "label": "Record review",
                    "required": true,
                    "reason": "Verify the synthetic compounding or dispensing record fields relevant to the concern."
                  },
                  {
                    "key": "lot_batch_review",
                    "label": "Lot or batch context review",
                    "required": true,
                    "reason": "Look for similar concerns tied to the same lot, batch, medication, dosage form, or concern type when those fields are available."
                  },
                  {
                    "key": "inventory_inspection",
                    "label": "Inventory inspection if available",
                    "required": true,
                    "reason": "Inspect available inventory when the concern could involve visible product quality, device, equipment, or packaging issues."
                  },
                  {
                    "key": "trend_scan",
                    "label": "Trend scan",
                    "required": true,
                    "reason": "Check for repeated similar concerns when enough synthetic fields exist to support trend review."
                  },
                  {
                    "key": "customer_context_follow_up",
                    "label": "Customer clinical context follow-up",
                    "required": true,
                    "reason": "Vomiting after administration requires timing, dose, symptom course, veterinarian contact, and severity context before final routing."
                  }
                ],
                "missingInformation": [
                  "Medication or product placeholder",
                  "Species",
                  "Dosage form",
                  "Lot or batch information if available",
                  "Whether any severe escalation trigger is present",
                  "Dose administered",
                  "Timing of vomiting relative to administration",
                  "Whether symptoms resolved",
                  "Whether veterinarian was contacted",
                  "Whether the pet was hospitalized"
                ],
                "escalationTriggersToRuleOut": [
                  "pet_death",
                  "pet_hospitalization",
                  "threatened_legal_action",
                  "veterinarian_alleges_harm_from_compound",
                  "possible_contamination",
                  "wrong_patient_or_wrong_medication"
                ],
                "evidence": [
                  {
                    "chunkId": "SOP-002::oral-liquid-shortage",
                    "sourceId": "SOP-002",
                    "sourceTitle": "Frontline Guidance, Delegate-Back, and Response Rules",
                    "sourceType": "sop",
                    "sectionHeading": "Oral Liquid Shortage",
                    "score": 8.0,
                    "matchedTerms": ["liquid", "oral"],
                    "supportingText": "Oral Liquid Shortage guidance."
                  },
                  {
                    "chunkId": "SOP-004::oral-liquid-shortage-context",
                    "sourceId": "SOP-004",
                    "sourceTitle": "Customer Context and Administration Review",
                    "sourceType": "sop",
                    "sectionHeading": "Oral Liquid Shortage Context",
                    "score": 8.0,
                    "matchedTerms": ["liquid", "oral"],
                    "supportingText": "Oral liquid shortage context."
                  },
                  {
                    "chunkId": "SOP-004::administration-technique",
                    "sourceId": "SOP-004",
                    "sourceTitle": "Customer Context and Administration Review",
                    "sourceType": "sop",
                    "sectionHeading": "Administration Technique",
                    "score": 2.0,
                    "matchedTerms": ["liquid", "oral"],
                    "supportingText": "Administration technique guidance."
                  },
                  {
                    "chunkId": "SOP-001::review-scope",
                    "sourceId": "SOP-001",
                    "sourceTitle": "Intake Classification and Risk Lane Assignment",
                    "sourceType": "sop",
                    "sectionHeading": "Review Scope",
                    "score": 1.0,
                    "matchedTerms": ["but"],
                    "supportingText": "Review scope guidance."
                  },
                  {
                    "chunkId": "SOP-002::bud-clarification",
                    "sourceId": "SOP-002",
                    "sourceTitle": "Frontline Guidance, Delegate-Back, and Response Rules",
                    "sourceType": "sop",
                    "sectionHeading": "BUD Clarification",
                    "score": 1.0,
                    "matchedTerms": ["about"],
                    "supportingText": "BUD clarification guidance."
                  }
                ],
                "limitations": [
                  "This synthetic assistant does not access real compounding records, inventory, customer history, or external drug references.",
                  "Phase 1 output is a review checklist, not a final clinical or legal conclusion.",
                  "Causality should not be inferred from the intake narrative alone."
                ]
              }
            }
            """;
}
