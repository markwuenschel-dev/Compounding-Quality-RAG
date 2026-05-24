package com.compoundingquality.reviewapi.dto;

public record HealthResponse(
    String service,
    String status,
    String timestamp
) {}