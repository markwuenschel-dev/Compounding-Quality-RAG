package com.compoundingquality.reviewapi.error;

import com.compoundingquality.reviewapi.rag.RagEngineException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.ConstraintViolationException;
import java.util.List;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.ErrorResponseException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.server.ResponseStatusException;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiErrorResponse> handleMethodArgumentNotValid(
            MethodArgumentNotValidException exception,
            HttpServletRequest request
    ) {
        List<FieldErrorDetail> fieldErrors = exception.getBindingResult()
                .getFieldErrors()
                .stream()
                .map(error -> new FieldErrorDetail(
                        error.getField(),
                        rejectedValue(error.getRejectedValue()),
                        error.getDefaultMessage()
                ))
                .toList();

        return buildResponse(
                HttpStatus.BAD_REQUEST,
                "Validation failed",
                request,
                fieldErrors
        );
    }

    @ExceptionHandler(ConstraintViolationException.class)
    public ResponseEntity<ApiErrorResponse> handleConstraintViolation(
            ConstraintViolationException exception,
            HttpServletRequest request
    ) {
        List<FieldErrorDetail> fieldErrors = exception.getConstraintViolations()
                .stream()
                .map(violation -> new FieldErrorDetail(
                        violation.getPropertyPath().toString(),
                        null,
                        violation.getMessage()
                ))
                .toList();

        return buildResponse(
                HttpStatus.BAD_REQUEST,
                "Validation failed",
                request,
                fieldErrors
        );
    }

    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ResponseEntity<ApiErrorResponse> handleUnreadableMessage(
            HttpMessageNotReadableException exception,
            HttpServletRequest request
    ) {
        return buildResponse(
                HttpStatus.BAD_REQUEST,
                "Malformed request body",
                request,
                List.of()
        );
    }

    @ExceptionHandler(RagEngineException.class)
    public ResponseEntity<ApiErrorResponse> handleRagEngineException(
            RagEngineException exception,
            HttpServletRequest request
    ) {
        return buildResponse(
                statusForRagEngineCode(exception.code()),
                exception.getMessage(),
                exception.code(),
                request,
                List.of()
        );
    }

    @ExceptionHandler(ResponseStatusException.class)
    public ResponseEntity<ApiErrorResponse> handleResponseStatus(
            ResponseStatusException exception,
            HttpServletRequest request
    ) {
        HttpStatusCode statusCode = exception.getStatusCode();
        String message = exception.getReason() == null
                ? "Request failed"
                : exception.getReason();

        return buildResponse(statusCode, message, request, List.of());
    }

    @ExceptionHandler(ErrorResponseException.class)
    public ResponseEntity<ApiErrorResponse> handleErrorResponse(
            ErrorResponseException exception,
            HttpServletRequest request
    ) {
        return buildResponse(
                exception.getStatusCode(),
                exception.getBody().getDetail(),
                request,
                List.of()
        );
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiErrorResponse> handleUnexpected(
            Exception exception,
            HttpServletRequest request
    ) {
        return buildResponse(
                HttpStatus.INTERNAL_SERVER_ERROR,
                "Unexpected server error",
                request,
                List.of()
        );
    }

    private HttpStatus statusForRagEngineCode(String code) {
        return switch (code) {
            case "INVALID_REQUEST", "REFUSED" -> HttpStatus.UNPROCESSABLE_CONTENT;
            case "ENGINE_TIMEOUT" -> HttpStatus.GATEWAY_TIMEOUT;
            case "ENGINE_INTERRUPTED" -> HttpStatus.SERVICE_UNAVAILABLE;
            case "ENGINE_REQUEST_ENCODING" -> HttpStatus.INTERNAL_SERVER_ERROR;
            case "ENGINE_PROCESS_START",
                    "ENGINE_PROCESS_EXIT",
                    "ENGINE_INVALID_STDOUT",
                    "ENGINE_INVALID_RESPONSE",
                    "ENGINE_RESPONSE_MAPPING",
                    "ENGINE_FAILURE" -> HttpStatus.BAD_GATEWAY;
            default -> HttpStatus.BAD_GATEWAY;
        };
    }

    private ResponseEntity<ApiErrorResponse> buildResponse(
            HttpStatusCode statusCode,
            String message,
            HttpServletRequest request,
            List<FieldErrorDetail> fieldErrors
    ) {
        return buildResponse(
                statusCode,
                message,
                null,
                request,
                fieldErrors
        );
    }

    private ResponseEntity<ApiErrorResponse> buildResponse(
            HttpStatusCode statusCode,
            String message,
            String code,
            HttpServletRequest request,
            List<FieldErrorDetail> fieldErrors
    ) {
        int status = statusCode.value();

        ApiErrorResponse response = ApiErrorResponse.of(
                status,
                reasonPhrase(statusCode),
                message,
                request.getRequestURI(),
                requestId(request),
                fieldErrors,
                code
        );

        return ResponseEntity.status(statusCode).body(response);
    }

    private String reasonPhrase(HttpStatusCode statusCode) {
        if (statusCode instanceof HttpStatus httpStatus) {
            return httpStatus.getReasonPhrase();
        }

        return "HTTP " + statusCode.value();
    }

    private String requestId(HttpServletRequest request) {
        String requestId = request.getHeader("X-Request-Id");

        return requestId == null || requestId.isBlank()
                ? UUID.randomUUID().toString()
                : requestId;
    }

    private String rejectedValue(Object value) {
        return value == null ? null : value.toString();
    }
}
