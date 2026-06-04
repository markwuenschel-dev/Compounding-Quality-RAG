package com.compoundingquality.reviewapi.application;

import com.compoundingquality.reviewapi.dto.FinalAssessmentRequest;
import com.compoundingquality.reviewapi.dto.FinalAssessmentResponse;
import com.compoundingquality.reviewapi.dto.ReviewSummaryRequest;
import com.compoundingquality.reviewapi.rag.RagEngineClient;
import com.compoundingquality.reviewapi.rag.RagFinalAssessmentRequest;
import com.compoundingquality.reviewapi.rag.RagFinalAssessmentResult;
import com.compoundingquality.reviewapi.rag.RagReviewSummary;
import java.util.Objects;
import org.springframework.stereotype.Service;

@Service
public class FinalAssessmentService {

    private final RagEngineClient ragEngineClient;

    public FinalAssessmentService(RagEngineClient ragEngineClient) {
        this.ragEngineClient = Objects.requireNonNull(
                ragEngineClient,
                "ragEngineClient must not be null"
        );
    }

    public FinalAssessmentResponse createFinalAssessment(FinalAssessmentRequest request) {
        Objects.requireNonNull(request, "request must not be null");

        int topK = request.topK() == null
                ? RagFinalAssessmentRequest.DEFAULT_TOP_K
                : request.topK();

        RagFinalAssessmentResult result = ragEngineClient.createFinalAssessment(
                new RagFinalAssessmentRequest(
                        request.concernText(),
                        topK,
                        toRagReviewSummary(request.reviewSummary())
                )
        );

        return toResponse(result);
    }

    private static RagReviewSummary toRagReviewSummary(ReviewSummaryRequest request) {
        return new RagReviewSummary(
                request.recordReviewResult(),
                request.lotBatchPatternSummary(),
                request.inventoryInspectionResult(),
                request.customerContextSummary(),
                request.apiReferenceReviewResult(),
                request.missingInformation(),
                request.evidenceLimitations(),
                request.severeTriggersObserved()
        );
    }

    private static FinalAssessmentResponse toResponse(RagFinalAssessmentResult result) {
        return new FinalAssessmentResponse(
                toRawIntake(result.rawIntake()),
                toProductContext(result.productContext()),
                toInvestigationRequirements(result.investigationRequirements()),
                toReviewSummary(result.reviewSummary()),
                toDerivedAssessment(result.derivedAssessment())
        );
    }

    private static FinalAssessmentResponse.RawIntake toRawIntake(
            RagFinalAssessmentResult.RawIntake rawIntake
    ) {
        return new FinalAssessmentResponse.RawIntake(
                rawIntake.intakeSource(),
                rawIntake.submitterRole(),
                rawIntake.submissionPurpose(),
                rawIntake.concernNarrative(),
                rawIntake.starRating(),
                rawIntake.reviewTextPresent(),
                rawIntake.submitterSelectedClassification()
        );
    }

    private static FinalAssessmentResponse.ProductContext toProductContext(
            RagFinalAssessmentResult.ProductContext productContext
    ) {
        return new FinalAssessmentResponse.ProductContext(
                productContext.species(),
                productContext.dosageForm(),
                productContext.productPlaceholder(),
                productContext.flavorOrAttribute(),
                productContext.budPresent(),
                productContext.batchLotPresent()
        );
    }

    private static FinalAssessmentResponse.InvestigationRequirements toInvestigationRequirements(
            RagFinalAssessmentResult.InvestigationRequirements requirements
    ) {
        return new FinalAssessmentResponse.InvestigationRequirements(
                requirements.recordReviewRequired(),
                requirements.lotBatchReviewRequired(),
                requirements.inventoryInspectionRequired(),
                requirements.trendScanRequired(),
                requirements.customerOutreachRequired(),
                requirements.frontlineGuidanceLookupRequired(),
                requirements.technicalServicesResponseRequired()
        );
    }

    private static FinalAssessmentResponse.ReviewSummary toReviewSummary(
            RagReviewSummary reviewSummary
    ) {
        return new FinalAssessmentResponse.ReviewSummary(
                reviewSummary.recordReviewResult(),
                reviewSummary.lotBatchPatternSummary(),
                reviewSummary.inventoryInspectionResult(),
                reviewSummary.customerContextSummary(),
                reviewSummary.apiReferenceReviewResult(),
                reviewSummary.missingInformation(),
                reviewSummary.evidenceLimitations(),
                reviewSummary.severeTriggersObserved()
        );
    }

    private static FinalAssessmentResponse.DerivedAssessment toDerivedAssessment(
            RagFinalAssessmentResult.DerivedAssessment assessment
    ) {
        return new FinalAssessmentResponse.DerivedAssessment(
                assessment.reviewerAssignedClassification(),
                assessment.reviewerAssignedCategory(),
                assessment.reviewerAssignedSubcategory(),
                assessment.concernType(),
                assessment.riskLane(),
                assessment.reviewScope(),
                assessment.escalationTriggers(),
                assessment.handlingPath(),
                assessment.resolutionReviewRequired(),
                assessment.resolutionOptions(),
                assessment.rationale()
        );
    }
}
