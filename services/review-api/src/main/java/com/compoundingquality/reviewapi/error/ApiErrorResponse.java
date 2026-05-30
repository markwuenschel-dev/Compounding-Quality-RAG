package com.compoundingquality.reviewapi.error;

import java.time.Instant;
import java.util.List;

public record ApiErrorResponse(
        Instant timestamp,
        int status,
        String error,
        String message,
        String path,
        String requestId,
        List<FieldErrorDetail> fieldErrors
) {
    public static ApiErrorResponse of(
            int status,
            String error,
            String message,
            String path,
            String requestId,
            List<FieldErrorDetail> fieldErrors
    ) {
        return new ApiErrorResponse(
                Instant.now(),
                status,
                error,
                message,
                path,
                requestId,
                fieldErrors == null ? List.of() : fieldErrors
        );
    }
}