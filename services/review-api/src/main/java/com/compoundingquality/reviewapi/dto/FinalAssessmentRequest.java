package com.compoundingquality.reviewapi.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record FinalAssessmentRequest(
        @NotBlank(message = "concernText must not be blank")
        @Size(max = 5_000, message = "concernText must be 5000 characters or fewer")
        String concernText,

        @Min(value = 1, message = "topK must be at least 1")
        Integer topK,

        @NotNull(message = "reviewSummary must not be null")
        @Valid
        ReviewSummaryRequest reviewSummary
) {
}
