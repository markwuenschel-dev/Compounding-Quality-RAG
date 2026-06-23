package com.compoundingquality.reviewapi.rag;

import java.net.URI;
import java.util.Objects;

public record HttpRagEngineProperties(
        URI baseUrl
) {
    public HttpRagEngineProperties {
        Objects.requireNonNull(baseUrl, "baseUrl must not be null");

        String scheme = baseUrl.getScheme();

        if (!"http".equals(scheme) && !"https".equals(scheme)) {
            throw new IllegalArgumentException("baseUrl must use http or https");
        }
    }
}