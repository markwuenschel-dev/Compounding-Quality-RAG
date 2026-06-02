package com.compoundingquality.reviewapi.api;

import com.compoundingquality.reviewapi.dto.ChecklistRequest;
import com.compoundingquality.reviewapi.dto.ChecklistResponse;
import com.compoundingquality.reviewapi.application.ChecklistService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Objects;

@RestController
@RequestMapping("/api/checklist")
public class ChecklistController {

    private final ChecklistService checklistService;

    public ChecklistController(ChecklistService checklistService) {
        this.checklistService = Objects.requireNonNull(
                checklistService,
                "checklistService must not be null"
        );
    }

    @PostMapping
    public ResponseEntity<ChecklistResponse> createChecklist(
            @Valid @RequestBody ChecklistRequest request
    ) {
        return ResponseEntity.ok(checklistService.createChecklist(request));
    }
}