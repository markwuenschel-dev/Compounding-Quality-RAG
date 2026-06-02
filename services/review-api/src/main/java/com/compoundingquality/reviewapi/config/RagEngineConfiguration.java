package com.compoundingquality.reviewapi.config;

import com.compoundingquality.reviewapi.rag.PythonProcessRagEngineClient;
import com.compoundingquality.reviewapi.rag.PythonProcessRagEngineProperties;
import com.compoundingquality.reviewapi.rag.RagEngineClient;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.file.Path;
import java.time.Duration;
import java.util.List;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
@EnableConfigurationProperties(RagEngineConfiguration.PythonRagEngineSettings.class)
public class RagEngineConfiguration {

    @Bean
    public RagEngineClient ragEngineClient(
            ObjectMapper objectMapper,
            PythonRagEngineSettings settings
    ) {
        return new PythonProcessRagEngineClient(
                objectMapper,
                settings.toClientProperties()
        );
    }

    @ConfigurationProperties(prefix = "rag.python")
    public record PythonRagEngineSettings(
            List<String> command,
            Path workingDirectory,
            Duration timeout
    ) {
        private static final List<String> DEFAULT_COMMAND = List.of("python", "-m", "app.api_runner");
        private static final Path DEFAULT_WORKING_DIRECTORY = Path.of("../../rag-engine-python");
        private static final Duration DEFAULT_TIMEOUT = Duration.ofSeconds(10);

        public PythonRagEngineSettings {
            command = command == null || command.isEmpty() ? DEFAULT_COMMAND : List.copyOf(command);
            workingDirectory = workingDirectory == null ? DEFAULT_WORKING_DIRECTORY : workingDirectory;
            timeout = timeout == null ? DEFAULT_TIMEOUT : timeout;
        }

        PythonProcessRagEngineProperties toClientProperties() {
            return new PythonProcessRagEngineProperties(
                    command,
                    workingDirectory,
                    timeout
            );
        }
    }
}