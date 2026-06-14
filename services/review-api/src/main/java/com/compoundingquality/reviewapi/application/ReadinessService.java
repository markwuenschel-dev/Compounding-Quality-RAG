package com.compoundingquality.reviewapi.application;

import com.compoundingquality.reviewapi.dto.ReadinessResponse;
import com.compoundingquality.reviewapi.dto.ReadinessResponse.ReadinessCheck;
import com.compoundingquality.reviewapi.rag.PythonProcessRagEngineProperties;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import org.springframework.stereotype.Service;

@Service
public class ReadinessService {

    private static final Duration PYTHON_PROBE_TIMEOUT = Duration.ofSeconds(3);
    private static final String CORPUS_RELATIVE_PATH = "data/corpus";

    private final PythonProcessRagEngineProperties ragEngineProperties;
    private final PythonCommandProbe pythonCommandProbe;

    public ReadinessService(
            PythonProcessRagEngineProperties ragEngineProperties,
            PythonCommandProbe pythonCommandProbe
    ) {
        this.ragEngineProperties = ragEngineProperties;
        this.pythonCommandProbe = pythonCommandProbe;
    }

    public ReadinessResponse checkReadiness() {
        Path workingDirectory = ragEngineProperties
                .workingDirectory()
                .toAbsolutePath()
                .normalize();

        List<ReadinessCheck> checks = new ArrayList<>();
        checks.add(
                ReadinessCheck.up(
                        "spring",
                        "The Spring Boot API is running."
                )
        );

        ReadinessCheck workingDirectoryCheck =
                checkWorkingDirectory(workingDirectory);
        checks.add(workingDirectoryCheck);

        if (workingDirectoryCheck.available()) {
            checks.add(
                    pythonCommandProbe.probe(
                            ragEngineProperties.command(),
                            workingDirectory,
                            PYTHON_PROBE_TIMEOUT
                    )
            );
            checks.add(checkCorpus(workingDirectory.resolve(CORPUS_RELATIVE_PATH)));
        } else {
            checks.add(
                    ReadinessCheck.down(
                            "pythonCommand",
                            "The Python command was not checked because the configured working directory is unavailable."
                    )
            );
            checks.add(
                    ReadinessCheck.down(
                            "corpus",
                            "The corpus was not checked because the configured working directory is unavailable."
                    )
            );
        }

        boolean ready = checks.stream().allMatch(ReadinessCheck::available);

        return new ReadinessResponse(
                ready
                        ? ReadinessResponse.READY
                        : ReadinessResponse.NOT_READY,
                checks,
                Instant.now()
        );
    }

    private static ReadinessCheck checkWorkingDirectory(Path workingDirectory) {
        if (!Files.isDirectory(workingDirectory)) {
            return ReadinessCheck.down(
                    "workingDirectory",
                    "Configured working directory does not exist: %s"
                            .formatted(workingDirectory)
            );
        }

        if (!Files.isReadable(workingDirectory)) {
            return ReadinessCheck.down(
                    "workingDirectory",
                    "Configured working directory is not readable: %s"
                            .formatted(workingDirectory)
            );
        }

        return ReadinessCheck.up(
                "workingDirectory",
                workingDirectory.toString()
        );
    }

    private static ReadinessCheck checkCorpus(Path corpusDirectory) {
        if (!Files.isDirectory(corpusDirectory)) {
            return ReadinessCheck.down(
                    "corpus",
                    "Corpus directory does not exist: %s"
                            .formatted(corpusDirectory)
            );
        }

        try (var paths = Files.walk(corpusDirectory)) {
            long sourceCount = paths
                    .filter(Files::isRegularFile)
                    .filter(ReadinessService::isSupportedCorpusFile)
                    .count();

            if (sourceCount == 0) {
                return ReadinessCheck.down(
                        "corpus",
                        "Corpus directory contains no supported source files: %s"
                                .formatted(corpusDirectory)
                );
            }

            return ReadinessCheck.up(
                    "corpus",
                    "%d source file%s available in %s"
                            .formatted(
                                    sourceCount,
                                    sourceCount == 1 ? "" : "s",
                                    corpusDirectory
                            )
            );
        } catch (IOException exc) {
            return ReadinessCheck.down(
                    "corpus",
                    "Corpus directory could not be inspected: %s"
                            .formatted(exc.getMessage())
            );
        }
    }

    private static boolean isSupportedCorpusFile(Path path) {
        String filename = path.getFileName().toString().toLowerCase();

        return filename.endsWith(".md")
                || filename.endsWith(".txt")
                || filename.endsWith(".json");
    }
}
