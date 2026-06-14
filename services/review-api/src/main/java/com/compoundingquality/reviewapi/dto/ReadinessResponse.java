package com.compoundingquality.reviewapi.dto;

import java.time.Instant;
import java.util.List;
import java.util.Objects;

public record ReadinessResponse(
        String status,
        List<ReadinessCheck> checks,
        Instant timestamp
) {

    public static final String READY = "READY";
    public static final String NOT_READY = "NOT_READY";

    public ReadinessResponse {
        status = Objects.requireNonNull(status, "status must not be null");
        checks = List.copyOf(Objects.requireNonNull(checks, "checks must not be null"));
        timestamp = Objects.requireNonNull(timestamp, "timestamp must not be null");
    }

    public record ReadinessCheck(
            String name,
            String status,
            String detail
    ) {

        public static final String UP = "UP";
        public static final String DOWN = "DOWN";

        public ReadinessCheck {
            name = Objects.requireNonNull(name, "name must not be null");
            status = Objects.requireNonNull(status, "status must not be null");
            detail = Objects.requireNonNull(detail, "detail must not be null");
        }

        public static ReadinessCheck up(String name, String detail) {
            return new ReadinessCheck(name, UP, detail);
        }

        public static ReadinessCheck down(String name, String detail) {
            return new ReadinessCheck(name, DOWN, detail);
        }

        public boolean available() {
            return UP.equals(status);
        }
    }
}
