package com.compoundingquality.reviewapi.rag;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Objects;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;

public class PythonProcessRagEngineClient implements RagEngineClient {

    private static final String COMMAND_CHECKLIST = "checklist";
    private static final int STDERR_SUMMARY_LIMIT = 2_000;

    private final ObjectMapper objectMapper;
    private final PythonProcessRagEngineProperties properties;
    private final ProcessExecutor processExecutor;

    public PythonProcessRagEngineClient(
            ObjectMapper objectMapper,
            PythonProcessRagEngineProperties properties
    ) {
        this(objectMapper, properties, new DefaultProcessExecutor());
    }

    PythonProcessRagEngineClient(
            ObjectMapper objectMapper,
            PythonProcessRagEngineProperties properties,
            ProcessExecutor processExecutor
    ) {
        this.objectMapper = Objects.requireNonNull(objectMapper, "objectMapper must not be null");
        this.properties = Objects.requireNonNull(properties, "properties must not be null");
        this.processExecutor = Objects.requireNonNull(processExecutor, "processExecutor must not be null");
    }

    @Override
    public RagChecklistResult createChecklist(RagChecklistRequest request) {
        Objects.requireNonNull(request, "request must not be null");

        String stdinJson = encodeBridgeRequest(request);
        ProcessResult processResult = processExecutor.execute(properties, stdinJson);

        if (processResult.exitCode() != 0) {
            throw new RagEngineException(
                    "ENGINE_PROCESS_EXIT",
                    "Python RAG engine exited with code %d. stderr: %s".formatted(
                            processResult.exitCode(),
                            summarize(processResult.stderr())
                    )
            );
        }

        BridgeResponse response = decodeBridgeResponse(processResult.stdout());

        if (response.ok() == null) {
            throw new RagEngineException(
                    "ENGINE_INVALID_RESPONSE",
                    "Python RAG engine response did not include ok status."
            );
        }

        if (!response.ok()) {
            BridgeError error = response.error();
            String code = hasText(error == null ? null : error.code())
                    ? error.code()
                    : "ENGINE_ERROR";
            String message = hasText(error == null ? null : error.message())
                    ? error.message()
                    : "Python RAG engine returned an error.";

            throw new RagEngineException(code, message);
        }

        if (response.result() == null) {
            throw new RagEngineException(
                    "ENGINE_INVALID_RESPONSE",
                    "Python RAG engine returned ok=true without a result."
            );
        }

        return mapResult(response.result());
    }

    private String encodeBridgeRequest(RagChecklistRequest request) {
        BridgeRequest bridgeRequest = new BridgeRequest(
                COMMAND_CHECKLIST,
                new BridgePayload(request.concernText(), request.topK())
        );

        try {
            return objectMapper.writeValueAsString(bridgeRequest);
        } catch (JsonProcessingException exc) {
            throw new RagEngineException(
                    "ENGINE_REQUEST_ENCODING",
                    "Failed to encode Python RAG engine request.",
                    exc
            );
        }
    }

    private BridgeResponse decodeBridgeResponse(String stdout) {
        if (!hasText(stdout)) {
            throw new RagEngineException(
                    "ENGINE_INVALID_STDOUT",
                    "Python RAG engine returned empty stdout."
            );
        }

        try {
            return objectMapper.readValue(stdout, BridgeResponse.class);
        } catch (JsonProcessingException exc) {
            throw new RagEngineException(
                    "ENGINE_INVALID_STDOUT",
                    "Python RAG engine stdout was not valid bridge JSON.",
                    exc
            );
        }
    }

    private RagChecklistResult mapResult(BridgeResult result) {
        try {
            return new RagChecklistResult(
                    result.concernType(),
                    result.riskLane(),
                    result.reviewScope(),
                    result.initialTakeaway(),
                    mapChecklistItems(result.requiredChecks()),
                    copyStrings(result.missingInformation()),
                    copyStrings(result.escalationTriggersToRuleOut()),
                    mapEvidence(result.evidence()),
                    copyStrings(result.limitations())
            );
        } catch (IllegalArgumentException exc) {
            throw new RagEngineException(
                    "ENGINE_RESPONSE_MAPPING",
                    "Python RAG engine result did not match the Java checklist contract.",
                    exc
            );
        }
    }

    private static List<RagChecklistResult.ChecklistItem> mapChecklistItems(
            List<BridgeChecklistItem> items
    ) {
        if (items == null) {
            return List.of();
        }

        return items.stream()
                .map(item -> new RagChecklistResult.ChecklistItem(
                        item.key(),
                        item.label(),
                        item.required(),
                        item.reason()
                ))
                .toList();
    }

    private static List<RagChecklistResult.EvidenceCitation> mapEvidence(
            List<BridgeEvidenceCitation> citations
    ) {
        if (citations == null) {
            return List.of();
        }

        return citations.stream()
                .map(citation -> new RagChecklistResult.EvidenceCitation(
                        citation.chunkId(),
                        citation.sourceId(),
                        citation.sourceTitle(),
                        citation.sourceType(),
                        citation.sectionHeading(),
                        citation.score(),
                        copyStrings(citation.matchedTerms()),
                        citation.supportingText()
                ))
                .toList();
    }

    private static List<String> copyStrings(List<String> values) {
        return values == null ? List.of() : List.copyOf(values);
    }

    private static String summarize(String value) {
        if (!hasText(value)) {
            return "<empty>";
        }

        String trimmed = value.trim();

        if (trimmed.length() <= STDERR_SUMMARY_LIMIT) {
            return trimmed;
        }

        return trimmed.substring(0, STDERR_SUMMARY_LIMIT) + "...";
    }

    private static boolean hasText(String value) {
        return value != null && !value.isBlank();
    }

    interface ProcessExecutor {
        ProcessResult execute(
                PythonProcessRagEngineProperties properties,
                String stdinJson
        );
    }

    record ProcessResult(
            int exitCode,
            String stdout,
            String stderr
    ) {
        ProcessResult {
            stdout = stdout == null ? "" : stdout;
            stderr = stderr == null ? "" : stderr;
        }
    }

    private static final class DefaultProcessExecutor implements ProcessExecutor {

        @Override
        public ProcessResult execute(
                PythonProcessRagEngineProperties properties,
                String stdinJson
        ) {
            Process process = startProcess(properties);

            try (ExecutorService executor = Executors.newFixedThreadPool(2)) {
                Future<String> stdoutFuture = executor.submit(
                        () -> readFully(process.getInputStream())
                );
                Future<String> stderrFuture = executor.submit(
                        () -> readFully(process.getErrorStream())
                );

                writeStdin(process, stdinJson);

                boolean finished = process.waitFor(
                        properties.timeout().toMillis(),
                        TimeUnit.MILLISECONDS
                );

                if (!finished) {
                    process.destroyForcibly();

                    throw new RagEngineException(
                            "ENGINE_TIMEOUT",
                            "Python RAG engine timed out after %s.".formatted(properties.timeout())
                    );
                }

                return new ProcessResult(
                        process.exitValue(),
                        getFuture(stdoutFuture),
                        getFuture(stderrFuture)
                );
            } catch (InterruptedException exc) {
                Thread.currentThread().interrupt();
                process.destroyForcibly();

                throw new RagEngineException(
                        "ENGINE_INTERRUPTED",
                        "Python RAG engine call was interrupted.",
                        exc
                );
            }
        }

        private static Process startProcess(PythonProcessRagEngineProperties properties) {
            ProcessBuilder processBuilder = new ProcessBuilder(properties.command());
            processBuilder.directory(properties.workingDirectory().toFile());

            try {
                return processBuilder.start();
            } catch (IOException exc) {
                throw new RagEngineException(
                        "ENGINE_PROCESS_START",
                        "Failed to start Python RAG engine process.",
                        exc
                );
            }
        }

        private static void writeStdin(Process process, String stdinJson) {
            try (OutputStream stdin = process.getOutputStream()) {
                stdin.write(stdinJson.getBytes(StandardCharsets.UTF_8));
                stdin.flush();
            } catch (IOException exc) {
                process.destroyForcibly();

                throw new RagEngineException(
                        "ENGINE_STDIN_WRITE",
                        "Failed to write request JSON to Python RAG engine stdin.",
                        exc
                );
            }
        }

        private static String readFully(InputStream inputStream) throws IOException {
            try (inputStream; ByteArrayOutputStream buffer = new ByteArrayOutputStream()) {
                inputStream.transferTo(buffer);
                return buffer.toString(StandardCharsets.UTF_8);
            }
        }

        private static String getFuture(Future<String> future) throws InterruptedException {
            try {
                return future.get();
            } catch (ExecutionException exc) {
                throw new RagEngineException(
                        "ENGINE_STREAM_READ",
                        "Failed to read Python RAG engine process output.",
                        exc
                );
            }
        }
    }

    record BridgeRequest(
            String command,
            BridgePayload payload
    ) {
    }

    record BridgePayload(
            String concernText,
            int topK
    ) {
    }

    record BridgeResponse(
            Boolean ok,
            BridgeResult result,
            BridgeError error
    ) {
    }

    record BridgeError(
            String code,
            String message
    ) {
    }

    record BridgeResult(
            String concernType,
            String riskLane,
            String reviewScope,
            String initialTakeaway,
            List<BridgeChecklistItem> requiredChecks,
            List<String> missingInformation,
            List<String> escalationTriggersToRuleOut,
            List<BridgeEvidenceCitation> evidence,
            List<String> limitations
    ) {
    }

    record BridgeChecklistItem(
            String key,
            String label,
            boolean required,
            String reason
    ) {
    }

    record BridgeEvidenceCitation(
            String chunkId,
            String sourceId,
            String sourceTitle,
            String sourceType,
            String sectionHeading,
            Double score,
            List<String> matchedTerms,
            String supportingText
    ) {
    }
}