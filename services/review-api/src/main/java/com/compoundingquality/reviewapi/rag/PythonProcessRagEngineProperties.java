package com.compoundingquality.reviewapi.rag;

import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.List;
import java.util.Objects;

public record PythonProcessRagEngineProperties(
        List<String> command,
        Path workingDirectory,
        Duration timeout
) {
    public static final Duration DEFAULT_TIMEOUT = Duration.ofSeconds(10);

    public PythonProcessRagEngineProperties {
        command = List.copyOf(Objects.requireNonNull(command, "command must not be null"));

        if (command.isEmpty()) {
            throw new IllegalArgumentException("command must not be empty");
        }

        if (command.stream().anyMatch(PythonProcessRagEngineProperties::isBlank)) {
            throw new IllegalArgumentException("command must not contain blank values");
        }

        workingDirectory = Objects.requireNonNull(workingDirectory, "working directory must not be null").toAbsolutePath().normalize();

        if(!Files.isDirectory(workingDirectory)) {
            throw new IllegalArgumentException("workingDirectory must be an existing directory");
        }

        timeout = Objects.requireNonNull(timeout, "timeout must not be null");

        if (timeout.isZero() || timeout.isNegative()) {
            throw new IllegalArgumentException("timeout must be positive");
        }
    }


    public static PythonProcessRagEngineProperties localDefault(Path ragEngineDirectory) {
        return new PythonProcessRagEngineProperties(List.of("python", "-m", "app.api_runner"),
            ragEngineDirectory,
            DEFAULT_TIMEOUT
        );
    }

    public static boolean isBlank(String value) {
        return value == null || value.isBlank();
    }
}