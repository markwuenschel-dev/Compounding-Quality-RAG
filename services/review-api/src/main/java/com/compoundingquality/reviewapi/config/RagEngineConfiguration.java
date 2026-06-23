package com.compoundingquality.reviewapi.config;

import com.compoundingquality.reviewapi.rag.HttpRagEngineClient;
import com.compoundingquality.reviewapi.rag.HttpRagEngineProperties;
import com.compoundingquality.reviewapi.rag.RagEngineClient;
import java.net.URI;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestClient;

@Configuration
@EnableConfigurationProperties(RagEngineConfiguration.HttpRagEngineSettings.class)
public class RagEngineConfiguration {

    @Bean
    public RestClient.Builder restClientBuilder() {
        return RestClient.builder();
    }

    @Bean
    public HttpRagEngineProperties httpRagEngineProperties(
            HttpRagEngineSettings settings
    ) {
        return settings.toClientProperties();
    }

    @Bean
    public RagEngineClient ragEngineClient(
            RestClient.Builder restClientBuilder,
            HttpRagEngineProperties properties
    ) {
        return new HttpRagEngineClient(restClientBuilder, properties);
    }

    @ConfigurationProperties(prefix = "rag.http")
    public record HttpRagEngineSettings(
            URI baseUrl
    ) {
        private static final URI DEFAULT_BASE_URL =
                URI.create("http://localhost:8000");

        public HttpRagEngineSettings {
            baseUrl = baseUrl == null ? DEFAULT_BASE_URL : baseUrl;
        }

        HttpRagEngineProperties toClientProperties() {
            return new HttpRagEngineProperties(baseUrl);
        }
    }
}