package com.compoundingquality.reviewapi.rag;

public class RagEngineException extends RuntimeException {

    private final String code;

    public RagEngineException(String code, String message) {
        super(message);
        this.code = requireText(code, "code");
    }

    public RagEngineException(String code, String message, Throwable cause) {
        super(message, cause);
        this.code = requireText(code, "code");
    }

    public String code() {
        return code;
    }

    private static String requireText(String value, String fieldName) {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException(fieldName + " must not be blank");
        }

        return value;
    }
}
