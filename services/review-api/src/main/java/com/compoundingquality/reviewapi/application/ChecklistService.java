package com.compoundingquality.reviewapi.application;

import com.compoundingquality.reviewapi.dto.ChecklistRequest;
import com.compoundingquality.reviewapi.dto.ChecklistResponse;
import com.compoundingquality.reviewapi.rag.RagChecklistRequest;
import com.compoundingquality.reviewapi.rag.RagChecklistResult;
import com.compoundingquality.reviewapi.rag.RagEngineClient;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Locale;
import java.util.Objects;

@Service
public class ChecklistService {

    private static final String UNKNOWN = "unknown";

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
                new RagChecklistRequest(
                        request.concernText(),
                        request.resolvedTopK()
                )
        );

        return toResponse(result);
    }

    private static ChecklistResponse toResponse(RagChecklistResult result) {
        String concernType = valueOrUnknown(result.likelyConcernType());
        String riskLane = valueOrUnknown(result.likelyRiskLane());

        return new ChecklistResponse(
                concernType,
                riskLane,
                deriveReviewScope(result),
                buildInitialTakeaway(concernType, riskLane),
                toChecklistItems(result.reviewChecks()),
                result.missingInformation(),
                result.escalationTriggersToRuleOut(),
                toEvidenceCitations(result.evidence()),
                result.limitations()
        );
    }

    private static List<ChecklistResponse.ChecklistItem> toChecklistItems(
        List<RagChecklistResult.ChecklistItem> items
    ) {
        return items.stream()
                .map(item -> new ChecklistResponse.ChecklistItem(
                        slugify(item.checkName()),
                        item.checkName(),
                        item.required(),
                        item.rationale()
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

    private static String deriveReviewScope(RagChecklistResult result) {
        if ("life_threatening_or_legal".equals(result.likelyRiskLane())) {
            return "escalation_review";
        }

        if ("bud_question".equals(result.likelyConcernType())) {
            return "guidance_only";
        }

        return "full_quality_review";
    }

    private static String buildInitialTakeaway(String concernType, String riskLane) {
        return "Initial screen suggests %s with %s risk lane. Final routing depends on review findings and confirmed escalation triggers."
                .formatted(humanize(concernType), humanize(riskLane));
    }

    private static String valueOrUnknown(String value) {
        if (value == null || value.isBlank()) {
            return UNKNOWN;
        }

        return value;
    }

    private static String humanize(String value) {
        return valueOrUnknown(value).replace("_", " ");
    }

    private static String slugify(String value) {
        String slug = value.toLowerCase(Locale.ROOT)
                .replaceAll("[^a-z0-9]+", "_")
                .replaceAll("^_+|_+$", "");

        return slug.isBlank() ? "check" : slug;
    }
}