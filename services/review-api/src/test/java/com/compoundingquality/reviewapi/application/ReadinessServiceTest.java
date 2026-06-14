package com.compoundingquality.reviewapi.application;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import com.compoundingquality.reviewapi.dto.ReadinessResponse;
import com.compoundingquality.reviewapi.dto.ReadinessResponse.ReadinessCheck;
import com.compoundingquality.reviewapi.rag.PythonProcessRagEngineProperties;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class ReadinessServiceTest {

    @TempDir
    Path tempDirectory;

    @Test
    void returnsReadyWhenAllDependenciesAreAvailable() throws Exception {
        Path corpusDirectory = tempDirectory.resolve("data/corpus");
        Files.createDirectories(corpusDirectory);
        Files.writeString(corpusDirectory.resolve("sop.md"), "# Synthetic SOP");

        PythonProcessRagEngineProperties properties = mockProperties(tempDirectory);
        PythonCommandProbe commandProbe = (
                command,
                workingDirectory,
                timeout
        ) -> ReadinessCheck.up("pythonCommand", "Python 3.x");

        ReadinessResponse response =
                new ReadinessService(properties, commandProbe).checkReadiness();

        assertThat(response.status()).isEqualTo(ReadinessResponse.READY);
        assertThat(response.checks())
                .allMatch(ReadinessCheck::available);
    }

    @Test
    void returnsNotReadyWhenWorkingDirectoryIsMissing() {
        Path missingDirectory = tempDirectory.resolve("missing");
        PythonProcessRagEngineProperties properties =
                mockProperties(missingDirectory);
        PythonCommandProbe commandProbe = mock(PythonCommandProbe.class);

        ReadinessResponse response =
                new ReadinessService(properties, commandProbe).checkReadiness();

        assertThat(response.status()).isEqualTo(ReadinessResponse.NOT_READY);
        assertThat(check(response, "workingDirectory").status())
                .isEqualTo(ReadinessCheck.DOWN);
        assertThat(check(response, "pythonCommand").status())
                .isEqualTo(ReadinessCheck.DOWN);
        assertThat(check(response, "corpus").status())
                .isEqualTo(ReadinessCheck.DOWN);
    }

    @Test
    void returnsNotReadyWhenCorpusContainsNoSupportedFiles() throws Exception {
        Files.createDirectories(tempDirectory.resolve("data/corpus"));

        PythonProcessRagEngineProperties properties = mockProperties(tempDirectory);
        PythonCommandProbe commandProbe = (
                command,
                workingDirectory,
                timeout
        ) -> ReadinessCheck.up("pythonCommand", "Python 3.x");

        ReadinessResponse response =
                new ReadinessService(properties, commandProbe).checkReadiness();

        assertThat(response.status()).isEqualTo(ReadinessResponse.NOT_READY);
        assertThat(check(response, "corpus").detail())
                .contains("no supported source files");
    }

    @Test
    void returnsNotReadyWhenPythonCommandIsUnavailable() throws Exception {
        Path corpusDirectory = tempDirectory.resolve("data/corpus");
        Files.createDirectories(corpusDirectory);
        Files.writeString(corpusDirectory.resolve("sop.md"), "# Synthetic SOP");

        PythonProcessRagEngineProperties properties = mockProperties(tempDirectory);
        PythonCommandProbe commandProbe = (
                command,
                workingDirectory,
                timeout
        ) -> ReadinessCheck.down(
                "pythonCommand",
                "The configured Python command could not be started."
        );

        ReadinessResponse response =
                new ReadinessService(properties, commandProbe).checkReadiness();

        assertThat(response.status()).isEqualTo(ReadinessResponse.NOT_READY);
        assertThat(check(response, "pythonCommand").status())
                .isEqualTo(ReadinessCheck.DOWN);
    }

    private static PythonProcessRagEngineProperties mockProperties(
            Path workingDirectory
    ) {
        PythonProcessRagEngineProperties properties =
                mock(PythonProcessRagEngineProperties.class);

        when(properties.command()).thenReturn(List.of("python"));
        when(properties.workingDirectory()).thenReturn(workingDirectory);
        when(properties.timeout()).thenReturn(Duration.ofSeconds(30));

        return properties;
    }

    private static ReadinessCheck check(
            ReadinessResponse response,
            String name
    ) {
        return response.checks()
                .stream()
                .filter(check -> check.name().equals(name))
                .findFirst()
                .orElseThrow();
    }
}
