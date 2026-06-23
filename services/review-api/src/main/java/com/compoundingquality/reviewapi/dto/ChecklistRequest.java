package com.compoundingquality.reviewapi.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record ChecklistRequest(
        @NotBlank(message = "concernText must not be blank")
        @Size(max = 5_000, message = "concernText must be 5000 characters or fewer")
        String concernText,

        @Min(value = 1, message = "topK must be at least 1")
        @Max(value = 20, message = "topK must be 20 or fewer")
        Integer topK
) {
    public static final int DEFAULT_TOP_K = 5;

    public int resolvedTopK() {
        return topK == null ? DEFAULT_TOP_K : topK;
    }
}