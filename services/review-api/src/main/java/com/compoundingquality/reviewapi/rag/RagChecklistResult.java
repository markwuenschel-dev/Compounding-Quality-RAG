package com.compoundingquality.reviewapi.rag;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

public record RagChecklistResult(
        @JsonProperty("concern_text")
        String concernText,

        @JsonProperty("likely_concern_type")
        String likelyConcernType,

        @JsonProperty("likely_risk_lane")
        String likelyRiskLane,

        @JsonProperty("review_checks")
        List<ChecklistItem> reviewChecks,

        @JsonProperty("missing_information")
        List<String> missingInformation,

        @JsonProperty("escalation_triggers_to_rule_out")
        List<String> escalationTriggersToRuleOut,

        List<EvidenceCitation> evidence,

        List<String> limitations
) {
    public RagChecklistResult {
        concernText = requireText(concernText, "concernText");
        likelyConcernType = blankToNull(likelyConcernType);
        likelyRiskLane = blankToNull(likelyRiskLane);

        reviewChecks = reviewChecks == null ? List.of() : List.copyOf(reviewChecks);
        missingInformation = missingInformation == null ? List.of() : List.copyOf(missingInformation);
        escalationTriggersToRuleOut = escalationTriggersToRuleOut == null
                ? List.of()
                : List.copyOf(escalationTriggersToRuleOut);
        evidence = evidence == null ? List.of() : List.copyOf(evidence);
        limitations = limitations == null ? List.of() : List.copyOf(limitations);
    }

    public record ChecklistItem(
            @JsonProperty("check_name")
            String checkName,

            boolean required,

            String rationale,

            List<EvidenceCitation> evidence
    ) {
        public ChecklistItem {
            checkName = requireText(checkName, "checkName");
            rationale = requireText(rationale, "rationale");
            evidence = evidence == null ? List.of() : List.copyOf(evidence);
        }
    }

    public record EvidenceCitation(
            @JsonProperty("chunk_id")
            String chunkId,

            @JsonProperty("source_id")
            String sourceId,

            @JsonProperty("source_title")
            String sourceTitle,

            @JsonProperty("source_type")
            String sourceType,

            @JsonProperty("section_heading")
            String sectionHeading,

            Double score,

            @JsonProperty("matched_terms")
            List<String> matchedTerms,

            @JsonProperty("supporting_text")
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

    private static String blankToNull(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }

        return value;
    }
}