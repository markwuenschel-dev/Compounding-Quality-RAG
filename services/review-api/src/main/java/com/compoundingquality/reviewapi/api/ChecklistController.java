package com.compoundingquality.reviewapi.api;

import com.compoundingquality.reviewapi.dto.ChecklistRequest;
import com.compoundingquality.reviewapi.dto.ChecklistResponse;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Locale;

@RestController
@RequestMapping("/api/checklist")
public class ChecklistController {

    @PostMapping
    public ResponseEntity<ChecklistResponse> createChecklist(
            @Valid @RequestBody ChecklistRequest request
    ) {
        return ResponseEntity.ok(buildMockChecklist(request.concernText()));
    }

    private ChecklistResponse buildMockChecklist(String concernText) {
        String normalizedConcern = concernText.toLowerCase(Locale.ROOT);
        boolean vomitingConcern = normalizedConcern.contains("vomit");
        boolean flavorConcern = normalizedConcern.contains("flavor");

        String concernType = vomitingConcern && flavorConcern
                ? "flavor_related_vomiting"
                : "compounding_quality_concern";

        String riskLane = vomitingConcern
                ? "unexpected_non_life_threatening"
                : "expected_self_limiting";

        String initialTakeaway = vomitingConcern
                ? "Initial screen suggests a possible flavor-related vomiting concern that requires review before final routing."
                : "Initial screen suggests a compounding-quality concern that requires structured review before final routing.";

        return new ChecklistResponse(
                concernType,
                riskLane,
                "full_quality_review",
                initialTakeaway,
                List.of(
                        new ChecklistResponse.ChecklistItems(
                                "record_review",
                                "Record review",
                                true,
                                "Verify relevant compounding, dispensing, and documentation fields before final disposition."
                        ),
                        new ChecklistResponse.ChecklistItems(
                                "lot_batch_review",
                                "Lot or batch context review",
                                true,
                                "Check whether similar concerns exist for the same lot, batch, medication, dosage form, or concern type when available."
                        ),
                        new ChecklistResponse.ChecklistItems(
                                "inventory_inspection",
                                "Inventory inspection if available",
                                true,
                                "Inspect available inventory when the concern may involve visible product quality, packaging, device, or formulation issues."
                        ),
                        new ChecklistResponse.ChecklistItems(
                                "trend_scan",
                                "Trend scan",
                                true,
                                "Look for repeated similar concerns when enough fields exist to support pattern review."
                        ),
                        new ChecklistResponse.ChecklistItems(
                                "customer_context_follow_up",
                                "Customer clinical context follow-up",
                                vomitingConcern,
                                "Vomiting after administration requires timing, dose, symptom course, veterinarian contact, and severity context before final routing."
                        )
                ),
                List.of(
                        "Medication or product placeholder",
                        "Species",
                        "Dosage form",
                        "Lot or batch information, if available",
                        "Whether any severe escalation trigger is present",
                        "Dose administered",
                        "Timing of concern relative to administration",
                        "Whether symptoms resolved",
                        "Whether veterinarian was contacted",
                        "Whether the pet was hospitalized"
                ),
                List.of(
                        "pet_death",
                        "pet_hospitalization",
                        "threatened_legal_action",
                        "veterinarian_alleges_harm_from_compound",
                        "possible_contamination",
                        "wrong_patient_or_wrong_medication"
                ),
                List.of(
                        new ChecklistResponse.EvidenceCitation(
                                "SOP-002",
                                "Frontline Guidance, Delegate-Back, and Response Rules",
                                "Flavor or Palatability Guidance"
                        ),
                        new ChecklistResponse.EvidenceCitation(
                                "SOP-004",
                                "Customer Context and Administration Review",
                                "Palatability and Flavor Rejection"
                        ),
                        new ChecklistResponse.EvidenceCitation(
                                "SOP-008",
                                "Trend and Pattern Monitoring Rules",
                                "Similar Concern Same Medication and Dosage Form"
                        )
                ),
                List.of(
                        "This mocked endpoint does not call the Python RAG engine yet.",
                        "This output is a review checklist, not a final clinical, legal, or quality disposition.",
                        "The public demo does not access real customer records, patient records, compounding records, inventory, or external drug references.",
                        "Causality should not be inferred from the intake narrative alone."
                )
        );
    }
}