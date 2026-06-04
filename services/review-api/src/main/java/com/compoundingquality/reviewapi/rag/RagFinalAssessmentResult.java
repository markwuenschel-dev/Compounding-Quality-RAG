package com.compoundingquality.reviewapi.rag;

import java.util.List;
import java.util.Objects;

public record RagFinalAssessmentResult(
        RawIntake rawIntake,
        ProductContext productContext,
        InvestigationRequirements investigationRequirements,
        RagReviewSummary reviewSummary,
        DerivedAssessment derivedAssessment
) {
    public RagFinalAssessmentResult {
        rawIntake = Objects.requireNonNull(rawIntake, "rawIntake must not be null");
        productContext = Objects.requireNonNull(productContext, "productContext must not be null");
        investigationRequirements = Objects.requireNonNull(
                investigationRequirements,
                "investigationRequirements must not be null"
        );
        reviewSummary = Objects.requireNonNull(reviewSummary, "reviewSummary must not be null");
        derivedAssessment = Objects.requireNonNull(
                derivedAssessment,
                "derivedAssessment must not be null"
        );
    }

    public record RawIntake(
            String intakeSource,
            String submitterRole,
            String submissionPurpose,
            String concernNarrative,
            Integer starRating,
            Boolean reviewTextPresent,
            String submitterSelectedClassification
    ) {
        public RawIntake {
            intakeSource = requireText(intakeSource, "intakeSource");
            submitterRole = requireText(submitterRole, "submitterRole");
            submissionPurpose = requireText(submissionPurpose, "submissionPurpose");
            concernNarrative = requireText(concernNarrative, "concernNarrative");
        }
    }

    public record ProductContext(
            String species,
            String dosageForm,
            String productPlaceholder,
            String flavorOrAttribute,
            Boolean budPresent,
            Boolean batchLotPresent
    ) {
        public ProductContext {
            species = requireText(species, "species");
            dosageForm = requireText(dosageForm, "dosageForm");
        }
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
            reviewerAssignedClassification = requireText(
                    reviewerAssignedClassification,
                    "reviewerAssignedClassification"
            );
            concernType = requireText(concernType, "concernType");
            riskLane = requireText(riskLane, "riskLane");
            reviewScope = requireText(reviewScope, "reviewScope");
            handlingPath = requireText(handlingPath, "handlingPath");
            rationale = requireText(rationale, "rationale");

            escalationTriggers = escalationTriggers == null
                    ? List.of()
                    : List.copyOf(escalationTriggers);

            resolutionOptions = resolutionOptions == null
                    ? List.of()
                    : List.copyOf(resolutionOptions);
        }
    }

    private static String requireText(String value, String fieldName) {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException(fieldName + " must not be blank");
        }

        return value;
    }
}
