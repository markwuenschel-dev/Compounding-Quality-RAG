package com.compoundingquality.reviewapi.api;

import com.compoundingquality.reviewapi.application.RetrieveService;
import com.compoundingquality.reviewapi.dto.RetrieveRequest;
import com.compoundingquality.reviewapi.dto.RetrieveResponse;
import jakarta.validation.Valid;
import java.util.Objects;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/retrieve")
public class RetrieveController {

    private final RetrieveService retrieveService;

    public RetrieveController(RetrieveService retrieveService) {
        this.retrieveService = Objects.requireNonNull(
                retrieveService,
                "retrieveService must not be null"
        );
    }

    @PostMapping
    public ResponseEntity<RetrieveResponse> retrieve(
            @Valid @RequestBody RetrieveRequest request
    ) {
        return ResponseEntity.ok(retrieveService.retrieve(request));
    }
}
