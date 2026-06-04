package com.compoundingquality.reviewapi.rag;

import java.util.List;

public record RagReviewSummary(
        String recordReviewResult,
        String lotBatchPatternSummary,
        String inventoryInspectionResult,
        String customerContextSummary,
        String apiReferenceReviewResult,
        List<String> missingInformation,
        List<String> evidenceLimitations,
        List<String> severeTriggersObserved
) {
    public RagReviewSummary {
        recordReviewResult = requireText(recordReviewResult, "recordReviewResult");
        lotBatchPatternSummary = requireText(lotBatchPatternSummary, "lotBatchPatternSummary");
        inventoryInspectionResult = requireText(inventoryInspectionResult, "inventoryInspectionResult");
        apiReferenceReviewResult = requireText(apiReferenceReviewResult, "apiReferenceReviewResult");

        missingInformation = missingInformation == null
                ? List.of()
                : List.copyOf(missingInformation);

        evidenceLimitations = evidenceLimitations == null
                ? List.of()
                : List.copyOf(evidenceLimitations);

        severeTriggersObserved = severeTriggersObserved == null
                ? List.of()
                : List.copyOf(severeTriggersObserved);
    }

    private static String requireText(String value, String fieldName) {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException(fieldName + " must not be blank");
        }

        return value;
    }
}
