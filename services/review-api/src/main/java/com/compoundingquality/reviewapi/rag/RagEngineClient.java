package com.compoundingquality.reviewapi.rag;

public interface RagEngineClient {

    RagChecklistResult createChecklist(RagChecklistRequest request);

    RagRetrieveResult retrieve(RagRetrieveRequest request);

    RagFinalAssessmentResult createFinalAssessment(RagFinalAssessmentRequest request);
}
