package com.compoundingquality.reviewapi.config;


import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class ApiConfig {

    @Bean
    public OpenAPI reviewApiConfig() {
        return new OpenAPI().info(new Info()
            .title("Compounding Quality Review API")
            .version("0.1.0")
            .description("Spring Boot API boundary for syntheic Compounding Quality RAG engine."));
    }
}