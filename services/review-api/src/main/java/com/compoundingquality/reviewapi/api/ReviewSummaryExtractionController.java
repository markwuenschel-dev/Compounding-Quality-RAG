package com.compoundingquality.reviewapi.api;

import com.compoundingquality.reviewapi.application.ReviewSummaryExtractionService;
import com.compoundingquality.reviewapi.dto.ReviewSummaryExtractRequest;
import com.compoundingquality.reviewapi.dto.ReviewSummaryExtractResponse;
import jakarta.validation.Valid;
import java.util.Objects;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/review-summary/extract")
public class ReviewSummaryExtractionController {

    private final ReviewSummaryExtractionService extractionService;

    public ReviewSummaryExtractionController(
            ReviewSummaryExtractionService extractionService
    ) {
        this.extractionService = Objects.requireNonNull(
                extractionService,
                "extractionService must not be null"
        );
    }

    @PostMapping
    public ResponseEntity<ReviewSummaryExtractResponse> extract(
            @Valid @RequestBody ReviewSummaryExtractRequest request
    ) {
        return ResponseEntity.ok(extractionService.extract(request));
    }
}
