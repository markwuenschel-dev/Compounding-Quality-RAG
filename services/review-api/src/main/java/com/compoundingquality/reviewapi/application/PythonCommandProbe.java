package com.compoundingquality.reviewapi.application;

import com.compoundingquality.reviewapi.dto.ReadinessResponse.ReadinessCheck;
import java.nio.file.Path;
import java.time.Duration;
import java.util.List;

public interface PythonCommandProbe {

    ReadinessCheck probe(
            List<String> configuredCommand,
            Path workingDirectory,
            Duration timeout
    );
}
