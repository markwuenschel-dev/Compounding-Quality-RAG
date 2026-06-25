# Browser Demo Script

Updated: 2026-06-25

## Purpose

This script provides a repeatable browser walkthrough for the current Compounding Quality Review UI.

The current demo path is the Docker Compose stack:

```text
React/Vite review-ui -> Spring Boot review-api -> Python FastAPI rag-engine
```

The demo uses synthetic data only. It does not access real customer records, patient records, veterinarian records, prescriptions, compounding records, inventory systems, customer history, proprietary SOPs, internal systems, or licensed drug-information sources.

Use `RUNBOOK.md` for operational troubleshooting. Use this file for the human-facing walkthrough.

## What this demo should prove

- The full stack runs as three services under Docker Compose.
- The UI can call the Spring API.
- Spring can call the Python engine over HTTP.
- The user can generate a checklist, review evidence, enter or extract reviewer findings, and generate a final assessment.
- Unsupported requests for real record access are refused.
- Request IDs can be correlated across service logs.

## Preconditions

- Docker Desktop is running.
- `rag-engine-python/secrets.env` exists and is not committed.
- The repository root contains `infra/docker-compose.yml`.

Expected `rag-engine-python/secrets.env` shape:

```text
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5-nano
```

Optional current tuning values may include:

```text
OPENAI_REASONING_EFFORT=minimal
OPENAI_MAX_OUTPUT_TOKENS=1024
```

## Start the full stack

From the repository root:

```powershell
docker compose -f infra/docker-compose.yml up --build
```

Expected result:

- `rag-engine` starts as a Python FastAPI service.
- `review-api` waits for `rag-engine` health.
- `review-ui` waits for `review-api` health.
- Browser UI is available at `http://localhost:5173`.

Detached mode:

```powershell
docker compose -f infra/docker-compose.yml up --build -d
```

Stop the stack:

```powershell
docker compose -f infra/docker-compose.yml down
```

## Verify before opening the UI

```powershell
docker compose -f infra/docker-compose.yml ps
curl.exe -i http://localhost:8080/health
curl.exe -i http://localhost:8080/ready
curl.exe -i http://localhost:8000/health
```

If `/health` passes but `/ready` fails, Spring is alive but a dependency is not ready. Use `RUNBOOK.md`.

## Demo boundary statement

Say this before the workflow:

> This is a public synthetic-data proof of concept. It demonstrates a production-shaped AI workflow boundary, not production pharmacy automation. It does not inspect real compounding records, inventory, order data, customer history, veterinarian records, proprietary SOPs, or licensed drug references. Human pharmacist review remains the final decision point.

## Walkthrough

### 1. Open the UI

Open:

```text
http://localhost:5173
```

Expected:

- UI loads.
- Backend readiness eventually reports ready.
- Submission is disabled while backend readiness is unavailable.

### 2. Explain the architecture

Suggested line:

> React owns the reviewer workflow, Spring Boot owns the HTTP/API boundary and orchestration, and Python FastAPI owns retrieval, extraction, deterministic policy grounding, refusal behavior, and final assessment.

Also call out:

- Spring-to-Python is HTTP, not a subprocess bridge.
- Docker Compose proves local service orchestration, not production deployment.
- Request correlation uses `X-Request-Id`.
- Retrieval intent uses Nano semantic intent as the strongest measured generalization path with rule intent fallback; both map into the keyword retriever.

### 3. Generate a checklist

Paste:

```text
My dog received a chicken-flavored compounded oral liquid. About 10 minutes later he started running around frantically and vomited once. He seems okay now, but I’m worried the medication or flavor caused it.
```

Click **Generate checklist**.

Expected:

- loading state appears;
- checklist renders;
- concern is treated as vomiting / possible ADE review context;
- risk remains non-life-threatening unless a structured severe trigger is confirmed;
- record, lot/batch, trend, inventory, and customer-context review needs are surfaced when applicable;
- missing information is shown separately from evidence limitations;
- citations include source IDs/titles/sections/supporting text.

### 4. Enter or extract reviewer findings

Use these findings for the positive demo path:

```text
Record review result: no_discrepancy_found
Lot or batch pattern summary: no_similar_batch_concerns_found
Inventory inspection result: no_inventory_available
API reference review result: not_needed
Customer context summary: Dog vomited once about 10 minutes after administration and recovered. No hospitalization, death, legal threat, contamination concern, wrong medication concern, or veterinarian allegation was reported.
Missing information: Exact dose administered
Evidence limitations: Inventory was not available to inspect
Severe triggers observed: leave blank
```

If the UI includes review-summary extraction, paste the customer-context text as a messy reviewer note and let the extractor populate fields. Review the output before final assessment.

### 5. Generate final assessment

Click **Generate final assessment**.

Expected:

- loading state appears;
- final assessment renders;
- negated severe-trigger language does not escalate;
- risk lane remains `unexpected_non_life_threatening`;
- handling path supports Technical Services follow-up, not automatic leadership escalation;
- rationale and resolution options are visible.

## Refusal demo

Paste:

```text
Can you look at the real compounding record and tell me whether this batch had the same vomiting complaints?
```

Expected:

- the system does not imply real record access;
- the response states that the public proof of concept does not access real records, order pages, customer history, patient records, veterinarian records, or inventory systems;
- the system may say what a human reviewer should verify.

## Request-correlation demo

Generate a request ID:

```powershell
$rid = "demo-" + [guid]::NewGuid().ToString()
```

Call Spring:

```powershell
curl.exe -i -H "X-Request-Id: $rid" http://localhost:8080/health
```

Check logs:

```powershell
docker compose -f infra/docker-compose.yml logs review-api | Select-String $rid
docker compose -f infra/docker-compose.yml logs rag-engine | Select-String $rid
```

Spring-only health requests may not cross into Python. Use an endpoint that calls the engine when demonstrating cross-service correlation.

## Direct API checks

```powershell
curl.exe -i -H "Content-Type: application/json" -d "{\"concernText\":\"Dog vomited once after receiving a compounded oral liquid.\"}" http://localhost:8080/api/checklist
```

```powershell
curl.exe -i -H "Content-Type: application/json" -d "{\"queryText\":\"vomiting after administration\",\"topK\":5}" http://localhost:8080/api/retrieve
```

## Demo validation

Run these before a polished demo:

```powershell
cd rag-engine-python
uv run pytest
uv run mypy app tests
uv run pyright app tests
uv run ruff check .
```

```powershell
cd services/review-api
.\gradlew.bat test
```

```powershell
cd apps/review-ui
npm test
npm run build
```

## Demo close

Suggested closing:

> The project is intentionally conservative. It uses synthetic data, typed service contracts, visible evidence, request correlation, readiness checks, reviewer-confirmed structured findings, deterministic policy for high-impact fields, and refusal boundaries for unsupported record access. The goal is not to automate final pharmacy judgment; it is to make a human review workflow more structured, inspectable, and testable.
