package com.compoundingquality.reviewapi.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record RetrieveRequest(
        @NotBlank(message = "queryText must not be blank")
        @Size(max = 5_000, message = "queryText must be 5000 characters or fewer")
        String queryText,

        @Min(value = 1, message = "topK must be at least 1")
        Integer topK
) {
}
