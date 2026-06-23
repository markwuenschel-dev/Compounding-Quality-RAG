package com.compoundingquality.reviewapi.application;

import com.compoundingquality.reviewapi.dto.ChecklistRequest;
import com.compoundingquality.reviewapi.dto.ChecklistResponse;
import com.compoundingquality.reviewapi.rag.RagChecklistRequest;
import com.compoundingquality.reviewapi.rag.RagChecklistResult;
import com.compoundingquality.reviewapi.rag.RagEngineClient;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.*;

class ChecklistServiceTest {

    @Test
    void createChecklistSendsDefaultTopKToRagEngine() {
        RagEngineClient ragEngineClient = mock(RagEngineClient.class);
        when(ragEngineClient.createChecklist(any())).thenReturn(sampleRagResult());

        ChecklistService service = new ChecklistService(ragEngineClient);

        service.createChecklist(
                new ChecklistRequest("My dog vomited after a flavored oral liquid.", null)
        );

        ArgumentCaptor<RagChecklistRequest> captor = ArgumentCaptor.forClass(
                RagChecklistRequest.class
        );

        verify(ragEngineClient).createChecklist(captor.capture());

        assertEquals(
                "My dog vomited after a flavored oral liquid.",
                captor.getValue().concernText()
        );
        assertEquals(RagChecklistRequest.DEFAULT_TOP_K, captor.getValue().topK());
    }

    @Test
    void createChecklistMapsCoreClassificationFieldsFromRagResult() {
        RagEngineClient ragEngineClient = mock(RagEngineClient.class);
        when(ragEngineClient.createChecklist(any())).thenReturn(sampleRagResult());

        ChecklistService service = new ChecklistService(ragEngineClient);

        ChecklistResponse response = service.createChecklist(
                new ChecklistRequest("My dog vomited after a flavored oral liquid.", null)
        );

        assertEquals("flavor_related_vomiting", response.concernType());
        assertEquals("unexpected_non_life_threatening", response.riskLane());
        assertEquals("full_quality_review", response.reviewScope());
        assertEquals(
                "Initial screen suggests flavor related vomiting with unexpected non life threatening risk lane. Final routing depends on review findings and confirmed escalation triggers.",
                response.initialTakeaway()
        );
    }

    @Test
    void createChecklistMapsChecklistItems() {
        RagEngineClient ragEngineClient = mock(RagEngineClient.class);
        when(ragEngineClient.createChecklist(any())).thenReturn(sampleRagResult());

        ChecklistService service = new ChecklistService(ragEngineClient);

        ChecklistResponse response = service.createChecklist(
                new ChecklistRequest("My dog vomited after a flavored oral liquid.", null)
        );

        assertEquals(1, response.requiredChecks().size());

        ChecklistResponse.ChecklistItem item = response.requiredChecks().get(0);

        assertEquals("record_review", item.key());
        assertEquals("Record review", item.label());
        assertEquals(true, item.required());
        assertEquals("Verify relevant fields before final disposition.", item.reason());
    }

    @Test
    void createChecklistMapsEvidenceCitationFields() {
        RagEngineClient ragEngineClient = mock(RagEngineClient.class);
        when(ragEngineClient.createChecklist(any())).thenReturn(sampleRagResult());

        ChecklistService service = new ChecklistService(ragEngineClient);

        ChecklistResponse response = service.createChecklist(
                new ChecklistRequest("My dog vomited after a flavored oral liquid.", null)
        );

        assertEquals(1, response.evidence().size());

        ChecklistResponse.EvidenceCitation citation = response.evidence().get(0);

        assertEquals("SOP-001", citation.sourceId());
        assertEquals("Sample SOP", citation.sourceTitle());
        assertEquals("Sample Section", citation.sectionHeading());
    }

    @Test
    void createChecklistMapsCollectionsFromRagResult() {
        RagEngineClient ragEngineClient = mock(RagEngineClient.class);
        when(ragEngineClient.createChecklist(any())).thenReturn(sampleRagResult());

        ChecklistService service = new ChecklistService(ragEngineClient);

        ChecklistResponse response = service.createChecklist(
                new ChecklistRequest("My dog vomited after a flavored oral liquid.", null)
        );

        assertEquals(List.of("Dose administered"), response.missingInformation());
        assertEquals(
                List.of("pet_hospitalization"),
                response.escalationTriggersToRuleOut()
        );
        assertEquals(
                List.of("Checklist output is preliminary."),
                response.limitations()
        );
    }

    private static RagChecklistResult sampleRagResult() {
        return new RagChecklistResult(
                "My dog vomited after a flavored oral liquid.",
                "flavor_related_vomiting",
                "unexpected_non_life_threatening",
                List.of(
                        new RagChecklistResult.ChecklistItem(
                                "Record review",
                                true,
                                "Verify relevant fields before final disposition.",
                                List.of()
                        )
                ),
                List.of("Dose administered"),
                List.of("pet_hospitalization"),
                List.of(
                        new RagChecklistResult.EvidenceCitation(
                                "SOP-001::sample-section",
                                "SOP-001",
                                "Sample SOP",
                                "sop",
                                "Sample Section",
                                7.5,
                                List.of("vomit"),
                                "Sample supporting text."
                        )
                ),
                List.of("Checklist output is preliminary.")
        );
    }
}