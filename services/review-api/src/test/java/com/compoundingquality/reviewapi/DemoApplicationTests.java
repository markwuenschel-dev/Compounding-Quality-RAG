package com.compoundingquality.reviewapi;

import com.compoundingquality.reviewapi.rag.RagEngineClient;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;


@SpringBootTest
class DemoApplicationTests {

    @MockitoBean
    private RagEngineClient ragEngineClient;

    @Test
    void contextLoads() {
    }
}