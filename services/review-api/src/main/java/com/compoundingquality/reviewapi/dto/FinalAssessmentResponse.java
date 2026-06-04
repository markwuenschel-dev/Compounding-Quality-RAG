package com.compoundingquality.reviewapi.dto;

import java.util.List;

public record FinalAssessmentResponse(
        RawIntake rawIntake,
        ProductContext productContext,
        InvestigationRequirements investigationRequirements,
        ReviewSummary reviewSummary,
        DerivedAssessment derivedAssessment
) {
    public record RawIntake(
            String intakeSource,
            String submitterRole,
            String submissionPurpose,
            String concernNarrative,
            Integer starRating,
            Boolean reviewTextPresent,
            String submitterSelectedClassification
    ) {
    }

    public record ProductContext(
            String species,
            String dosageForm,
            String productPlaceholder,
            String flavorOrAttribute,
            Boolean budPresent,
            Boolean batchLotPresent
    ) {
    }

    public record InvestigationRequirements(
            Boolean recordReviewRequired,
            Boolean lotBatchReviewRequired,
            Boolean inventoryInspectionRequired,
            Boolean trendScanRequired,
            Boolean customerOutreachRequired,
            Boolean frontlineGuidanceLookupRequired,
            Boolean technicalServicesResponseRequired
    ) {
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

    public record DerivedAssessment(
            String reviewerAssignedClassification,
            String reviewerAssignedCategory,
            String reviewerAssignedSubcategory,
            String concernType,
            String riskLane,
            String reviewScope,
            List<String> escalationTriggers,
            String handlingPath,
            boolean resolutionReviewRequired,
            List<String> resolutionOptions,
            String rationale
    ) {
        public DerivedAssessment {
            escalationTriggers = escalationTriggers == null
                    ? List.of()
                    : List.copyOf(escalationTriggers);

            resolutionOptions = resolutionOptions == null
                    ? List.of()
                    : List.copyOf(resolutionOptions);
        }
    }
}
