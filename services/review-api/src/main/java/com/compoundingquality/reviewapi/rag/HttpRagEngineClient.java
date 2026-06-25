package com.compoundingquality.reviewapi.rag;

import com.compoundingquality.reviewapi.config.RequestCorrelationFilter;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.json.JsonMapper;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.Objects;
import org.slf4j.MDC;
import org.springframework.web.client.RestClient;

public final class HttpRagEngineClient implements RagEngineClient {

    private static final Duration REQUEST_TIMEOUT = Duration.ofSeconds(30);

    private final URI baseUrl;
    private final HttpClient httpClient;
    private final JsonMapper jsonMapper;

    public HttpRagEngineClient(
            RestClient.Builder restClientBuilder,
            HttpRagEngineProperties properties
    ) {
        Objects.requireNonNull(restClientBuilder, "restClientBuilder must not be null");
        Objects.requireNonNull(properties, "properties must not be null");

        this.baseUrl = properties.baseUrl();
        this.httpClient = HttpClient.newBuilder()
                .connectTimeout(REQUEST_TIMEOUT)
                .build();
        this.jsonMapper = JsonMapper.builder()
                .propertyNamingStrategy(PropertyNamingStrategies.SNAKE_CASE)
                .build();
    }

    @Override
    public RagChecklistResult createChecklist(RagChecklistRequest request) {
        Objects.requireNonNull(request, "request must not be null");

        return postJson(
                "/checklist",
                new PythonChecklistRequest(
                        request.concernText(),
                        request.topK()
                ),
                RagChecklistResult.class,
                "CHECKLIST_FAILED"
        );
    }

    @Override
    public RagRetrieveResult retrieve(RagRetrieveRequest request) {
        Objects.requireNonNull(request, "request must not be null");

        return postJson(
                "/retrieve",
                new PythonRetrieveRequest(
                        request.queryText(),
                        request.topK()
                ),
                RagRetrieveResult.class,
                "RETRIEVE_FAILED"
        );
    }

    @Override
    public RagFinalAssessmentResult createFinalAssessment(
            RagFinalAssessmentRequest request
    ) {
        Objects.requireNonNull(request, "request must not be null");

        return postJson(
                "/final-assessment",
                new PythonFinalAssessmentRequest(
                        request.concernText(),
                        request.topK(),
                        request.reviewSummary()
                ),
                RagFinalAssessmentResult.class,
                "FINAL_ASSESSMENT_FAILED"
        );
    }

    @Override
    public RagReviewSummaryExtractResult extractReviewSummary(
            RagReviewSummaryExtractRequest request
    ) {
        Objects.requireNonNull(request, "request must not be null");

        return postJson(
                "/review-summary/extract",
                new PythonReviewSummaryExtractRequest(
                        request.pharmacistNotes(),
                        request.concernText()
                ),
                RagReviewSummaryExtractResult.class,
                "REVIEW_SUMMARY_EXTRACT_FAILED"
        );
    }

    private <T> T postJson(
            String path,
            Object requestBody,
            Class<T> responseType,
            String errorCode
    ) {
        String requestJson = encodeRequest(requestBody, errorCode);
        URI uri = baseUrl.resolve(path);

        HttpRequest.Builder requestBuilder = HttpRequest.newBuilder()
                .uri(uri)
                .version(HttpClient.Version.HTTP_1_1)
                .timeout(REQUEST_TIMEOUT)
                .header("Content-Type", "application/json; charset=utf-8")
                .header("Accept", "application/json")
                .POST(HttpRequest.BodyPublishers.ofByteArray(
                        requestJson.getBytes(java.nio.charset.StandardCharsets.UTF_8)
                ));

        String requestId = MDC.get(RequestCorrelationFilter.REQUEST_ID_MDC_KEY);
        if (requestId != null && !requestId.isBlank()) {
            requestBuilder.header(RequestCorrelationFilter.REQUEST_ID_HEADER, requestId);
        }

        HttpRequest request = requestBuilder.build();

        HttpResponse<String> response;

        try {
            response = httpClient.send(
                    request,
                    HttpResponse.BodyHandlers.ofString()
            );
        } catch (IOException exc) {
            throw new RagEngineException(
                    errorCode,
                    "Python RAG engine HTTP call failed: %s"
                            .formatted(exc.getMessage()),
                    exc
            );
        } catch (InterruptedException exc) {
            Thread.currentThread().interrupt();

            throw new RagEngineException(
                    errorCode,
                    "Python RAG engine HTTP call was interrupted.",
                    exc
            );
        }

        int statusCode = response.statusCode();
        String responseBody = response.body();

        if (statusCode < 200 || statusCode >= 300) {
            throw new RagEngineException(
                    errorCode,
                    "Python RAG engine returned HTTP %d. Request body: %s. Response body: %s"
                            .formatted(statusCode, requestJson, responseBody)
            );
        }

        if (responseBody == null || responseBody.isBlank()) {
            throw new RagEngineException(
                    errorCode,
                    "Python RAG engine returned an empty response."
            );
        }

        return decodeResponse(responseBody, responseType, errorCode);
    }

    private String encodeRequest(Object requestBody, String errorCode) {
        try {
            return jsonMapper.writeValueAsString(requestBody);
        } catch (JsonProcessingException exc) {
            throw new RagEngineException(
                    errorCode,
                    "Failed to encode Python RAG engine request.",
                    exc
            );
        }
    }

    private <T> T decodeResponse(
            String responseJson,
            Class<T> responseType,
            String errorCode
    ) {
        try {
            return jsonMapper.readValue(responseJson, responseType);
        } catch (JsonProcessingException exc) {
            throw new RagEngineException(
                    errorCode,
                    "Python RAG engine response did not match Java response type %s. Response body: %s"
                            .formatted(responseType.getSimpleName(), responseJson),
                    exc
            );
        }
    }

    private record PythonChecklistRequest(
            @JsonProperty("concern_text") String concernText,
            @JsonProperty("top_k") int topK
    ) {
    }

    private record PythonRetrieveRequest(
            String query,
            @JsonProperty("top_k") int topK
    ) {
    }

    private record PythonFinalAssessmentRequest(
            @JsonProperty("concern_text") String concernText,
            @JsonProperty("top_k") int topK,
            @JsonProperty("review_summary") RagReviewSummary reviewSummary
    ) {
    }

    private record PythonReviewSummaryExtractRequest(
            @JsonProperty("reviewer_note") String reviewerNote,
            @JsonProperty("concern_text") String concernText
    ) {
    }
}