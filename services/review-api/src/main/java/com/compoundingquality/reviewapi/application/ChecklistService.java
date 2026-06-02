package com.compoundingquality.reviewapi.application;

import com.compoundingquality.reviewapi.dto.ChecklistRequest;
import com.compoundingquality.reviewapi.dto.ChecklistResponse;
import com.compoundingquality.reviewapi.rag.RagChecklistRequest;
import com.compoundingquality.reviewapi.rag.RagChecklistResult;
import com.compoundingquality.reviewapi.rag.RagEngineClient;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Objects;

@Service
public class ChecklistService {

    private final RagEngineClient ragEngineClient;

    public ChecklistService(RagEngineClient ragEngineClient) {
        this.ragEngineClient = Objects.requireNonNull(
                ragEngineClient,
                "ragEngineClient must not be null"
        );
    }

    public ChecklistResponse createChecklist(ChecklistRequest request) {
        Objects.requireNonNull(request, "request must not be null");

        RagChecklistResult result = ragEngineClient.createChecklist(
                RagChecklistRequest.fromConcernText(request.concernText())
        );

        return toResponse(result);
    }

    private static ChecklistResponse toResponse(RagChecklistResult result) {
        return new ChecklistResponse(
                result.concernType(),
                result.riskLane(),
                result.reviewScope(),
                result.initialTakeaway(),
                toChecklistItem(result.requiredChecks()),
                result.missingInformation(),
                result.escalationTriggersToRuleOut(),
                toEvidenceCitations(result.evidence()),
                result.limitations()
        );
    }

    private static List<ChecklistResponse.ChecklistItem> toChecklistItem(
            List<RagChecklistResult.ChecklistItem> items
    ) {
        return items.stream()
                .map(item -> new ChecklistResponse.ChecklistItem(
                        item.key(),
                        item.label(),
                        item.required(),
                        item.reason()
                ))
                .toList();
    }

    private static List<ChecklistResponse.EvidenceCitation> toEvidenceCitations(
            List<RagChecklistResult.EvidenceCitation> citations
    ) {
        return citations.stream()
                .map(citation -> new ChecklistResponse.EvidenceCitation(
                        citation.sourceId(),
                        citation.sourceTitle(),
                        citation.sectionHeading()
                ))
                .toList();
    }
}