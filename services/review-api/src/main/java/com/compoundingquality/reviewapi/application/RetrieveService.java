package com.compoundingquality.reviewapi.application;

import com.compoundingquality.reviewapi.dto.RetrieveRequest;
import com.compoundingquality.reviewapi.dto.RetrieveResponse;
import com.compoundingquality.reviewapi.rag.RagEngineClient;
import com.compoundingquality.reviewapi.rag.RagRetrieveRequest;
import com.compoundingquality.reviewapi.rag.RagRetrieveResult;
import java.util.List;
import java.util.Objects;
import org.springframework.stereotype.Service;

@Service
public class RetrieveService {

    private final RagEngineClient ragEngineClient;

    public RetrieveService(RagEngineClient ragEngineClient) {
        this.ragEngineClient = Objects.requireNonNull(
                ragEngineClient,
                "ragEngineClient must not be null"
        );
    }

    public RetrieveResponse retrieve(RetrieveRequest request) {
        Objects.requireNonNull(request, "request must not be null");

        int topK = request.topK() == null
                ? RagRetrieveRequest.DEFAULT_TOP_K
                : request.topK();

        RagRetrieveResult result = ragEngineClient.retrieve(
                new RagRetrieveRequest(request.queryText(), topK)
        );

        return toResponse(request.queryText(), topK, result);
    }

    private static RetrieveResponse toResponse(
            String queryText,
            int topK,
            RagRetrieveResult result
    ) {
        return new RetrieveResponse(
                queryText,
                topK,
                toEvidenceCitations(result.results())
        );
    }

    private static List<RetrieveResponse.EvidenceCitation> toEvidenceCitations(
            List<RagRetrieveResult.SearchResult> results
    ) {
        return results.stream()
                .map(RetrieveService::toEvidenceCitation)
                .toList();
    }

    private static RetrieveResponse.EvidenceCitation toEvidenceCitation(
            RagRetrieveResult.SearchResult result
    ) {
        RagRetrieveResult.Chunk chunk = result.chunk();

        return new RetrieveResponse.EvidenceCitation(
                chunk == null ? null : chunk.chunkId(),
                chunk == null ? null : chunk.sourceId(),
                chunk == null ? null : chunk.sourceTitle(),
                chunk == null ? null : chunk.sourceType(),
                chunk == null ? null : chunk.sectionHeading(),
                result.score(),
                result.matchedTerms(),
                chunk == null ? null : chunk.text()
        );
    }
}
