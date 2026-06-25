package com.compoundingquality.reviewapi.config;

import static org.assertj.core.api.Assertions.assertThat;

import jakarta.servlet.FilterChain;
import org.junit.jupiter.api.Test;
import org.slf4j.MDC;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;

class RequestCorrelationFilterTest {

    private final RequestCorrelationFilter filter = new RequestCorrelationFilter();

    @Test
    void storesIncomingRequestIdInMdcAndRequestAttributeThenClearsMdc()
            throws Exception {
        MockHttpServletRequest request = new MockHttpServletRequest();
        request.addHeader(RequestCorrelationFilter.REQUEST_ID_HEADER, "test-request-id-123");
        MockHttpServletResponse response = new MockHttpServletResponse();

        FilterChain chain = (servletRequest, servletResponse) -> {
            assertThat(MDC.get(RequestCorrelationFilter.REQUEST_ID_MDC_KEY))
                    .isEqualTo("test-request-id-123");
            assertThat(servletRequest.getAttribute(
                    RequestCorrelationFilter.REQUEST_ID_ATTRIBUTE
            )).isEqualTo("test-request-id-123");
        };

        filter.doFilter(request, response, chain);

        assertThat(response.getHeader(RequestCorrelationFilter.REQUEST_ID_HEADER))
                .isEqualTo("test-request-id-123");
        assertThat(MDC.get(RequestCorrelationFilter.REQUEST_ID_MDC_KEY)).isNull();
    }

    @Test
    void generatesUuidWhenRequestIdHeaderIsMissing() throws Exception {
        MockHttpServletRequest request = new MockHttpServletRequest();
        MockHttpServletResponse response = new MockHttpServletResponse();

        FilterChain chain = (servletRequest, servletResponse) -> {
            String requestId = MDC.get(RequestCorrelationFilter.REQUEST_ID_MDC_KEY);

            assertThat(requestId)
                    .matches("[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-"
                            + "[0-9a-f]{4}-[0-9a-f]{12}");
            assertThat(servletRequest.getAttribute(
                    RequestCorrelationFilter.REQUEST_ID_ATTRIBUTE
            )).isEqualTo(requestId);
        };

        filter.doFilter(request, response, chain);

        assertThat(response.getHeader(RequestCorrelationFilter.REQUEST_ID_HEADER))
                .matches("[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-"
                        + "[0-9a-f]{4}-[0-9a-f]{12}");
        assertThat(MDC.get(RequestCorrelationFilter.REQUEST_ID_MDC_KEY)).isNull();
    }
}
