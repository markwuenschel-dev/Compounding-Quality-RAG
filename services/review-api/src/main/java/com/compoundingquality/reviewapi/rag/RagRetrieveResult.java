package com.compoundingquality.reviewapi.rag;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import java.util.List;

/**
 * Mirrors the Python RAG engine {@code /retrieve} response shape
 * ({@code {"query": ..., "results": [{"chunk": {...}, "score": ..., "matched_terms": [...]}]}}).
 * The engine returns the full chunk payload, so unknown chunk metadata is ignored.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public record RagRetrieveResult(
        String query,
        List<SearchResult> results
) {
    public RagRetrieveResult {
        results = results == null ? List.of() : List.copyOf(results);
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record SearchResult(
            Chunk chunk,
            Double score,
            List<String> matchedTerms
    ) {
        public SearchResult {
            matchedTerms = matchedTerms == null ? List.of() : List.copyOf(matchedTerms);
        }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record Chunk(
            String chunkId,
            String sourceId,
            String sourceTitle,
            String sourceType,
            String sectionHeading,
            String text
    ) {
    }
}
