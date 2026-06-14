package com.compoundingquality.reviewapi.api;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.compoundingquality.reviewapi.application.ReviewSummaryExtractionService;
import com.compoundingquality.reviewapi.dto.ReviewSummaryExtractRequest;
import com.compoundingquality.reviewapi.dto.ReviewSummaryExtractResponse;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(ReviewSummaryExtractionController.class)
class ReviewSummaryExtractionControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private ReviewSummaryExtractionService extractionService;

    @Test
    void returnsTheStructuredExtraction() throws Exception {
        when(
                extractionService.extract(
                        any(ReviewSummaryExtractRequest.class)
                )
        ).thenReturn(buildResponse());

        mockMvc.perform(
                        post("/api/review-summary/extract")
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("""
                                        {
                                          "concernText": "Dog vomited after the dose.",
                                          "pharmacistNotes": "Worksheet review found no discrepancy."
                                        }
                                        """)
                )
                .andExpect(status().isOk())
                .andExpect(
                        jsonPath(
                                "$.reviewSummary.recordReviewResult"
                        ).value("no_discrepancy_found")
                )
                .andExpect(
                        jsonPath(
                                "$.fieldEvidence[0].supportingQuote"
                        ).value(
                                "Worksheet review found no discrepancy."
                        )
                )
                .andExpect(
                        jsonPath(
                                "$.unresolvedQuestions[0].fieldName"
                        ).value("dose_administered")
                );
    }

    @Test
    void rejectsBlankPharmacistNotes() throws Exception {
        mockMvc.perform(
                        post("/api/review-summary/extract")
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("""
                                        {
                                          "concernText": "Dog vomited.",
                                          "pharmacistNotes": " "
                                        }
                                        """)
                )
                .andExpect(status().isBadRequest())
                .andExpect(
                        jsonPath("$.message")
                                .value("Validation failed")
                );
    }

    private static ReviewSummaryExtractResponse buildResponse() {
        return new ReviewSummaryExtractResponse(
                new ReviewSummaryExtractResponse.ReviewSummary(
                        "no_discrepancy_found",
                        "unavailable",
                        "not_checked",
                        "Dog vomited once.",
                        "not_needed",
                        List.of("Exact dose administered"),
                        List.of(),
                        List.of()
                ),
                List.of(
                        new ReviewSummaryExtractResponse.FieldEvidence(
                                "record_review_result",
                                "normalized",
                                "Worksheet review found no discrepancy.",
                                "Normalized into the enum contract."
                        )
                ),
                List.of(
                        new ReviewSummaryExtractResponse.UnresolvedQuestion(
                                "dose_administered",
                                "What dose was administered?",
                                "Dose context is missing.",
                                List.of("review_scope")
                        )
                )
        );
    }
}
