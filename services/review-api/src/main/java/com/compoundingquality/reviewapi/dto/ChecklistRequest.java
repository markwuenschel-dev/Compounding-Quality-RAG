package com.compoundingquality.reviewapi.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record ChecklistRequest(
        @NotBlank(message = "concernText must not be blank") @Size(max = 5_000, message = "concernText must be 5000 characters or fewer") String concernText) {
}