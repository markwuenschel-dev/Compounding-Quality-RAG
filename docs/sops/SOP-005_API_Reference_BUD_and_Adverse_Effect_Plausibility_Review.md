# SOP-005 API Reference, BUD, and Adverse Effect Plausibility Review

Document ID: SOP-005  
Title: API Reference, BUD, and Adverse Effect Plausibility Review  
Version: 1.1  
Effective Date: 2026-05-04  
Process Area: API and BUD review  
Source Type: sop  
Synthetic: true
## Purpose

Define how the synthetic workflow handles adverse-effect plausibility, BUD questions, and external reference limitations.

## Scope

This SOP applies to suspected ADE narratives, flavor-related vomiting, efficacy concerns, BUD questions, and customer or veterinarian allegations involving medication effects.

## Review Procedure

1. Determine whether adverse-effect plausibility is needed to answer the question.
2. If the public synthetic corpus includes a synthetic API-reference document, retrieve and cite it as limited synthetic support.
3. If no synthetic reference exists, state that the public corpus does not support adverse-effect plausibility claims.
4. If compounding-record metadata is modeled, BUD is assumed present in the record summary; otherwise BUD should not be inferred.
5. Do not use licensed drug-information content or external reference text in the public corpus.

## Adverse Effect Support Values

- `not_needed`
- `synthetic_reference_consulted`
- `external_reference_needed`
- `not_supported_by_public_corpus`

## BUD Boundary

The public RAG project should not answer exact formulation-specific BUD questions unless a synthetic SOP or synthetic review summary explicitly contains that information.

## Notes and Limitations

The system may identify that an external drug-information review is needed. It should not fabricate adverse-effect claims or imply access to proprietary reference resources.
