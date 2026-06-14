package com.compoundingquality.reviewapi.api;

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultHandlers.print;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.compoundingquality.reviewapi.application.ReadinessService;
import com.compoundingquality.reviewapi.dto.ReadinessResponse;
import com.compoundingquality.reviewapi.dto.ReadinessResponse.ReadinessCheck;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(ReadinessController.class)
class ReadinessControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private ReadinessService readinessService;

    @Test
    void returnsOkWhenApplicationIsReady() throws Exception {
        when(readinessService.checkReadiness()).thenReturn(
                new ReadinessResponse(
                        ReadinessResponse.READY,
                        List.of(
                                ReadinessCheck.up(
                                        "spring",
                                        "The Spring Boot API is running."
                                )
                        ),
                        Instant.parse("2026-06-14T12:00:00Z")
                )
        );

        mockMvc.perform(get("/ready"))
                .andDo(print())
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("READY"))
                .andExpect(jsonPath("$.checks[0].name").value("spring"))
                .andExpect(jsonPath("$.checks[0].status").value("UP"));
    }

    @Test
    void returnsServiceUnavailableWhenDependencyIsUnavailable() throws Exception {
        when(readinessService.checkReadiness()).thenReturn(
                new ReadinessResponse(
                        ReadinessResponse.NOT_READY,
                        List.of(
                                ReadinessCheck.down(
                                        "pythonCommand",
                                        "Python command unavailable."
                                )
                        ),
                        Instant.parse("2026-06-14T12:00:00Z")
                )
        );

        mockMvc.perform(get("/ready"))
                .andDo(print())
                .andExpect(status().isServiceUnavailable())
                .andExpect(jsonPath("$.status").value("NOT_READY"))
                .andExpect(jsonPath("$.checks[0].status").value("DOWN"));
    }
}
