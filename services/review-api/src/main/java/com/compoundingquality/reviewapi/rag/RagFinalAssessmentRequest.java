package com.compoundingquality.reviewapi.rag;

import java.util.Objects;

public record RagFinalAssessmentRequest(
        String concernText,
        int topK,
        RagReviewSummary reviewSummary
) {
    public static final int DEFAULT_TOP_K = 5;

    public RagFinalAssessmentRequest {
        if (concernText == null || concernText.isBlank()) {
            throw new IllegalArgumentException("concernText must not be blank");
        }

        if (topK < 1) {
            throw new IllegalArgumentException("topK must be at least 1");
        }

        reviewSummary = Objects.requireNonNull(
                reviewSummary,
                "reviewSummary must not be null"
        );
    }

    public static RagFinalAssessmentRequest fromConcernText(
            String concernText,
            RagReviewSummary reviewSummary
    ) {
        return new RagFinalAssessmentRequest(
                concernText,
                DEFAULT_TOP_K,
                reviewSummary
        );
    }
}
