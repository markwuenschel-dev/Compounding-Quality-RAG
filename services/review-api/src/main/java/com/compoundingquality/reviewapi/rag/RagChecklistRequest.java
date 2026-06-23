package com.compoundingquality.reviewapi.rag;

public record RagChecklistRequest(
        String concernText,
        int topK
) {
    public static final int DEFAULT_TOP_K = 5;

    public RagChecklistRequest {
        if (concernText == null || concernText.isBlank()) {
            throw new IllegalArgumentException("concernText must not be blank");
        }

        if (topK < 1) {
            throw new IllegalArgumentException("topK must be at least 1");
        }
    }

    public static RagChecklistRequest fromConcernText(String concernText) {
        return new RagChecklistRequest(concernText, DEFAULT_TOP_K);
    }
}