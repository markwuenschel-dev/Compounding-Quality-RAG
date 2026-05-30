package com.compoundingquality.reviewapi.error;

public record FieldErrorDetail(
        String field,
        String rejectedValue,
        String message
) {
}