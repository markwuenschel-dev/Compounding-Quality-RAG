package com.compoundingquality.reviewapi.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record ReviewSummaryExtractRequest(
        @NotBlank(message = "concernText must not be blank")
        @Size(max = 5_000, message = "concernText must be 5000 characters or fewer")
        String concernText,

        @NotBlank(message = "pharmacistNotes must not be blank")
        @Size(max = 10_000, message = "pharmacistNotes must be 10000 characters or fewer")
        String pharmacistNotes
) {
}
