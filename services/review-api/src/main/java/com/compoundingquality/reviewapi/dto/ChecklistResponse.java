package com.compoundingquality.reviewapi.dto;

import java.util.List;

public record ChecklistResponse(
        String concernType,
        String riskLane,
        String reviewScope,
        String initialTakeaway,
        List<ChecklistItems> requiredChecks,
        List<String> missingInformation,
        List<String> escalationTriggersToRuleOut,
        List<EvidenceCitation> evidence,
        List<String> limitations) {
    public ChecklistResponse {
        requiredChecks = requiredChecks == null ? List.of() : List.copyOf(requiredChecks);
        missingInformation = missingInformation == null ? List.of() : List.copyOf(missingInformation);
        escalationTriggersToRuleOut = escalationTriggersToRuleOut == null ? List.of()
                : List.copyOf(escalationTriggersToRuleOut);
        evidence = evidence == null ? List.of() : List.copyOf(evidence);
        limitations = limitations == null ? List.of() : List.copyOf(limitations);
    }

    public record ChecklistItems(
            String key,
            String label,
            boolean required,
            String reason) {
    }

    public record EvidenceCitation(
            String sourceId,
            String sourceTitle,
            String sectionHeading) {
    }
}
