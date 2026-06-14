package com.compoundingquality.reviewapi.rag;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.Objects;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import tools.jackson.core.JacksonException;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.json.JsonMapper;

public class PythonProcessRagEngineClient implements RagEngineClient {

    private static final String COMMAND_CHECKLIST = "checklist";
    private static final String COMMAND_RETRIEVE = "retrieve";
    private static final String COMMAND_FINAL_ASSESSMENT = "final_assessment";
    private static final int STDERR_SUMMARY_LIMIT = 2_000;

    private final JsonMapper jsonMapper;
    private final PythonProcessRagEngineProperties properties;
    private final ProcessExecutor processExecutor;

    public PythonProcessRagEngineClient(
            JsonMapper jsonMapper,
            PythonProcessRagEngineProperties properties
    ) {
        this(jsonMapper, properties, new DefaultProcessExecutor());
    }

    PythonProcessRagEngineClient(
            JsonMapper jsonMapper,
            PythonProcessRagEngineProperties properties,
            ProcessExecutor processExecutor
    ) {
        this.jsonMapper = Objects.requireNonNull(jsonMapper, "jsonMapper must not be null");
        this.properties = Objects.requireNonNull(properties, "properties must not be null");
        this.processExecutor = Objects.requireNonNull(processExecutor, "processExecutor must not be null");
    }

    @Override
    public RagChecklistResult createChecklist(RagChecklistRequest request) {
        Objects.requireNonNull(request, "request must not be null");

        return executeCommand(
                COMMAND_CHECKLIST,
                new ChecklistPayload(request.concernText(), request.topK()),
                RagChecklistResult.class
        );
    }

    @Override
    public RagRetrieveResult retrieve(RagRetrieveRequest request) {
        Objects.requireNonNull(request, "request must not be null");

        return executeCommand(
                COMMAND_RETRIEVE,
                new RetrievePayload(request.queryText(), request.topK()),
                RagRetrieveResult.class
        );
    }

    @Override
    public RagFinalAssessmentResult createFinalAssessment(RagFinalAssessmentRequest request) {
        Objects.requireNonNull(request, "request must not be null");

        return executeCommand(
                COMMAND_FINAL_ASSESSMENT,
                new FinalAssessmentPayload(
                        request.concernText(),
                        request.topK(),
                        request.reviewSummary()
                ),
                RagFinalAssessmentResult.class
        );
    }

    private <T> T executeCommand(
            String command,
            Object payload,
            Class<T> resultType
    ) {
        String stdinJson = encodeBridgeRequest(new BridgeRequest(command, payload));
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

        if (response.result() == null || response.result().isNull()) {
            throw new RagEngineException(
                    "ENGINE_INVALID_RESPONSE",
                    "Python RAG engine returned ok=true without a result."
            );
        }

        return decodeBridgeResult(response.result(), resultType);
    }

    private String encodeBridgeRequest(BridgeRequest request) {
        try {
            return jsonMapper.writeValueAsString(request);
        } catch (JacksonException exc) {
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
            return jsonMapper.readValue(stdout, BridgeResponse.class);
        } catch (JacksonException exc) {
            throw new RagEngineException(
                    "ENGINE_INVALID_STDOUT",
                    "Python RAG engine stdout was not valid bridge JSON.",
                    exc
            );
        }
    }

    private <T> T decodeBridgeResult(JsonNode result, Class<T> resultType) {
        try {
            return jsonMapper.treeToValue(result, resultType);
        } catch (JacksonException exc) {
            throw new RagEngineException(
                    "ENGINE_RESPONSE_MAPPING",
                    "Python RAG engine result did not match the Java %s contract."
                            .formatted(resultType.getSimpleName()),
                    exc
            );
        }
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

        private static Process startProcess(
                PythonProcessRagEngineProperties properties
        ) {
            ProcessBuilder processBuilder = new ProcessBuilder(properties.command());
            processBuilder.directory(properties.workingDirectory().toFile());
            processBuilder.environment().put("PYTHONIOENCODING", "utf-8");
            processBuilder.environment().put("PYTHONUTF8", "1");

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
            Object payload
    ) {
    }

    record BridgeResponse(
            Boolean ok,
            JsonNode result,
            BridgeError error
    ) {
    }

    record BridgeError(
            String code,
            String message,
            JsonNode details
    ) {
    }

    record ChecklistPayload(
            String concernText,
            int topK
    ) {
    }

    record RetrievePayload(
            String queryText,
            int topK
    ) {
    }

    record FinalAssessmentPayload(
            String concernText,
            int topK,
            RagReviewSummary reviewSummary
    ) {
    }
}
