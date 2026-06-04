package com.compoundingquality.reviewapi.rag;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.json.JsonMapper;
import java.nio.file.Path;
import java.time.Duration;
import java.util.List;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;


class PythonProcessRagEngineClientContractTest {

    private final JsonMapper jsonMapper = JsonMapper.builder().build();

    @TempDir
    Path workingDirectory;

    @Test
    void sendsCanonicalChecklistBridgeRequestToExecutor() throws Exception {
        CapturingProcessExecutor executor = new CapturingProcessExecutor(
                new PythonProcessRagEngineClient.ProcessResult(
                        0,
                        validChecklistResponse(),
                        ""
                )
        );

        PythonProcessRagEngineClient client = client(executor);

        RagChecklistResult result = client.createChecklist(
                new RagChecklistRequest("Dog vomited after flavored oral liquid.", 4)
        );

        JsonNode requestJson = jsonMapper.readTree(executor.stdinJson());

        assertThat(requestJson.path("command").asString())
                .isEqualTo("checklist");

        assertThat(requestJson.path("payload").path("concernText").asString())
                .isEqualTo("Dog vomited after flavored oral liquid.");

        assertThat(requestJson.path("payload").path("topK").asInt())
                .isEqualTo(4);

        assertThat(executor.properties().workingDirectory())
                .isEqualTo(workingDirectory);

        assertThat(result.concernType())
                .isEqualTo("flavor_related_vomiting");
    }

    @Test
    void mapsChecklistResultAndPreservesEvidenceOrder() {
        CapturingProcessExecutor executor = new CapturingProcessExecutor(
                new PythonProcessRagEngineClient.ProcessResult(
                        0,
                        validChecklistResponse(),
                        ""
                )
        );

        PythonProcessRagEngineClient client = client(executor);

        RagChecklistResult result = client.createChecklist(
                new RagChecklistRequest("Dog vomited after flavored oral liquid.", 2)
        );

        assertThat(result.requiredChecks())
                .extracting(RagChecklistResult.ChecklistItem::key)
                .containsExactly(
                        "record_review",
                        "trend_scan",
                        "customer_context_follow_up"
                );

        assertThat(result.evidence())
                .extracting(RagChecklistResult.EvidenceCitation::sourceId)
                .containsExactly("SOP-004", "SOP-008");

        assertThat(result.evidence().getFirst().matchedTerms())
                .containsExactly("vomiting", "flavor", "administration");
    }

    @Test
    void throwsConfiguredBridgeErrorWhenPythonReturnsOkFalse() {
        CapturingProcessExecutor executor = new CapturingProcessExecutor(
                new PythonProcessRagEngineClient.ProcessResult(
                        0,
                        """
                        {
                          "ok": false,
                          "error": {
                            "code": "UNSUPPORTED_RECORD_ACCESS",
                            "message": "This public demo cannot inspect real operational records."
                          }
                        }
                        """,
                        ""
                )
        );

        PythonProcessRagEngineClient client = client(executor);

        assertThatThrownBy(() -> client.createChecklist(
                new RagChecklistRequest("Can you inspect the real compounding record?", 5)
        ))
                .isInstanceOf(RagEngineException.class)
                .satisfies(error -> {
                    RagEngineException ragError = (RagEngineException) error;

                    assertThat(ragError.code())
                            .isEqualTo("UNSUPPORTED_RECORD_ACCESS");

                    assertThat(ragError.getMessage())
                            .isEqualTo("This public demo cannot inspect real operational records.");
                });
    }

    @Test
    void classifiesValidJsonWithMissingRequiredMappedFieldAsInvalidResponse() {
        CapturingProcessExecutor executor = new CapturingProcessExecutor(
                new PythonProcessRagEngineClient.ProcessResult(
                        0,
                        """
                        {
                          "ok": true,
                          "result": {
                            "concernType": "flavor_related_vomiting",
                            "riskLane": "unexpected_non_life_threatening",
                            "reviewScope": "full_quality_review",
                            "initialTakeaway": "Vomiting after administration requires review context.",
                            "requiredChecks": [],
                            "missingInformation": [],
                            "escalationTriggersToRuleOut": [],
                            "evidence": [
                              {
                                "chunkId": "SOP-004::palatability-and-flavor-rejection",
                                "sourceId": "SOP-004",
                                "sourceTitle": "Customer Context and Administration Review",
                                "sourceType": "sop",
                                "score": 0.91,
                                "matchedTerms": ["vomiting"],
                                "supportingText": "Vomiting requires customer context."
                              }
                            ],
                            "limitations": []
                          }
                        }
                        """,
                        ""
                )
        );

        PythonProcessRagEngineClient client = client(executor);

        assertThatThrownBy(() -> client.createChecklist(
        new RagChecklistRequest("Dog vomited after administration.", 5)
))
        .isInstanceOf(RagEngineException.class)
        .satisfies(error -> {
            RagEngineException ragError = (RagEngineException) error;

            assertThat(ragError.code())
                    .isEqualTo("ENGINE_RESPONSE_MAPPING");

            assertThat(ragError)
                    .hasRootCauseInstanceOf(IllegalArgumentException.class);

            assertThat(ragError)
                    .hasRootCauseMessage("sectionHeading must not be blank");
        });
    }

    @Test
    void summarizesStderrWhenPythonProcessExitsNonZero() {
        String stderr = "alpha-".repeat(500) + "omega";

        CapturingProcessExecutor executor = new CapturingProcessExecutor(
                new PythonProcessRagEngineClient.ProcessResult(
                        2,
                        "",
                        stderr
                )
        );

        PythonProcessRagEngineClient client = client(executor);

        assertThatThrownBy(() -> client.createChecklist(
                new RagChecklistRequest("Dog vomited after administration.", 5)
        ))
                .isInstanceOf(RagEngineException.class)
                .satisfies(error -> {
                    RagEngineException ragError = (RagEngineException) error;

                    assertThat(ragError.getMessage())
                            .contains("Python RAG engine exited with code 2");

                    assertThat(ragError.getMessage())
                            .contains("alpha-");

                    assertThat(ragError.getMessage())
                            .doesNotContain("omega");

                    assertThat(ragError.getMessage())
                            .endsWith("...");

                    assertThat(ragError.getMessage().length())
                            .isLessThan(2_300);
                });
    }

    @Test
    void classifiesStdoutPollutionAsInvalidStdout() {
        CapturingProcessExecutor executor = new CapturingProcessExecutor(
                new PythonProcessRagEngineClient.ProcessResult(
                        0,
                        """
                        bridge stub received request
                        {"ok": true, "result": {}}
                        """,
                        ""
                )
        );

        PythonProcessRagEngineClient client = client(executor);

        assertThatThrownBy(() -> client.createChecklist(
                new RagChecklistRequest("Dog vomited after administration.", 5)
        ))
                .isInstanceOf(RagEngineException.class)
                .satisfies(error -> {
                    RagEngineException ragError = (RagEngineException) error;

                    assertThat(ragError.code())
                            .isEqualTo("ENGINE_INVALID_STDOUT");
                });
    }

    private PythonProcessRagEngineClient client(CapturingProcessExecutor executor) {
        PythonProcessRagEngineProperties properties = new PythonProcessRagEngineProperties(
                List.of("python", "-m", "app.api_runner"),
                workingDirectory,
                Duration.ofSeconds(10)
        );

        return new PythonProcessRagEngineClient(jsonMapper, properties, executor);
    }

    private static String validChecklistResponse() {
        return """
                {
                  "ok": true,
                  "result": {
                    "concernType": "flavor_related_vomiting",
                    "riskLane": "unexpected_non_life_threatening",
                    "reviewScope": "full_quality_review",
                    "initialTakeaway": "Initial screen suggests flavor-related vomiting with an unexpected non-life-threatening risk lane.",
                    "requiredChecks": [
                      {
                        "key": "record_review",
                        "label": "Record review",
                        "required": true,
                        "reason": "Verify compounding or dispensing record fields relevant to the concern."
                      },
                      {
                        "key": "trend_scan",
                        "label": "Trend scan",
                        "required": true,
                        "reason": "Check for repeated similar concerns when enough fields exist to support trend review."
                      },
                      {
                        "key": "customer_context_follow_up",
                        "label": "Customer clinical context follow-up",
                        "required": true,
                        "reason": "Vomiting after administration requires timing, dose, symptom course, and severity context."
                      }
                    ],
                    "missingInformation": [
                      "Dose administered",
                      "Whether symptoms resolved",
                      "Whether veterinarian was contacted"
                    ],
                    "escalationTriggersToRuleOut": [
                      "pet_death",
                      "pet_hospitalization",
                      "threatened_legal_action"
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
                        "supportingText": "Palatability and flavor concerns require customer context when vomiting occurs after administration."
                      },
                      {
                        "chunkId": "SOP-008::similar-concern-same-medication-and-dosage-form",
                        "sourceId": "SOP-008",
                        "sourceTitle": "Trend and Pattern Monitoring Rules",
                        "sourceType": "sop",
                        "sectionHeading": "Similar Concern Same Medication and Dosage Form",
                        "score": 0.84,
                        "matchedTerms": ["similar", "concern", "dosage"],
                        "supportingText": "Similar concerns should be reviewed when enough medication, dosage form, batch, or lot context is available."
                      }
                    ],
                    "limitations": [
                      "Demo-only bridge response."
                    ]
                  }
                }
                """;
    }

    private static final class CapturingProcessExecutor
            implements PythonProcessRagEngineClient.ProcessExecutor {

        private final PythonProcessRagEngineClient.ProcessResult result;

        private PythonProcessRagEngineProperties properties;
        private String stdinJson;

        private CapturingProcessExecutor(PythonProcessRagEngineClient.ProcessResult result) {
            this.result = result;
        }

        @Override
        public PythonProcessRagEngineClient.ProcessResult execute(
                PythonProcessRagEngineProperties properties,
                String stdinJson
        ) {
            this.properties = properties;
            this.stdinJson = stdinJson;
            return result;
        }

        private PythonProcessRagEngineProperties properties() {
            return properties;
        }

        private String stdinJson() {
            return stdinJson;
        }
    }
}