package com.compoundingquality.reviewapi.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import java.util.List;

public record ReviewSummaryRequest(
        @NotBlank(message = "recordReviewResult must not be blank")
        String recordReviewResult,

        @NotBlank(message = "lotBatchPatternSummary must not be blank")
        String lotBatchPatternSummary,

        @NotBlank(message = "inventoryInspectionResult must not be blank")
        String inventoryInspectionResult,

        @Size(max = 5_000, message = "customerContextSummary must be 5000 characters or fewer")
        String customerContextSummary,

        @NotBlank(message = "apiReferenceReviewResult must not be blank")
        String apiReferenceReviewResult,

        List<@NotBlank(message = "missingInformation values must not be blank") String> missingInformation,

        List<@NotBlank(message = "evidenceLimitations values must not be blank") String> evidenceLimitations,

        List<@NotBlank(message = "severeTriggersObserved values must not be blank") String> severeTriggersObserved
) {
    public ReviewSummaryRequest {
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
}
