package com.compoundingquality.reviewapi.application;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.compoundingquality.reviewapi.dto.ReviewSummaryExtractRequest;
import com.compoundingquality.reviewapi.rag.RagEngineClient;
import com.compoundingquality.reviewapi.rag.RagReviewSummary;
import com.compoundingquality.reviewapi.rag.RagReviewSummaryExtractRequest;
import com.compoundingquality.reviewapi.rag.RagReviewSummaryExtractResult;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;

class ReviewSummaryExtractionServiceTest {

    @Test
    void mapsThePythonExtractionResultToThePublicResponse() {
        RagEngineClient ragEngineClient = mock(RagEngineClient.class);
        when(
                ragEngineClient.extractReviewSummary(
                        any(RagReviewSummaryExtractRequest.class)
                )
        ).thenReturn(buildResult());

        ReviewSummaryExtractionService service =
                new ReviewSummaryExtractionService(ragEngineClient);

        var response = service.extract(
                new ReviewSummaryExtractRequest(
                        "Dog vomited after the dose.",
                        "Worksheet review found no discrepancy."
                )
        );

        assertThat(
                response.reviewSummary().recordReviewResult()
        ).isEqualTo("no_discrepancy_found");
        assertThat(response.fieldEvidence()).hasSize(1);
        assertThat(response.unresolvedQuestions()).hasSize(1);

        ArgumentCaptor<RagReviewSummaryExtractRequest> captor =
                ArgumentCaptor.forClass(
                        RagReviewSummaryExtractRequest.class
                );
        verify(ragEngineClient).extractReviewSummary(captor.capture());

        assertThat(captor.getValue().concernText())
                .isEqualTo("Dog vomited after the dose.");
        assertThat(captor.getValue().pharmacistNotes())
                .isEqualTo("Worksheet review found no discrepancy.");
    }

    private static RagReviewSummaryExtractResult buildResult() {
        return new RagReviewSummaryExtractResult(
                new RagReviewSummary(
                        "no_discrepancy_found",
                        "unavailable",
                        "not_checked",
                        "Dog vomited once.",
                        "not_needed",
                        List.of("Exact dose administered"),
                        List.of("Inventory was not inspected."),
                        List.of()
                ),
                List.of(
                        new RagReviewSummaryExtractResult.FieldEvidence(
                                "record_review_result",
                                "normalized",
                                "Worksheet review found no discrepancy.",
                                "Normalized into the enum contract."
                        )
                ),
                List.of(
                        new RagReviewSummaryExtractResult.UnresolvedQuestion(
                                "dose_administered",
                                "What dose was administered?",
                                "Dose context is missing.",
                                List.of("review_scope")
                        )
                )
        );
    }
}
