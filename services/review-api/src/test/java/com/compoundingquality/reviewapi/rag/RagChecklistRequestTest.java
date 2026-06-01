package com.compoundingquality.reviewapi.rag;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

class RagChecklistRequestTest {

    @Test
    void fromConcernTextUsesDefaultTopK() {
        RagChecklistRequest request = RagChecklistRequest.fromConcernText("My dog vomited once.");

        assertEquals("My dog vomited once.", request.concernText());
        assertEquals(RagChecklistRequest.DEFAULT_TOP_K, request.topK());
    }

    @Test
    void constructorRejectsMissingOrBlankConcernText() {
        assertThrows(
                IllegalArgumentException.class,
                () -> new RagChecklistRequest(null, 5)
        );

        assertThrows(
                IllegalArgumentException.class,
                () -> new RagChecklistRequest("", 5)
        );

        assertThrows(
                IllegalArgumentException.class,
                () -> new RagChecklistRequest("   ", 5)
        );
    }

    @Test
    void constructorRejectsNonPositiveTopK() {
        assertThrows(
                IllegalArgumentException.class,
                () -> new RagChecklistRequest("My dog vomited once.", 0)
        );

        assertThrows(
                IllegalArgumentException.class,
                () -> new RagChecklistRequest("My dog vomited once.", -1)
        );
    }
}