package com.compoundingquality.reviewapi.application;

import com.compoundingquality.reviewapi.dto.ReadinessResponse.ReadinessCheck;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Duration;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.springframework.stereotype.Component;

@Component
public class DefaultPythonCommandProbe implements PythonCommandProbe {

    private static final String CHECK_NAME = "pythonCommand";

    @Override
    public ReadinessCheck probe(
            List<String> configuredCommand,
            Path workingDirectory,
            Duration timeout
    ) {
        if (configuredCommand == null || configuredCommand.isEmpty()) {
            return ReadinessCheck.down(
                    CHECK_NAME,
                    "No Python command is configured."
            );
        }

        String executable = configuredCommand.get(0);

        if (executable == null || executable.isBlank()) {
            return ReadinessCheck.down(
                    CHECK_NAME,
                    "The configured Python executable is blank."
            );
        }

        ProcessBuilder processBuilder = new ProcessBuilder(
                executable,
                "--version"
        );
        processBuilder.directory(workingDirectory.toFile());
        processBuilder.redirectErrorStream(true);
        processBuilder.environment().put("PYTHONIOENCODING", "utf-8");
        processBuilder.environment().put("PYTHONUTF8", "1");

        try {
            Process process = processBuilder.start();
            boolean finished = process.waitFor(
                    timeout.toMillis(),
                    TimeUnit.MILLISECONDS
            );

            if (!finished) {
                process.destroyForcibly();

                return ReadinessCheck.down(
                        CHECK_NAME,
                        "The configured Python command did not respond before the readiness timeout."
                );
            }

            String output = readOutput(process);
            int exitCode = process.exitValue();

            if (exitCode != 0) {
                return ReadinessCheck.down(
                        CHECK_NAME,
                        "The configured Python command exited with code %d%s."
                                .formatted(
                                        exitCode,
                                        output.isBlank() ? "" : ": " + output
                                )
                );
            }

            return ReadinessCheck.up(
                    CHECK_NAME,
                    output.isBlank()
                            ? "The configured Python command is available."
                            : output
            );
        } catch (IOException exc) {
            return ReadinessCheck.down(
                    CHECK_NAME,
                    "The configured Python command could not be started: %s"
                            .formatted(exc.getMessage())
            );
        } catch (InterruptedException exc) {
            Thread.currentThread().interrupt();

            return ReadinessCheck.down(
                    CHECK_NAME,
                    "The Python command readiness check was interrupted."
            );
        }
    }

    private static String readOutput(Process process) throws IOException {
        try (
                var inputStream = process.getInputStream();
                var buffer = new ByteArrayOutputStream()
        ) {
            inputStream.transferTo(buffer);

            return buffer
                    .toString(StandardCharsets.UTF_8)
                    .lines()
                    .findFirst()
                    .orElse("")
                    .trim();
        }
    }
}
