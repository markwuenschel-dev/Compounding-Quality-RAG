package com.compoundingquality.reviewapi.api;

import com.compoundingquality.reviewapi.application.FinalAssessmentService;
import com.compoundingquality.reviewapi.dto.FinalAssessmentRequest;
import com.compoundingquality.reviewapi.dto.FinalAssessmentResponse;
import jakarta.validation.Valid;
import java.util.Objects;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/final-assessment")
public class FinalAssessmentController {

    private final FinalAssessmentService finalAssessmentService;

    public FinalAssessmentController(FinalAssessmentService finalAssessmentService) {
        this.finalAssessmentService = Objects.requireNonNull(
                finalAssessmentService,
                "finalAssessmentService must not be null"
        );
    }

    @PostMapping
    public ResponseEntity<FinalAssessmentResponse> createFinalAssessment(
            @Valid @RequestBody FinalAssessmentRequest request
    ) {
        return ResponseEntity.ok(
                finalAssessmentService.createFinalAssessment(request)
        );
    }
}
