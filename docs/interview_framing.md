# Interview Framing

This project is strongest when framed as a domain-specific AI workflow system, not as a generic chatbot.

> I built a local-first, synthetic-data RAG assistant for compounding-quality review. React provides the reviewer workflow, Spring Boot owns the API boundary and runtime orchestration, and Python owns retrieval, structured extraction, policy grounding, evaluation, and final assessment.

## Core architecture answer

### Why this architecture?

Python already contained the tested RAG and domain-evaluation engine. Spring Boot provides an enterprise-shaped service boundary with HTTP routes, DTO validation, OpenAPI, structured errors, readiness checks, and a future path to authentication and audit. React provides a human-review interface rather than pretending the model should make an autonomous decision.

### Why not rewrite the Python logic in Java?

A rewrite would duplicate tested behavior and create migration risk. The better engineering choice was to preserve the working Python domain engine behind a stable Java contract. That boundary started as an in-process bridge and has since become an HTTP service called by Spring Boot, without changing the public API.

## Review-summary extraction answer

### What did you build?

I built a hybrid extraction pipeline for messy complaint and investigation narratives.

```text
LLM candidate
-> Pydantic validation
-> deterministic grounding
-> review-scope defaults
-> unresolved questions
-> evidence mapping
-> evaluation
```

The LLM handles language variation. Deterministic code handles workflow-critical semantics such as negation, same-lot patterns, completed versus needed references, non-disclosure, missing investigation steps, device-failure context, and severe triggers.

### Why not use an LLM alone?

An LLM-only system was inconsistent about omitted fields and phrases with overlapping meaning. For example:

- `No external reference needed` contains the positive phrase `external reference needed`.
- `15 mg/mL, 30 mL` describes strength and package size, not the administered dose.
- `Worksheet review found no discrepancy` is a completed record review even though it does not say `record review`.
- `One additional quality complaint was identified for the lot` must normalize to a controlled lot-pattern value.

I used the LLM for semantic normalization and deterministic policy for fields where repeatability and safety mattered more than flexibility.

### How did you evaluate it?

I selected 40 strongly paired complaint/investigation cases and split them into 20 development cases and 20 holdout cases. I tuned only against development cases.

The current development extraction result is:

- 100% scalar-field accuracy
- 100% missing-information precision and recall
- 100% severe-trigger precision and recall
- 100% unresolved-question precision and recall
- 20/20 cases passing

I would explicitly say that this is a development result, not a production claim. The holdout remains the next unbiased test.

## What were the repair scripts?

They were one-time codemods: small repository migration programs that found exact source blocks, replaced them, compiled the result, and added regression tests.

That was useful because I was applying repeatable changes to a local repository remotely. It was safer than manual line-by-line edits, but the early sequence became too fragmented. I learned to prefer complete replacement files for small changes and one verified, atomic migration for broad changes.

## Strong debugging story

> I started with a development extraction benchmark around 66% scalar accuracy and 25% missing-information precision/recall. Instead of prompt-tuning blindly, I grouped errors by mechanism. I found negation precedence, missing review-scope semantics, broad substring matching, administered-dose confusion, incomplete reference states, and unnormalized lot language. I fixed each mechanism in deterministic code, wrote a regression test that reproduced it, and reran the same benchmark. The extraction set reached 20/20, while retrieval remained at 75% hit rate@5. That separation told me the extraction layer was stable enough to stop changing and the next bottleneck was retrieval.

## What would you improve next?

- Correct retrieval labels that conflict with domain policy.
- Add adverse-event and disclosure-aware query expansion/reranking.
- Add SOP wording only where the source policy is genuinely missing.
- Run the untouched holdout.
- Expand the dataset with newly adjudicated cases.
- Add production monitoring, authentication, and approved data integrations only in a private environment.

## Interview answer starters

### How do you debug a bad result?

I decompose the pipeline:

1. Did refusal or boundary detection route correctly?
2. Did retrieval return the right source IDs?
3. Did extraction produce a valid typed object?
4. Did deterministic grounding preserve negation and explicit findings?
5. Did the scope policy apply the correct default?
6. Did unresolved questions reflect only decision-relevant gaps?
7. Is the expected answer itself correct?

Then I create a minimal regression test for the failure mechanism.

### What makes this production-shaped?

- typed request and response contracts;
- schema validation;
- deterministic policy around high-impact fields;
- explicit readiness and timeout behavior;
- structured errors;
- unit, integration, and benchmark tests;
- development/holdout separation;
- evidence and limitation reporting;
- a human confirmation step.

### What is not production yet?

- no real operational integrations;
- no enterprise authentication or authorization;
- no production audit store;
- no deployed monitoring;
- a small benchmark;
- local Docker Compose rather than a production deployment target or orchestration;
- public generalized guidance rather than approved internal sources.

### How does your pharmacy background help?

I can distinguish fields that look similar technically but mean different things operationally: a product strength versus an administered dose, a reported symptom versus a controlled escalation trigger, a missing record review versus a truly non-applicable review, and a completed external reference review versus an unsupported disclosure request. That domain precision shaped the schemas, labels, tests, and policy layer.
