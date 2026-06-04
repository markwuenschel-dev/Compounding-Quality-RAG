package com.compoundingquality.reviewapi.config;

import static org.assertj.core.api.Assertions.assertThat;

import com.compoundingquality.reviewapi.rag.PythonProcessRagEngineClient;
import com.compoundingquality.reviewapi.rag.RagEngineClient;
import java.nio.file.Path;
import java.time.Duration;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.boot.test.context.runner.ApplicationContextRunner;
import tools.jackson.databind.json.JsonMapper;

class RagEngineConfigurationTest {

    @TempDir
    Path ragEngineDirectory;

    @Test
    void createsRagEngineClientBean() {
        contextRunner().run(context -> {
            assertThat(context).hasNotFailed();
            assertThat(context).hasSingleBean(JsonMapper.class);
            assertThat(context).hasSingleBean(RagEngineClient.class);
            assertThat(context.getBean(RagEngineClient.class))
                    .isInstanceOf(PythonProcessRagEngineClient.class);
        });
    }

    @Test
    void bindsPythonLaunchSettings() {
        contextRunner().run(context -> {
            assertThat(context).hasNotFailed();

            var settings = context.getBean(
                    RagEngineConfiguration.PythonRagEngineSettings.class
            );

            assertThat(settings.command())
                    .containsExactly("python", "-m", "app.api_runner");

            assertThat(settings.workingDirectory())
                    .isEqualTo(ragEngineDirectory.toString());

            assertThat(settings.timeout())
                    .isEqualTo(Duration.ofSeconds(10));
        });
    }

    private ApplicationContextRunner contextRunner() {
        return new ApplicationContextRunner()
                .withBean(JsonMapper.class, () -> JsonMapper.builder().build())
                .withUserConfiguration(RagEngineConfiguration.class)
                .withPropertyValues(
                        "rag.python.command[0]=python",
                        "rag.python.command[1]=-m",
                        "rag.python.command[2]=app.api_runner",
                        "rag.python.working-directory=" + ragEngineDirectory,
                        "rag.python.timeout=10s"
                );
    }
}
