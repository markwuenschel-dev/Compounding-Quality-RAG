package com.compoundingquality.reviewapi.rag;

import static org.assertj.core.api.Assertions.assertThat;

import com.compoundingquality.reviewapi.config.RequestCorrelationFilter;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.slf4j.MDC;
import org.springframework.web.client.RestClient;

class HttpRagEngineClientTest {

    private HttpServer server;

    @AfterEach
    void tearDown() {
        MDC.clear();
        if (server != null) {
            server.stop(0);
        }
    }

    @Test
    void forwardsRequestIdFromMdcToPythonRagEngine() throws Exception {
        CapturedRequest capturedRequest = new CapturedRequest();
        server = HttpServer.create(new InetSocketAddress(0), 0);
        server.createContext("/retrieve", exchange -> handleRetrieve(
                exchange,
                capturedRequest
        ));
        server.start();

        URI baseUrl = URI.create(
                "http://localhost:%d/".formatted(server.getAddress().getPort())
        );
        HttpRagEngineClient client = new HttpRagEngineClient(
                RestClient.builder(),
                new HttpRagEngineProperties(baseUrl)
        );

        MDC.put(RequestCorrelationFilter.REQUEST_ID_MDC_KEY, "test-request-id-123");

        RagRetrieveResult result = client.retrieve(
                new RagRetrieveRequest("flavor concern", 3)
        );

        assertThat(result.queryText()).isEqualTo("flavor concern");
        assertThat(capturedRequest.requestId).isEqualTo("test-request-id-123");
        assertThat(capturedRequest.body).contains("\"query\":\"flavor concern\"");
    }

    private void handleRetrieve(
            HttpExchange exchange,
            CapturedRequest capturedRequest
    ) throws IOException {
        capturedRequest.requestId =
                exchange.getRequestHeaders()
                        .getFirst(RequestCorrelationFilter.REQUEST_ID_HEADER);
        capturedRequest.body = new String(
                exchange.getRequestBody().readAllBytes(),
                StandardCharsets.UTF_8
        );

        byte[] response = """
                {
                  "query_text": "flavor concern",
                  "top_k": 3,
                  "evidence": []
                }
                """.getBytes(StandardCharsets.UTF_8);

        exchange.getResponseHeaders().add("Content-Type", "application/json");
        exchange.sendResponseHeaders(200, response.length);
        exchange.getResponseBody().write(response);
        exchange.close();
    }

    private static final class CapturedRequest {
        private String requestId;
        private String body;
    }
}
