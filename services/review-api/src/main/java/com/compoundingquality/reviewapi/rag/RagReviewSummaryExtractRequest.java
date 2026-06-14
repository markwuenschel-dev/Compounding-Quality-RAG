package com.compoundingquality.reviewapi.rag;

public record RagReviewSummaryExtractRequest(
        String concernText,
        String pharmacistNotes
) {

    public RagReviewSummaryExtractRequest {
        concernText = requireText(concernText, "concernText");
        pharmacistNotes = requireText(pharmacistNotes, "pharmacistNotes");
    }

    private static String requireText(String value, String fieldName) {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException(
                    fieldName + " must not be blank"
            );
        }

        return value;
    }
}
