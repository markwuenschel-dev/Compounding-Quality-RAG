package com.compoundingquality.reviewapi.api;

import java.time.Instant;
// import java.util.Map;
import com.compoundingquality.reviewapi.dto.HealthResponse;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
// import org.springframework.web.bind.annotation.RequestParam;


@RestController
public class HealthController {

    @GetMapping("/health")
    public HealthResponse health() {
        return new HealthResponse(
            "review-api",
            "UP",
            Instant.now().toString()
        );
    }
        
}
