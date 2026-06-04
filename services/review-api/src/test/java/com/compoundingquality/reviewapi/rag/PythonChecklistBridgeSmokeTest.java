package com.compoundingquality.reviewapi.rag;

import static org.assertj.core.api.Assertions.assertThat;

import com.compoundingquality.reviewapi.config.RagEngineConfiguration;
import tools.jackson.databind.json.JsonMapper;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.runner.ApplicationContextRunner;

class PythonChecklistBridgeSmokeTest {

    @Test
    void callsConfiguredPythonBridgeAndMapsChecklistResult() {
        Path stubPath = Path.of("src/test/resources/python/checklist_bridge_stub.py")
                .toAbsolutePath()
                .normalize();

        Path workingDirectory = stubPath.getParent();

        contextRunner(stubPath, workingDirectory).run(context -> {
            assertThat(context).hasNotFailed();

            RagEngineClient client = context.getBean(RagEngineClient.class);

            RagChecklistResult result = client.createChecklist(
                    new RagChecklistRequest(
                            "My dog vomited once 10 minutes after taking a chicken-flavored compounded oral liquid.",
                            3
                    )
            );

            assertThat(result.concernType())
                    .isEqualTo("flavor_related_vomiting");

            assertThat(result.riskLane())
                    .isEqualTo("unexpected_non_life_threatening");

            assertThat(result.reviewScope())
                    .isEqualTo("full_quality_review");

            assertThat(result.initialTakeaway())
                    .contains("unexpected non-life-threatening");

            assertThat(result.requiredChecks())
                    .extracting(RagChecklistResult.ChecklistItem::key)
                    .containsExactly(
                            "record_review",
                            "trend_scan",
                            "customer_context_follow_up"
                    );

            assertThat(result.missingInformation())
                    .contains(
                            "Dose administered",
                            "Whether symptoms resolved",
                            "Whether veterinarian was contacted"
                    );

            assertThat(result.escalationTriggersToRuleOut())
                    .contains(
                            "pet_death",
                            "pet_hospitalization",
                            "threatened_legal_action"
                    );

            assertThat(result.evidence())
                    .singleElement()
                    .satisfies(citation -> {
                        assertThat(citation.chunkId())
                                .isEqualTo("SOP-004::palatability-and-flavor-rejection");

                        assertThat(citation.sourceId())
                                .isEqualTo("SOP-004");

                        assertThat(citation.sourceTitle())
                                .isEqualTo("Customer Context and Administration Review");

                        assertThat(citation.sourceType())
                                .isEqualTo("sop");

                        assertThat(citation.sectionHeading())
                                .isEqualTo("Palatability and Flavor Rejection");

                        assertThat(citation.score())
                                .isEqualTo(0.91);

                        assertThat(citation.matchedTerms())
                                .contains("vomiting", "flavor");
                    });

            assertThat(result.limitations())
                    .contains("Demo-only bridge response.");
        });
    }

    private ApplicationContextRunner contextRunner(Path stubPath, Path workingDirectory) {
        String pythonExecutable = System.getProperty("python.executable", "python");

        return new ApplicationContextRunner()
                .withBean(JsonMapper.class, () -> JsonMapper.builder().build())
                .withUserConfiguration(RagEngineConfiguration.class)
                .withPropertyValues(
                        "rag.python.command[0]=" + pythonExecutable,
                        "rag.python.command[1]=-u",
                        "rag.python.command[2]=" + stubPath,
                        "rag.python.working-directory=" + workingDirectory,
                        "rag.python.timeout=5s"
                );
    }
}