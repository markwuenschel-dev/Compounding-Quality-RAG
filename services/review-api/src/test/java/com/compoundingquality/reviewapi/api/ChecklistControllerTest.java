package com.compoundingquality.reviewapi.api;

import com.compoundingquality.reviewapi.error.GlobalExceptionHandler;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import static org.springframework.test.web.servlet.result.MockMvcResultHandlers.print;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.hamcrest.Matchers.hasSize;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(ChecklistController.class)
@Import(GlobalExceptionHandler.class)
public class ChecklistControllerTest {
    @Autowired
    private MockMvc mockMvc;

    @Test
    void createChecklistReturnsMockedChecklistShape() throws Exception {
        mockMvc.perform(post("/api/checklist")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                        {
                          "concernText": "My dog vomited after taking a flavored compounded oral liquid."
                        }
                        """))
                .andDo(print())
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.concernType").value("flavor_related_vomiting"))
                .andExpect(jsonPath("$.riskLane").value("unexpected_non_life_threatening"))
                .andExpect(jsonPath("$.reviewScope").value("full_quality_review"))
                .andExpect(jsonPath("$.initialTakeaway").isNotEmpty())
                .andExpect(jsonPath("$.requiredChecks", hasSize(5)))
                .andExpect(jsonPath("$.requiredChecks[0].key").value("record_review"))
                .andExpect(jsonPath("$.requiredChecks[0].required").value(true))
                .andExpect(jsonPath("$.missingInformation").isArray())
                .andExpect(jsonPath("$.escalationTriggersToRuleOut").isArray())
                .andExpect(jsonPath("$.evidence").isArray())
                .andExpect(jsonPath("$.limitations").isArray());
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
}
