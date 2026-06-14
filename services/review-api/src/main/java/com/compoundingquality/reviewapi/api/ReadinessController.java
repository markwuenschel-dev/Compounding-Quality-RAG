package com.compoundingquality.reviewapi.api;

import com.compoundingquality.reviewapi.application.ReadinessService;
import com.compoundingquality.reviewapi.dto.ReadinessResponse;
import java.util.Objects;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class ReadinessController {

    private final ReadinessService readinessService;

    public ReadinessController(ReadinessService readinessService) {
        this.readinessService = Objects.requireNonNull(
                readinessService,
                "readinessService must not be null"
        );
    }

    @GetMapping("/ready")
    public ResponseEntity<ReadinessResponse> readiness() {
        ReadinessResponse response = readinessService.checkReadiness();
        HttpStatus status = ReadinessResponse.READY.equals(response.status())
                ? HttpStatus.OK
                : HttpStatus.SERVICE_UNAVAILABLE;

        return ResponseEntity.status(status).body(response);
    }
}
