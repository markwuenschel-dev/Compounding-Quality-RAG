package com.compoundingquality.reviewapi.application;

import com.compoundingquality.reviewapi.dto.ReviewSummaryExtractRequest;
import com.compoundingquality.reviewapi.dto.ReviewSummaryExtractResponse;
import com.compoundingquality.reviewapi.rag.RagEngineClient;
import com.compoundingquality.reviewapi.rag.RagReviewSummary;
import com.compoundingquality.reviewapi.rag.RagReviewSummaryExtractRequest;
import com.compoundingquality.reviewapi.rag.RagReviewSummaryExtractResult;
import java.util.Objects;
import org.springframework.stereotype.Service;

@Service
public class ReviewSummaryExtractionService {

    private final RagEngineClient ragEngineClient;

    public ReviewSummaryExtractionService(
            RagEngineClient ragEngineClient
    ) {
        this.ragEngineClient = Objects.requireNonNull(
                ragEngineClient,
                "ragEngineClient must not be null"
        );
    }

    public ReviewSummaryExtractResponse extract(
            ReviewSummaryExtractRequest request
    ) {
        Objects.requireNonNull(request, "request must not be null");

        RagReviewSummaryExtractResult result =
                ragEngineClient.extractReviewSummary(
                        new RagReviewSummaryExtractRequest(
                                request.concernText(),
                                request.pharmacistNotes()
                        )
                );

        return toResponse(result);
    }

    private static ReviewSummaryExtractResponse toResponse(
            RagReviewSummaryExtractResult result
    ) {
        return new ReviewSummaryExtractResponse(
                toReviewSummary(result.reviewSummary()),
                result.fieldEvidence()
                        .stream()
                        .map(ReviewSummaryExtractionService::toFieldEvidence)
                        .toList(),
                result.unresolvedQuestions()
                        .stream()
                        .map(ReviewSummaryExtractionService::toUnresolvedQuestion)
                        .toList()
        );
    }

    private static ReviewSummaryExtractResponse.ReviewSummary toReviewSummary(
            RagReviewSummary summary
    ) {
        return new ReviewSummaryExtractResponse.ReviewSummary(
                summary.recordReviewResult(),
                summary.lotBatchPatternSummary(),
                summary.inventoryInspectionResult(),
                summary.customerContextSummary(),
                summary.apiReferenceReviewResult(),
                summary.missingInformation(),
                summary.evidenceLimitations(),
                summary.severeTriggersObserved()
        );
    }

    private static ReviewSummaryExtractResponse.FieldEvidence toFieldEvidence(
            RagReviewSummaryExtractResult.FieldEvidence evidence
    ) {
        return new ReviewSummaryExtractResponse.FieldEvidence(
                evidence.fieldName(),
                evidence.status(),
                evidence.supportingQuote(),
                evidence.explanation()
        );
    }

    private static ReviewSummaryExtractResponse.UnresolvedQuestion
            toUnresolvedQuestion(
                    RagReviewSummaryExtractResult.UnresolvedQuestion question
            ) {
        return new ReviewSummaryExtractResponse.UnresolvedQuestion(
                question.fieldName(),
                question.question(),
                question.reason(),
                question.decisionImpact()
        );
    }
}
