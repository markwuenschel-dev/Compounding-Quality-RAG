package com.compoundingquality.reviewapi.dto;

import java.util.List;

public record RetrieveResponse(
        String queryText,
        int topK,
        List<EvidenceCitation> evidence
) {
    public RetrieveResponse {
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
            matchedTerms = matchedTerms == null ? List.of() : List.copyOf(matchedTerms);
        }
    }
}
