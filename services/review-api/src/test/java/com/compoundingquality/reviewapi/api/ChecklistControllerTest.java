package com.compoundingquality.reviewapi.api;

import static org.hamcrest.Matchers.hasSize;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultHandlers.print;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.List;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import com.compoundingquality.reviewapi.application.ChecklistService;
import com.compoundingquality.reviewapi.config.RequestCorrelationFilter;
import com.compoundingquality.reviewapi.dto.ChecklistRequest;
import com.compoundingquality.reviewapi.dto.ChecklistResponse;
import com.compoundingquality.reviewapi.error.GlobalExceptionHandler;

@WebMvcTest(ChecklistController.class)
@Import({GlobalExceptionHandler.class, RequestCorrelationFilter.class})
public class ChecklistControllerTest {
        @Autowired
        private MockMvc mockMvc;

        @MockitoBean
        private ChecklistService checklistService;

        @Test
        void createChecklistReturnsChecklistFromService() throws Exception {
                when(checklistService.createChecklist(any(ChecklistRequest.class)))
                                .thenReturn(sampleResponse());

                mockMvc.perform(post("/api/checklist")
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("""
                                                {
                                                "concernText": "My dog vomited after taking a flavored compounded oral liquid."
                                                }
                                                """))
                                .andExpect(status().isOk())
                                .andExpect(jsonPath("$.concernType").value("flavor_related_vomiting"))
                                .andExpect(jsonPath("$.riskLane").value("unexpected_non_life_threatening"))
                                .andExpect(jsonPath("$.reviewScope").value("full_quality_review"))
                                .andExpect(jsonPath("$.initialTakeaway").isNotEmpty())
                                .andExpect(jsonPath("$.requiredChecks", hasSize(1)))
                                .andExpect(jsonPath("$.requiredChecks[0].key").value("record_review"))
                                .andExpect(jsonPath("$.requiredChecks[0].required").value(true))
                                .andExpect(jsonPath("$.missingInformation").isArray())
                                .andExpect(jsonPath("$.escalationTriggersToRuleOut").isArray())
                                .andExpect(jsonPath("$.evidence").isArray())
                                .andExpect(jsonPath("$.evidence[0].sourceId").value("SOP-001"))
                                .andExpect(jsonPath("$.limitations").isArray());

                verify(checklistService).createChecklist(any(ChecklistRequest.class));
        }

        @Test
        void createChecklistRejectsBlankConcernTextWithGlobalErrorShape() throws Exception {
                mockMvc.perform(post("/api/checklist")
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("""
                                                {
                                                  "concernText": "   "
                                                }
                                                """))
                                .andDo(print())
                                .andExpect(status().isBadRequest())
                                .andExpect(jsonPath("$.status").value(400))
                                .andExpect(jsonPath("$.error").value("Bad Request"))
                                .andExpect(jsonPath("$.message").value("Validation failed"))
                                .andExpect(jsonPath("$.path").value("/api/checklist"))
                                .andExpect(jsonPath("$.requestId").isNotEmpty())
                                .andExpect(jsonPath("$.fieldErrors").isArray())
                                .andExpect(jsonPath("$.fieldErrors[0].field").value("concernText"))
                                .andExpect(jsonPath("$.fieldErrors[0].message").value("concernText must not be blank"));
        }

        @Test
        void createChecklistPreservesIncomingRequestIdOnValidationFailure() throws Exception {
                mockMvc.perform(post("/api/checklist")
                                .header("X-Request-Id", "test-request-id-123")
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("""
                                                {
                                                  "concernText": ""
                                                }
                                                """))
                                .andDo(print())
                                .andExpect(status().isBadRequest())
                                .andExpect(jsonPath("$.requestId").value("test-request-id-123"));
        }

        private static ChecklistResponse sampleResponse() {
                return new ChecklistResponse(
                                "flavor_related_vomiting",
                                "unexpected_non_life_threatening",
                                "full_quality_review",
                                "Initial screen suggests review is needed.",
                                List.of(
                                                new ChecklistResponse.ChecklistItem(
                                                                "record_review",
                                                                "Record review",
                                                                true,
                                                                "Verify relevant fields before final disposition.")),
                                List.of("Dose administered"),
                                List.of("pet_hospitalization"),
                                List.of(
                                                new ChecklistResponse.EvidenceCitation(
                                                                "SOP-001",
                                                                "Sample SOP",
                                                                "Sample Section")),
                                List.of("Checklist output is preliminary."));
        }
}