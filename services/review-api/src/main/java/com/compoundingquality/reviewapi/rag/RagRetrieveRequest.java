package com.compoundingquality.reviewapi.rag;

public record RagRetrieveRequest(
        String queryText,
        int topK
) {
    public static final int DEFAULT_TOP_K = 5;

    public RagRetrieveRequest {
        if (queryText == null || queryText.isBlank()) {
            throw new IllegalArgumentException("queryText must not be blank");
        }

        if (topK < 1) {
            throw new IllegalArgumentException("topK must be at least 1");
        }
    }

    public static RagRetrieveRequest fromQueryText(String queryText) {
        return new RagRetrieveRequest(queryText, DEFAULT_TOP_K);
    }
}
