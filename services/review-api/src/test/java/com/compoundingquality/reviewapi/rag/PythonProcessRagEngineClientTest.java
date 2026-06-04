package com.compoundingquality.reviewapi.rag;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.nio.file.Path;
import java.time.Duration;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.json.JsonMapper;

class PythonProcessRagEngineClientTest {

    private final JsonMapper jsonMapper = JsonMapper.builder().build();

    @TempDir
    Path workingDirectory;

    @Test
    void createChecklistSendsBridgeRequestAndMapsSuccessfulResponse() throws Exception {
        FakeProcessExecutor processExecutor = new FakeProcessExecutor(
                new PythonProcessRagEngineClient.ProcessResult(
                        0,
                        successfulBridgeResponse(),
                        ""
                )
        );

        PythonProcessRagEngineClient client = newClient(processExecutor);

        RagChecklistResult result = client.createChecklist(
                new RagChecklistRequest("My dog vomited after a flavored oral liquid.", 3)
        );

        JsonNode requestJson = jsonMapper.readTree(processExecutor.stdinJson());

        assertEquals("checklist", requestJson.path("command").asString());
        assertEquals(
                "My dog vomited after a flavored oral liquid.",
                requestJson.path("payload").path("concernText").asString()
        );
        assertEquals(3, requestJson.path("payload").path("topK").asInt());

        assertEquals("flavor_related_vomiting", result.concernType());
        assertEquals("unexpected_non_life_threatening", result.riskLane());
        assertEquals("full_quality_review", result.reviewScope());
        assertFalse(result.initialTakeaway().isBlank());

        assertEquals(1, result.requiredChecks().size());
        assertEquals("record_review", result.requiredChecks().get(0).key());
        assertEquals("Record review", result.requiredChecks().get(0).label());

        assertEquals(List.of("Dose administered"), result.missingInformation());
        assertEquals(List.of("pet_hospitalization"), result.escalationTriggersToRuleOut());

        assertEquals(1, result.evidence().size());
        assertEquals("SOP-001", result.evidence().get(0).sourceId());
        assertEquals(List.of("vomit"), result.evidence().get(0).matchedTerms());

        assertEquals(List.of("Checklist output is preliminary."), result.limitations());
    }

    @Test
    void createChecklistTurnsHandledBridgeErrorIntoRagEngineException() {
        FakeProcessExecutor processExecutor = new FakeProcessExecutor(
                new PythonProcessRagEngineClient.ProcessResult(
                        0,
                        """
                        {
                          "ok": false,
                          "error": {
                            "code": "REFUSED",
                            "message": "This request requires unavailable records."
                          }
                        }
                        """,
                        ""
                )
        );

        PythonProcessRagEngineClient client = newClient(processExecutor);

        RagEngineException exception = assertThrows(
                RagEngineException.class,
                () -> client.createChecklist(
                        new RagChecklistRequest("Check the real batch record.", 5)
                )
        );

        assertEquals("REFUSED", exception.code());
    }

    @Test
    void createChecklistRejectsNonzeroProcessExit() {
        FakeProcessExecutor processExecutor = new FakeProcessExecutor(
                new PythonProcessRagEngineClient.ProcessResult(
                        1,
                        """
                        {
                          "ok": false,
                          "error": {
                            "code": "ENGINE_FAILURE",
                            "message": "Engine failed."
                          }
                        }
                        """,
                        "Traceback: boom"
                )
        );

        PythonProcessRagEngineClient client = newClient(processExecutor);

        RagEngineException exception = assertThrows(
                RagEngineException.class,
                () -> client.createChecklist(new RagChecklistRequest("My dog vomited once.", 5))
        );

        assertEquals("ENGINE_PROCESS_EXIT", exception.code());
    }

    @Test
    void createChecklistRejectsInvalidStdout() {
        FakeProcessExecutor processExecutor = new FakeProcessExecutor(
                new PythonProcessRagEngineClient.ProcessResult(0, "not-json", "")
        );

        PythonProcessRagEngineClient client = newClient(processExecutor);

        RagEngineException exception = assertThrows(
                RagEngineException.class,
                () -> client.createChecklist(new RagChecklistRequest("My dog vomited once.", 5))
        );

        assertEquals("ENGINE_INVALID_STDOUT", exception.code());
    }

    @Test
    void createChecklistRejectsEmptyStdout() {
        FakeProcessExecutor processExecutor = new FakeProcessExecutor(
                new PythonProcessRagEngineClient.ProcessResult(0, "", "")
        );

        PythonProcessRagEngineClient client = newClient(processExecutor);

        RagEngineException exception = assertThrows(
                RagEngineException.class,
                () -> client.createChecklist(new RagChecklistRequest("My dog vomited once.", 5))
        );

        assertEquals("ENGINE_INVALID_STDOUT", exception.code());
    }

    @Test
    void createChecklistRejectsOkResponseWithoutResult() {
        FakeProcessExecutor processExecutor = new FakeProcessExecutor(
                new PythonProcessRagEngineClient.ProcessResult(
                        0,
                        """
                        {
                          "ok": true
                        }
                        """,
                        ""
                )
        );

        PythonProcessRagEngineClient client = newClient(processExecutor);

        RagEngineException exception = assertThrows(
                RagEngineException.class,
                () -> client.createChecklist(new RagChecklistRequest("My dog vomited once.", 5))
        );

        assertEquals("ENGINE_INVALID_RESPONSE", exception.code());
    }

    @Test
    void createChecklistRejectsMalformedResultContract() {
        FakeProcessExecutor processExecutor = new FakeProcessExecutor(
                new PythonProcessRagEngineClient.ProcessResult(
                        0,
                        """
                        {
                          "ok": true,
                          "result": {
                            "concernType": "",
                            "riskLane": "unexpected_non_life_threatening",
                            "reviewScope": "full_quality_review",
                            "initialTakeaway": "Initial screen suggests review is needed."
                          }
                        }
                        """,
                        ""
                )
        );

        PythonProcessRagEngineClient client = newClient(processExecutor);

        RagEngineException exception = assertThrows(
                RagEngineException.class,
                () -> client.createChecklist(new RagChecklistRequest("My dog vomited once.", 5))
        );

        assertEquals("ENGINE_RESPONSE_MAPPING", exception.code());
    }

    @Test
    void propertiesRejectInvalidProcessConfiguration() {
        assertThrows(
                IllegalArgumentException.class,
                () -> new PythonProcessRagEngineProperties(
                        List.of(),
                        workingDirectory,
                        Duration.ofSeconds(1)
                )
        );

        assertThrows(
                IllegalArgumentException.class,
                () -> new PythonProcessRagEngineProperties(
                        List.of("python", ""),
                        workingDirectory,
                        Duration.ofSeconds(1)
                )
        );

        assertThrows(
                IllegalArgumentException.class,
                () -> new PythonProcessRagEngineProperties(
                        List.of("python"),
                        workingDirectory.resolve("missing"),
                        Duration.ofSeconds(1)
                )
        );

        assertThrows(
                IllegalArgumentException.class,
                () -> new PythonProcessRagEngineProperties(
                        List.of("python"),
                        workingDirectory,
                        Duration.ZERO
                )
        );
    }

    private static String successfulBridgeResponse() {
        return """
                {
                  "ok": true,
                  "result": {
                    "concernType": "flavor_related_vomiting",
                    "riskLane": "unexpected_non_life_threatening",
                    "reviewScope": "full_quality_review",
                    "initialTakeaway": "Initial screen suggests review is needed.",
                    "requiredChecks": [
                      {
                        "key": "record_review",
                        "label": "Record review",
                        "required": true,
                        "reason": "Verify relevant fields before final disposition."
                      }
                    ],
                    "missingInformation": [
                      "Dose administered"
                    ],
                    "escalationTriggersToRuleOut": [
                      "pet_hospitalization"
                    ],
                    "evidence": [
                      {
                        "chunkId": "SOP-001::sample-section",
                        "sourceId": "SOP-001",
                        "sourceTitle": "Sample SOP",
                        "sourceType": "sop",
                        "sectionHeading": "Sample Section",
                        "score": 7.5,
                        "matchedTerms": [
                          "vomit"
                        ],
                        "supportingText": "Sample supporting text."
                      }
                    ],
                    "limitations": [
                      "Checklist output is preliminary."
                    ]
                  }
                }
                """;
    }

    private static final class FakeProcessExecutor
            implements PythonProcessRagEngineClient.ProcessExecutor {

        private final PythonProcessRagEngineClient.ProcessResult processResult;
        private String stdinJson;

        private FakeProcessExecutor(PythonProcessRagEngineClient.ProcessResult processResult) {
            this.processResult = processResult;
        }

        @Override
        public PythonProcessRagEngineClient.ProcessResult execute(
                PythonProcessRagEngineProperties properties,
                String stdinJson
        ) {
            this.stdinJson = stdinJson;
            return processResult;
        }

        private String stdinJson() {
            return stdinJson;
        }
    }

    private PythonProcessRagEngineClient newClient(
            PythonProcessRagEngineClient.ProcessExecutor executor
    ) {
        PythonProcessRagEngineProperties properties = new PythonProcessRagEngineProperties(
                List.of("python", "-m", "app.api_runner"),
                workingDirectory,
                Duration.ofSeconds(10)
        );

        return new PythonProcessRagEngineClient(
                jsonMapper,
                properties,
                executor
        );
    }
}
