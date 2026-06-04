package com.compoundingquality.reviewapi.error;

import com.fasterxml.jackson.annotation.JsonInclude;
import java.time.Instant;
import java.util.List;

@JsonInclude(JsonInclude.Include.NON_NULL)
public record ApiErrorResponse(
        Instant timestamp,
        int status,
        String error,
        String message,
        String path,
        String requestId,
        List<FieldErrorDetail> fieldErrors,
        String code
) {
    public ApiErrorResponse(
            Instant timestamp,
            int status,
            String error,
            String message,
            String path,
            String requestId,
            List<FieldErrorDetail> fieldErrors
    ) {
        this(
                timestamp,
                status,
                error,
                message,
                path,
                requestId,
                fieldErrors,
                null
        );
    }

    public static ApiErrorResponse of(
            int status,
            String error,
            String message,
            String path,
            String requestId,
            List<FieldErrorDetail> fieldErrors
    ) {
        return of(
                status,
                error,
                message,
                path,
                requestId,
                fieldErrors,
                null
        );
    }

    public static ApiErrorResponse of(
            int status,
            String error,
            String message,
            String path,
            String requestId,
            List<FieldErrorDetail> fieldErrors,
            String code
    ) {
        return new ApiErrorResponse(
                Instant.now(),
                status,
                error,
                message,
                path,
                requestId,
                fieldErrors == null ? List.of() : List.copyOf(fieldErrors),
                code
        );
    }
}
