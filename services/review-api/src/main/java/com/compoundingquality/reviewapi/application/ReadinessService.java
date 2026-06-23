package com.compoundingquality.reviewapi.application;

import com.compoundingquality.reviewapi.dto.ReadinessResponse;
import com.compoundingquality.reviewapi.dto.ReadinessResponse.ReadinessCheck;
import com.compoundingquality.reviewapi.rag.HttpRagEngineProperties;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import org.springframework.stereotype.Service;

@Service
public class ReadinessService {

    private static final Duration RAG_ENGINE_PROBE_TIMEOUT = Duration.ofSeconds(3);

    private final HttpRagEngineProperties ragEngineProperties;
    private final HttpClient httpClient;

    public ReadinessService(HttpRagEngineProperties ragEngineProperties) {
        this.ragEngineProperties = ragEngineProperties;
        this.httpClient = HttpClient.newBuilder()
                .connectTimeout(RAG_ENGINE_PROBE_TIMEOUT)
                .build();
    }

    public ReadinessResponse checkReadiness() {
        List<ReadinessCheck> checks = new ArrayList<>();

        checks.add(
                ReadinessCheck.up(
                        "spring",
                        "The Spring Boot API is running."
                )
        );

        checks.add(checkRagEngineBaseUrl());
        checks.add(checkRagEngineHealth());

        boolean ready = checks.stream().allMatch(ReadinessCheck::available);

        return new ReadinessResponse(
                ready
                        ? ReadinessResponse.READY
                        : ReadinessResponse.NOT_READY,
                checks,
                Instant.now()
        );
    }

    private ReadinessCheck checkRagEngineBaseUrl() {
        URI baseUrl = ragEngineProperties.baseUrl();

        return ReadinessCheck.up(
                "ragEngineBaseUrl",
                "Configured Python RAG engine base URL: %s".formatted(baseUrl)
        );
    }

    private ReadinessCheck checkRagEngineHealth() {
        URI healthUri = ragEngineProperties.baseUrl().resolve("/health");

        HttpRequest request = HttpRequest.newBuilder()
                .uri(healthUri)
                .timeout(RAG_ENGINE_PROBE_TIMEOUT)
                .GET()
                .build();

        try {
            HttpResponse<String> response = httpClient.send(
                    request,
                    HttpResponse.BodyHandlers.ofString()
            );

            if (response.statusCode() >= 200 && response.statusCode() < 300) {
                return ReadinessCheck.up(
                        "ragEngineHealth",
                        "Python RAG engine health endpoint responded with HTTP %d."
                                .formatted(response.statusCode())
                );
            }

            return ReadinessCheck.down(
                    "ragEngineHealth",
                    "Python RAG engine health endpoint responded with HTTP %d."
                            .formatted(response.statusCode())
            );
        } catch (IOException exc) {
            return ReadinessCheck.down(
                    "ragEngineHealth",
                    "Python RAG engine health endpoint could not be reached: %s"
                            .formatted(exc.getMessage())
            );
        } catch (InterruptedException exc) {
            Thread.currentThread().interrupt();

            return ReadinessCheck.down(
                    "ragEngineHealth",
                    "Python RAG engine health probe was interrupted."
            );
        } catch (IllegalArgumentException exc) {
            return ReadinessCheck.down(
                    "ragEngineHealth",
                    "Python RAG engine health URI is invalid: %s"
                            .formatted(exc.getMessage())
            );
        }
    }
}