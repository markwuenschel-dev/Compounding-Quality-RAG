## Spring Boot API Shell

- Added `GET /health`.
- Added `HealthResponse` DTO record.
- Added `HealthControllerTest` with MockMvc.
- Added Swagger/OpenAPI UI.
- Confirmed `gradlew test` passes.
## Python RAG / CLI Update

- Added schema-level `RefusalReason`, `RefusalResult`, and `IntakeUnderstanding` contracts.
- Added optional OpenAI-backed intake-understanding extraction.
- Wired intake understanding into Phase 1 so known concern facts can suppress redundant missing-information items.
- Added semantic boundary detection for unsupported inventory/order, external drug-reference, and clinical/legal conclusion requests.
- Updated reporting tests to avoid brittle exact-copy assertions.
- Confirmed Python tests pass after intake-understanding wiring.
