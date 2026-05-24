package com.compoundingquality.reviewapi.api;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(HealthController.class)
public class HealthControllerTest {
    @Autowired
    private MockMvc mockMvc;

    @Test
    void contextLoads() {}

    @Test
    public void shouldReturnStatusAndTimestamp() throws Exception {
        mockMvc.perform(get("/health"))
            .andExpect(jsonPath("$.service").value("review-api"))
            .andExpect(jsonPath("$.status").value("UP"))
            .andExpect(jsonPath("$.timestamp").exists());
    }

}
