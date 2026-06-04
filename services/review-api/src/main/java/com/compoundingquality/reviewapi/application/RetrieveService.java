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

        return toResponse(result);
    }

    private static RetrieveResponse toResponse(RagRetrieveResult result) {
        return new RetrieveResponse(
                result.queryText(),
                result.topK(),
                toEvidenceCitations(result.evidence())
        );
    }

    private static List<RetrieveResponse.EvidenceCitation> toEvidenceCitations(
            List<RagRetrieveResult.EvidenceCitation> citations
    ) {
        return citations.stream()
                .map(citation -> new RetrieveResponse.EvidenceCitation(
                        citation.chunkId(),
                        citation.sourceId(),
                        citation.sourceTitle(),
                        citation.sourceType(),
                        citation.sectionHeading(),
                        citation.score(),
                        citation.matchedTerms(),
                        citation.supportingText()
                ))
                .toList();
    }
}
