# Operations Runbook

This runbook explains how to start, verify, inspect, and troubleshoot the local Compounding Quality RAG stack.

The README explains what the project is. This runbook explains what to do when the stack does not behave as expected.

## Scope

This runbook covers the local, containerized development stack:

* React/TypeScript review UI
* Spring Boot review API
* Python FastAPI RAG engine
* Docker Compose service orchestration
* Health and readiness checks
* Request correlation across Spring and Python logs
* Common failure modes and recovery commands

This is not a production deployment guide. The public project uses synthetic data only and does not access real customer, patient, veterinarian, prescription, order, compounding-record, inventory, internal SOP, or licensed drug-reference data.

## Service Map

| Service      | Responsibility                                   | Default local access            |
| ------------ | ------------------------------------------------ | ------------------------------- |
| `review-ui`  | React/Vite user interface                        | `http://localhost:5173`         |
| `review-api` | Spring Boot API boundary and orchestration layer | usually `http://localhost:8080` |
| `rag-engine` | Python FastAPI review engine                     | usually `http://localhost:8000` |

Inside Docker Compose, services communicate over the Compose network by service name:

| Caller       | Target                                                                              |
| ------------ | ----------------------------------------------------------------------------------- |
| `review-ui`  | proxies `/api`, `/health`, and `/ready` to `review-api`                             |
| `review-api` | calls `rag-engine` over HTTP                                                        |
| `rag-engine` | owns retrieval, extraction, grounding, refusal behavior, and final-assessment logic |

## Required Configuration

The Python engine reads OpenAI configuration from a gitignored secrets file:

```text
rag-engine-python/secrets.env
```

Expected values:

```text
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5-nano
```

Optional tuning values may exist depending on the current implementation:

```text
OPENAI_REASONING_EFFORT=minimal
OPENAI_MAX_OUTPUT_TOKENS=1024
```

Do not commit secrets. Do not place real pharmacy, customer, patient, veterinarian, prescription, order, inventory, or proprietary SOP data in this repository.

## Normal Startup

From the repository root:

```powershell
docker compose -f infra/docker-compose.yml up --build
```

Expected result:

* `rag-engine` starts first.
* `review-api` waits for `rag-engine` health.
* `review-ui` waits for `review-api` health.
* UI becomes available at `http://localhost:5173`.

To run in detached mode:

```powershell
docker compose -f infra/docker-compose.yml up --build -d
```

To stop the stack:

```powershell
docker compose -f infra/docker-compose.yml down
```

To stop and remove orphaned services:

```powershell
docker compose -f infra/docker-compose.yml down --remove-orphans
```

## Basic Verification

### Check running containers

```powershell
docker compose -f infra/docker-compose.yml ps
```

Healthy startup should show all expected services running. If one service is unhealthy or exited, inspect that service's logs before making code changes.

### Check the UI

Open:

```text
http://localhost:5173
```

Expected result:

* Review UI loads.
* Backend readiness indicator eventually reports ready.
* API-backed workflow actions do not immediately fail.

### Check Spring API health

```powershell
curl.exe -i http://localhost:8080/health
```

Expected result:

```text
HTTP/1.1 200
```

### Check Spring API readiness

```powershell
curl.exe -i http://localhost:8080/ready
```

Expected result:

```text
HTTP/1.1 200
```

If readiness is down while health is up, Spring itself is alive but one or more dependencies are not ready.

### Check Python engine health directly

```powershell
curl.exe -i http://localhost:8000/health
```

Expected result:

```text
HTTP/1.1 200
```

If this fails, debug the Python engine before debugging Spring or React.

## Request Correlation

The stack propagates `X-Request-Id` across the Spring and Python boundary.

Spring is responsible for:

* accepting or generating the request ID;
* attaching it to the response header;
* placing it in MDC for Spring logs;
* forwarding it to the Python engine through `X-Request-Id`.

Python is responsible for:

* reading `X-Request-Id`;
* echoing it in the response header;
* including it in request logs and error logs.

### Verify Spring response header

```powershell
$rid = "runbook-" + [guid]::NewGuid().ToString()
curl.exe -i -H "X-Request-Id: $rid" http://localhost:8080/health
```

Expected result:

```text
X-Request-Id: runbook-...
```

### Verify Python response header directly

```powershell
$rid = "runbook-python-" + [guid]::NewGuid().ToString()
curl.exe -i -H "X-Request-Id: $rid" http://localhost:8000/health
```

Expected result:

```text
X-Request-Id: runbook-python-...
```

### Verify request ID in logs

After making a request with a known request ID:

```powershell
docker compose -f infra/docker-compose.yml logs review-api | Select-String $rid
docker compose -f infra/docker-compose.yml logs rag-engine | Select-String $rid
```

Expected result:

* Spring logs contain the request ID.
* Python logs contain the request ID when the request crosses into the engine.

For a Python-only smoke test, run:

```powershell
bash scripts/smoke_request_correlation.sh
```

Expected result:

```text
verified request correlation
```

If the script fails on Windows due to line endings, ensure shell scripts use LF endings.

## Logs

### All services

```powershell
docker compose -f infra/docker-compose.yml logs
```

### Follow all logs

```powershell
docker compose -f infra/docker-compose.yml logs -f
```

### Spring API logs

```powershell
docker compose -f infra/docker-compose.yml logs review-api
```

### Python engine logs

```powershell
docker compose -f infra/docker-compose.yml logs rag-engine
```

### React UI logs

```powershell
docker compose -f infra/docker-compose.yml logs review-ui
```

### Last 100 lines for one service

```powershell
docker compose -f infra/docker-compose.yml logs --tail=100 review-api
```

## Troubleshooting Decision Tree

### UI loads but API calls fail

Symptoms:

* UI opens in browser.
* Checklist, retrieval, extraction, or final-assessment actions fail.
* Browser shows network errors or backend unavailable state.

Checks:

```powershell
docker compose -f infra/docker-compose.yml ps
curl.exe -i http://localhost:8080/health
curl.exe -i http://localhost:8080/ready
docker compose -f infra/docker-compose.yml logs review-api
docker compose -f infra/docker-compose.yml logs review-ui
```

Likely causes:

| Observation                        | Likely cause                                                    | Next action                                  |
| ---------------------------------- | --------------------------------------------------------------- | -------------------------------------------- |
| UI running, API health fails       | `review-api` not running or port mismatch                       | Inspect `review-api` logs                    |
| API health passes, readiness fails | dependency problem, usually `rag-engine`                        | Inspect readiness body and `rag-engine` logs |
| Browser proxy error                | Vite proxy or service name mismatch                             | Inspect `review-ui` logs and Vite config     |
| API returns structured error       | backend handled request but rejected input or downstream failed | Use request ID and inspect API/Python logs   |

### API is up but readiness is down

Symptoms:

* `/health` returns `200`.
* `/ready` returns non-ready response or error.
* UI reports backend unavailable.

Checks:

```powershell
curl.exe -i http://localhost:8080/health
curl.exe -i http://localhost:8080/ready
curl.exe -i http://localhost:8000/health
docker compose -f infra/docker-compose.yml logs review-api
docker compose -f infra/docker-compose.yml logs rag-engine
```

Likely causes:

| Observation                                  | Likely cause                                                                    | Next action                    |
| -------------------------------------------- | ------------------------------------------------------------------------------- | ------------------------------ |
| Python health fails                          | `rag-engine` is not ready                                                       | Debug Python engine first      |
| Python health passes, Spring readiness fails | Spring cannot reach engine over Compose network or configured base URL is wrong | Check `PYTHON_ENGINE_BASE_URL` |
| Readiness body names failed check            | Named dependency is unavailable                                                 | Follow the named failure       |

### Python engine is unhealthy

Symptoms:

* `rag-engine` exited or unhealthy.
* Direct Python health check fails.
* Spring readiness fails.

Checks:

```powershell
docker compose -f infra/docker-compose.yml ps
docker compose -f infra/docker-compose.yml logs rag-engine
```

Likely causes:

| Log pattern                   | Likely cause                       | Next action                                     |
| ----------------------------- | ---------------------------------- | ----------------------------------------------- |
| missing environment variable  | missing `secrets.env` or key       | create/update `rag-engine-python/secrets.env`   |
| import error                  | Python dependency or package issue | rebuild image and run Python tests locally      |
| port already allocated        | local process already using port   | stop conflicting process or change port mapping |
| application startup exception | code/config issue                  | inspect traceback and reproduce locally         |

Recovery:

```powershell
docker compose -f infra/docker-compose.yml build rag-engine
docker compose -f infra/docker-compose.yml up rag-engine
```

### Review-summary extraction returns 502

Symptoms:

* UI or API returns downstream engine failure.
* Spring maps Python failure to API error.
* Extraction endpoint fails while simpler endpoints may work.

Checks:

```powershell
docker compose -f infra/docker-compose.yml logs review-api
docker compose -f infra/docker-compose.yml logs rag-engine
```

Likely causes:

| Observation                         | Likely cause                                     | Next action                             |
| ----------------------------------- | ------------------------------------------------ | --------------------------------------- |
| Python log shows missing OpenAI key | `OPENAI_API_KEY` missing from `secrets.env`      | add key and restart `rag-engine`        |
| Python log shows OpenAI/API timeout | external model call failed or timed out          | retry once, then inspect timeout/config |
| Spring log shows downstream timeout | Python engine took too long                      | inspect Python logs and model latency   |
| Python returns validation error     | request shape mismatch between Spring and Python | inspect DTOs and endpoint contract      |

Recovery:

```powershell
docker compose -f infra/docker-compose.yml restart rag-engine review-api
```

### Retrieval returns no evidence

Symptoms:

* `/api/retrieve` returns an empty evidence list.
* UI shows no supporting chunks.
* Checklist may still work.

Checks:

```powershell
docker compose -f infra/docker-compose.yml logs review-api
docker compose -f infra/docker-compose.yml logs rag-engine
```

Local Python checks:

```powershell
cd rag-engine-python
uv run python -m app.ingestion
uv run python -m app.retrieval_evaluate
```

Likely causes:

| Observation             | Likely cause                                            | Next action                                  |
| ----------------------- | ------------------------------------------------------- | -------------------------------------------- |
| index missing or stale  | ingestion output not generated or not copied into image | rerun ingestion and rebuild image            |
| query too sparse        | synthetic concern does not overlap corpus               | test with known evaluation question          |
| expected source missing | corpus/index mismatch                                   | regenerate index and rerun retrieval eval    |
| retrieval regression    | ranking/query construction changed                      | inspect retrieval comparison or failure logs |

### Request ID is missing from Spring logs

Symptoms:

* Response has no `X-Request-Id`.
* Spring logs show blank `requestId=`.
* Errors cannot be correlated across services.

Checks:

```powershell
$rid = "runbook-" + [guid]::NewGuid().ToString()
curl.exe -i -H "X-Request-Id: $rid" http://localhost:8080/health
docker compose -f infra/docker-compose.yml logs review-api | Select-String $rid
```

Likely causes:

| Observation                                     | Likely cause                                           | Next action                          |
| ----------------------------------------------- | ------------------------------------------------------ | ------------------------------------ |
| response header missing                         | request-correlation filter not registered              | inspect Spring filter/component scan |
| response header present but logs blank          | MDC pattern/config issue                               | inspect logging pattern              |
| logs contain request ID but error body does not | exception handler not reading request attribute/header | inspect global exception handler     |

### Request ID is missing from Python logs

Symptoms:

* Spring logs contain request ID.
* Python logs do not contain the same request ID.
* Python direct smoke test may pass or fail depending on path.

Checks:

```powershell
$rid = "runbook-python-" + [guid]::NewGuid().ToString()
curl.exe -i -H "X-Request-Id: $rid" http://localhost:8000/health
docker compose -f infra/docker-compose.yml logs rag-engine | Select-String $rid
```

Likely causes:

| Observation                                         | Likely cause                                  | Next action                                  |
| --------------------------------------------------- | --------------------------------------------- | -------------------------------------------- |
| direct Python request does not log ID               | FastAPI middleware/logging issue              | inspect `rag-engine-python/app/server.py`    |
| direct Python request logs ID, Spring path does not | Spring client not forwarding header           | inspect `HttpRagEngineClient`                |
| Python logs only uvicorn access line                | app logger not writing to stderr              | inspect Python logger setup                  |
| smoke script fails                                  | line endings, port conflict, middleware issue | run script manually and inspect captured log |

## Recovery Commands

### Rebuild all images

```powershell
docker compose -f infra/docker-compose.yml build --no-cache
```

### Restart all services

```powershell
docker compose -f infra/docker-compose.yml restart
```

### Restart one service

```powershell
docker compose -f infra/docker-compose.yml restart rag-engine
docker compose -f infra/docker-compose.yml restart review-api
docker compose -f infra/docker-compose.yml restart review-ui
```

### Tear down and restart cleanly

```powershell
docker compose -f infra/docker-compose.yml down --remove-orphans
docker compose -f infra/docker-compose.yml up --build
```

### Remove stopped containers and unused build cache

Use only when ordinary rebuilds do not clear stale container state:

```powershell
docker system prune
```

Do not prune volumes unless you intentionally want to remove local persisted data.

## Local Non-Compose Checks

### Python engine

```powershell
cd rag-engine-python
uv sync --dev
uv run python -m app.ingestion
uv run pytest
uv run mypy app tests
uv run pyright app tests
uv run ruff check .
```

### Spring Boot API

```powershell
cd services/review-api
.\gradlew.bat test
.\gradlew.bat bootRun
```

For local Spring-to-Python testing, ensure the Python engine is running and Spring points to it:

```powershell
$env:PYTHON_ENGINE_BASE_URL="http://localhost:8000"
```

### React UI

```powershell
cd apps/review-ui
npm ci
npm test
npm run build
npm run dev
```

## Evidence to Capture Before Debugging Further

Before changing code, capture:

```powershell
docker compose -f infra/docker-compose.yml ps
docker compose -f infra/docker-compose.yml logs --tail=200 review-api
docker compose -f infra/docker-compose.yml logs --tail=200 rag-engine
docker compose -f infra/docker-compose.yml logs --tail=200 review-ui
```

For request-specific failures, also capture:

* endpoint called;
* request payload, with secrets removed;
* response status;
* response body;
* `X-Request-Id`;
* matching Spring log lines;
* matching Python log lines.

Do not start broad refactors until the failing service, failing endpoint, and failing contract are identified.

## Known Limits

This local stack proves:

* services build locally;
* services start together under Docker Compose;
* health-gated startup works;
* Spring can call the Python engine over HTTP;
* the UI can call the Spring API through the local dev proxy;
* request IDs can be propagated and inspected across logs;
* synthetic review workflows can be demonstrated end to end.

This local stack does not prove:

* production deployment readiness;
* cloud networking;
* autoscaling;
* production monitoring;
* authentication or authorization;
* persistent audit storage;
* governed access to real pharmacy data;
* calibrated model confidence;
* compliance approval.

## Safe Operating Boundary

Use only synthetic inputs.

Do not paste or load:

* real customer data;
* patient data;
* veterinarian data;
* prescription/order data;
* internal SOPs;
* proprietary operational data;
* licensed external drug-reference content;
* screenshots from internal systems.

The system is a review-support prototype. It does not make final clinical, legal, quality, or customer-resolution decisions.

## Interview Framing

Use this runbook to explain operational ownership:

> The README explains the architecture and evaluation results. The runbook explains how to operate and troubleshoot the stack. It includes health checks, readiness checks, service logs, request correlation, common failure modes, and recovery commands. That matters because the project is not just a working demo — it has the operational surface needed to debug a React, Spring Boot, and Python AI workflow when something fails.
