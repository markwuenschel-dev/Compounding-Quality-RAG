package com.compoundingquality.reviewapi.error;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import com.compoundingquality.reviewapi.application.ChecklistService;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;

@WebMvcTest(controllers = GlobalExceptionHandlerTest.TestController.class)
@Import({
        GlobalExceptionHandler.class,
        GlobalExceptionHandlerTest.TestController.class
})
class GlobalExceptionHandlerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private ChecklistService checklistService;

    @Test
    void returnsValidationErrorShapeForInvalidRequestBody() throws Exception {
        mockMvc.perform(post("/test/validate")
        .contentType(MediaType.APPLICATION_JSON)
        .content("""
                {
                  "concernText": ""
                }
                """))
        .andExpect(status().isBadRequest())
        .andExpect(jsonPath("$.status").value(400))
        .andExpect(jsonPath("$.error").value("Bad Request"))
        .andExpect(jsonPath("$.message").value("Validation failed"))
        .andExpect(jsonPath("$.path").value("/test/validate"))
        .andExpect(jsonPath("$.requestId").isNotEmpty())
        .andExpect(jsonPath("$.fieldErrors").isArray())
        .andExpect(jsonPath("$.fieldErrors[0].field").value("concernText"))
        .andExpect(jsonPath("$.fieldErrors[0].message").value("concernText is required"));
            }


    @Test
    void returnsMalformedBodyErrorShape() throws Exception {
        mockMvc.perform(post("/test/validate")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").value(400))
                .andExpect(jsonPath("$.error").value("Bad Request"))
                .andExpect(jsonPath("$.message").isNotEmpty())
                .andExpect(jsonPath("$.path").value("/test/validate"))
                .andExpect(jsonPath("$.requestId").exists())
                .andExpect(jsonPath("$.fieldErrors").isArray());
    }

    @Test
    void returnsResponseStatusErrorShape() throws Exception {
        mockMvc.perform(get("/test/not-found")
                .header("X-Request-Id", "test-request-123"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.status").value(404))
                .andExpect(jsonPath("$.error").value("Not Found"))
                .andExpect(jsonPath("$.message").isNotEmpty())
                .andExpect(jsonPath("$.path").value("/test/not-found"))
                .andExpect(jsonPath("$.requestId").value("test-request-123"));
    }

    @Test
    void returnsGenericErrorShapeWithoutLeakingExceptionDetails() throws Exception {
        mockMvc.perform(get("/test/error"))
                .andExpect(status().isInternalServerError())
                .andExpect(jsonPath("$.status").value(500))
                .andExpect(jsonPath("$.error").value("Internal Server Error"))
                .andExpect(jsonPath("$.message").isNotEmpty())
                .andExpect(jsonPath("$.path").value("/test/error"))
                .andExpect(jsonPath("$.requestId").exists());
    }

    @RestController
    public static class TestController {

        @PostMapping("/test/validate")
        Map<String, String> validate(@Valid @RequestBody TestRequest request) {
            return Map.of("concernText", request.concernText());
        }

        @GetMapping("/test/not-found")
        void notFound() {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Test resource not found");
        }

        @GetMapping("/test/error")
        void error() {
            throw new IllegalStateException("Internal implementation detail");
        }
    }

    public record TestRequest(
            @NotBlank(message = "concernText is required") String concernText) {
    }
}