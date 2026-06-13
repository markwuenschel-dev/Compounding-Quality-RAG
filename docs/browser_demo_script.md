# Browser Demo Script

## Purpose

This script provides a repeatable full-stack walkthrough for the Compounding Quality Review UI.

The demo uses synthetic data only. It does not access real customer records, patient records, prescriptions, compounding records, inventory systems, customer history, proprietary SOPs, or licensed drug-information sources.

## Preconditions

- Java and Node.js are installed.
- Python environment and project dependencies are available.
- The Spring Boot API and React UI dependencies have already been installed.
- `apps/review-ui/vite.config.ts` proxies `/api` to `http://localhost:8080`.

Expected proxy configuration:

```ts
server: {
  proxy: {
    "/api": "http://localhost:8080",
  },
},
```

## Start the backend

Open a PowerShell terminal at the repository root:

```powershell
cd services\review-api
.\gradlew.bat bootRun
```

Wait for Spring Boot to start on port `8080`.

Verify the health endpoint in another terminal:

```powershell
Invoke-RestMethod -Uri "http://localhost:8080/health"
```

Expected result:

```json
{
  "service": "review-api",
  "status": "UP",
  "timestamp": "<current timestamp>"
}
```

## Start the React UI

Open a second PowerShell terminal at the repository root:

```powershell
cd apps\review-ui
npm run dev
```

Open the Vite URL shown in the terminal, usually:

```text
http://localhost:5173
```

## Demo walkthrough

### 1. Introduce the workflow

Suggested framing:

> This is a local-first review-support workbench for synthetic compounding-quality inquiries. The React UI collects the concern and reviewer findings, Spring Boot owns the HTTP contract and orchestration boundary, and the Python package owns the tested retrieval and domain behavior.

Call out the visible boundaries:

- Synthetic demo data only
- Human pharmacist review remains the final decision point
- Keyword retrieval remains the default application path
- Embedding and hybrid retrieval remain evaluation baselines

### 2. Generate a checklist

Enter this concern narrative:

```text
My dog received a chicken-flavored compounded oral liquid. About 10 minutes later he started running around frantically and vomited once. He seems okay now, but I’m worried the medication or flavor caused it.
```

Click **Generate checklist**.

Expected behavior:

- A loading state appears while the request is running.
- The checklist renders after the API responds.
- The result identifies a vomiting or suspected adverse-event concern.
- The risk lane remains non-life-threatening unless a structured severe trigger is confirmed.
- Required checks include relevant record, lot/batch, trend, inventory, or customer-context review steps.
- Missing information and evidence limitations are shown separately.
- Evidence citations include source IDs, titles, and section headings.
- The reviewer findings form appears after checklist success.

### 3. Enter reviewer findings

Use these values:

**Record review result**

```text
no_discrepancy_found
```

**Lot or batch pattern summary**

```text
no_similar_batch_concerns_found
```

**Inventory inspection result**

```text
no_inventory_available
```

**Customer context summary**

```text
Dog vomited once about 10 minutes after administration and recovered. No hospitalization, death, legal threat, contamination concern, wrong medication concern, or veterinarian allegation was reported.
```

**API reference review result**

```text
not_needed
```

**Missing information**

```text
Exact dose administered
```

**Evidence limitations**

```text
Inventory was not available to inspect
```

**Severe triggers observed**

Leave this field blank.

Click **Generate final assessment**.

Expected behavior:

- A loading state appears while the final assessment request is running.
- The final assessment renders successfully.
- Negated severe-trigger language does not create a severe escalation.
- The risk lane remains `unexpected_non_life_threatening`.
- The handling path supports Technical Services follow-up rather than automatic leadership escalation.
- Resolution options and rationale render.
- The UI shows that resolution review is required when the backend returns `true`.

## Refusal demo

Use a new concern or direct API test with this request:

```text
Can you look at the real compounding record and tell me whether this batch had the same vomiting complaints?
```

Expected behavior:

- The system must not imply access to real operational records.
- The response should state that the public proof of concept does not access real compounding records, order pages, customer history, patient records, or inventory systems.
- The system may state what a human reviewer should verify using supplied synthetic findings.

## Direct API checks

### Checklist endpoint

```powershell
Invoke-RestMethod `
  -Uri "http://localhost:8080/api/checklist" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"concernText":"Dog vomited once after receiving a compounded oral liquid."}'
```

### Retrieval endpoint

```powershell
Invoke-RestMethod `
  -Uri "http://localhost:8080/api/retrieve" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"queryText":"vomiting after administration","topK":5}'
```

## Troubleshooting

### Health endpoint works but the UI returns 404

Cause:

The browser request is reaching Vite instead of Spring Boot.

Check that `apps/review-ui/vite.config.ts` contains:

```ts
server: {
  proxy: {
    "/api": "http://localhost:8080",
  },
},
```

Restart Vite after changing the proxy:

```powershell
cd apps\review-ui
npm run dev
```

### `gradlew.bat` is not found from the repository root

The Gradle wrapper is inside `services/review-api`.

Use:

```powershell
cd services\review-api
.\gradlew.bat bootRun
```

### Spring Boot is running but an API endpoint still returns 404

Verify the endpoint directly:

```powershell
Invoke-RestMethod `
  -Uri "http://localhost:8080/api/checklist" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"concernText":"Dog vomited once."}'
```

If the direct request returns 404, confirm that the expected controller is registered and that the current branch contains the endpoint implementation.

### UI tests pass but browser requests fail

The React tests mock the API client. Passing tests prove frontend state and rendering behavior, but real browser requests still require:

- Spring Boot running on port `8080`
- Vite running on port `5173`
- `/api` proxy configured
- Python bridge and required local dependencies available

### Final assessment button remains disabled

Complete all required reviewer findings:

- Record review result
- Lot or batch pattern summary
- Inventory inspection result
- API reference review result

### Browser console shows network errors

Confirm both services are running:

```powershell
Invoke-RestMethod -Uri "http://localhost:8080/health"
```

Then restart the Vite dev server.

## Validation before the demo

Run frontend checks:

```powershell
cd apps\review-ui
npm test
npm run build
```

Run backend tests:

```powershell
cd ..\..\services\review-api
.\gradlew.bat test
```

Return to the repository root:

```powershell
cd ..\..
```

Confirm the working tree:

```powershell
git status
```

## Demo close

Suggested closing statement:

> The project is intentionally conservative. Retrieval remains inspectable, reviewer-confirmed structured findings control severe escalation, unsupported record-access requests are refused, and the final decision remains with the human pharmacist reviewer.
