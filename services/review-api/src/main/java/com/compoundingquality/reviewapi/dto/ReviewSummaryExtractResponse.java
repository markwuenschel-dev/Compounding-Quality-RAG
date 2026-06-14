package com.compoundingquality.reviewapi.dto;

import java.util.List;
import java.util.Objects;

public record ReviewSummaryExtractResponse(
        ReviewSummary reviewSummary,
        List<FieldEvidence> fieldEvidence,
        List<UnresolvedQuestion> unresolvedQuestions
) {

    public ReviewSummaryExtractResponse {
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

    public record ReviewSummary(
            String recordReviewResult,
            String lotBatchPatternSummary,
            String inventoryInspectionResult,
            String customerContextSummary,
            String apiReferenceReviewResult,
            List<String> missingInformation,
            List<String> evidenceLimitations,
            List<String> severeTriggersObserved
    ) {

        public ReviewSummary {
            recordReviewResult = requireText(
                    recordReviewResult,
                    "recordReviewResult"
            );
            lotBatchPatternSummary = requireText(
                    lotBatchPatternSummary,
                    "lotBatchPatternSummary"
            );
            inventoryInspectionResult = requireText(
                    inventoryInspectionResult,
                    "inventoryInspectionResult"
            );
            apiReferenceReviewResult = requireText(
                    apiReferenceReviewResult,
                    "apiReferenceReviewResult"
            );
            missingInformation = copy(missingInformation);
            evidenceLimitations = copy(evidenceLimitations);
            severeTriggersObserved = copy(severeTriggersObserved);
        }
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
            decisionImpact = copy(decisionImpact);
        }
    }

    private static List<String> copy(List<String> values) {
        return values == null ? List.of() : List.copyOf(values);
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
