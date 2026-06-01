package com.compoundingquality.reviewapi.rag;

import java.util.List;

public record RagChecklistResult(
        String concernType,
        String riskLane,
        String reviewScope,
        String initialTakeaway,
        List<ChecklistItem> requiredChecks,
        List<String> missingInformation,
        List<String> escalationTriggersToRuleOut,
        List<EvidenceCitation> evidence,
        List<String> limitations
) {
    public RagChecklistResult {
        concernType = requireText(concernType, "concernType");
        riskLane = requireText(riskLane, "riskLane");
        reviewScope = requireText(reviewScope, "reviewScope");
        initialTakeaway = requireText(initialTakeaway, "initialTakeaway");

        requiredChecks = requiredChecks == null ? List.of() : List.copyOf(requiredChecks);
        missingInformation = missingInformation == null ? List.of() : List.copyOf(missingInformation);
        escalationTriggersToRuleOut = escalationTriggersToRuleOut == null
                ? List.of()
                : List.copyOf(escalationTriggersToRuleOut);
        evidence = evidence == null ? List.of() : List.copyOf(evidence);
        limitations = limitations == null ? List.of() : List.copyOf(limitations);
    }

    public record ChecklistItem(
            String key,
            String label,
            boolean required,
            String reason
    ) {
        public ChecklistItem {
            key = requireText(key, "key");
            label = requireText(label, "label");
            reason = requireText(reason, "reason");
        }
    }

    public record EvidenceCitation(
            String chunkId,
            String sourceId,
            String sourceTitle,
            String sourceType,
            String sectionHeading,
            Double score,
            List<String> matchedTerms,
            String supportingText
    ) {
        public EvidenceCitation {
            chunkId = requireText(chunkId, "chunkId");
            sourceId = requireText(sourceId, "sourceId");
            sourceTitle = requireText(sourceTitle, "sourceTitle");
            sourceType = requireText(sourceType, "sourceType");
            sectionHeading = requireText(sectionHeading, "sectionHeading");

            matchedTerms = matchedTerms == null ? List.of() : List.copyOf(matchedTerms);
            supportingText = supportingText == null ? "" : supportingText;
        }
    }

    private static String requireText(String value, String fieldName) {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException(fieldName + " must not be blank");
        }

        return value;
    }
}
