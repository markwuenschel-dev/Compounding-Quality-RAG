package com.compoundingquality.reviewapi.rag;

import java.util.List;

public record RagRetrieveResult(
        String queryText,
        int topK,
        List<EvidenceCitation> evidence
) {
    public RagRetrieveResult {
        queryText = requireText(queryText, "queryText");

        if (topK < 1) {
            throw new IllegalArgumentException("topK must be at least 1");
        }

        evidence = evidence == null ? List.of() : List.copyOf(evidence);
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
            supportingText = requireText(supportingText, "supportingText");
        }
    }

    private static String requireText(String value, String fieldName) {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException(fieldName + " must not be blank");
        }

        return value;
    }
}
