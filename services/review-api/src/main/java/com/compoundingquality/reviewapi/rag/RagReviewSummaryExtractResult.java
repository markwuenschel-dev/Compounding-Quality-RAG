package com.compoundingquality.reviewapi.rag;

import java.util.List;
import java.util.Objects;

public record RagReviewSummaryExtractResult(
        RagReviewSummary reviewSummary,
        List<FieldEvidence> fieldEvidence,
        List<UnresolvedQuestion> unresolvedQuestions
) {

    public RagReviewSummaryExtractResult {
        reviewSummary = Objects.requireNonNull(
                reviewSummary,
                "reviewSummary must not be null"
        );
        fieldEvidence = fieldEvidence == null
                ? List.of()
                : List.copyOf(fieldEvidence);
        unresolvedQuestions = unresolvedQuestions == null
                ? List.of()
                : List.copyOf(unresolvedQuestions);
    }

    public record FieldEvidence(
            String fieldName,
            String status,
            String supportingQuote,
            String explanation
    ) {

        public FieldEvidence {
            fieldName = requireText(fieldName, "fieldName");
            status = requireText(status, "status");
        }
    }

    public record UnresolvedQuestion(
            String fieldName,
            String question,
            String reason,
            List<String> decisionImpact
    ) {

        public UnresolvedQuestion {
            fieldName = requireText(fieldName, "fieldName");
            question = requireText(question, "question");
            reason = requireText(reason, "reason");
            decisionImpact = decisionImpact == null
                    ? List.of()
                    : List.copyOf(decisionImpact);
        }
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
