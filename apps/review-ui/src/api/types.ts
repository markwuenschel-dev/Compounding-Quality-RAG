export type ChecklistRequest = {
  concernText: string;
};

export type ChecklistResponse = {
  concernType: string | null;
  riskLane: string | null;
  reviewScope: string | null;
  initialTakeaway: string | null;
  requiredChecks: ChecklistItem[];
  missingInformation: string[];
  escalationTriggersToRuleOut: string[];
  evidence: ChecklistEvidenceCitation[];
  limitations: string[];
};

export type ChecklistItem = {
  key: string | null;
  label: string | null;
  required: boolean;
  reason: string | null;
};

export type ChecklistEvidenceCitation = {
  sourceId: string | null;
  sourceTitle: string | null;
  sectionHeading: string | null;
};

export type RetrieveRequest = {
  queryText: string;
  topK?: number | null;
};

export type RetrieveResponse = {
  queryText: string | null;
  topK: number;
  evidence: RetrieveEvidenceCitation[];
};

export type RetrieveEvidenceCitation = {
  chunkId: string | null;
  sourceId: string | null;
  sourceTitle: string | null;
  sourceType: string | null;
  sectionHeading: string | null;
  score: number | null;
  matchedTerms: string[];
  supportingText: string | null;
};

export type ReviewSummaryRequest = {
  recordReviewResult: string;
  lotBatchPatternSummary: string;
  inventoryInspectionResult: string;
  customerContextSummary?: string | null;
  apiReferenceReviewResult: string;
  missingInformation: string[];
  evidenceLimitations: string[];
  severeTriggersObserved: string[];
};

export type ReviewSummaryExtractRequest = {
  concernText: string;
  pharmacistNotes: string;
};

export type ExtractionEvidenceStatus =
  | "explicit"
  | "normalized"
  | "ambiguous"
  | "not_stated";

export type ReviewSummaryFieldEvidence = {
  fieldName: string;
  status: ExtractionEvidenceStatus;
  supportingQuote: string | null;
  explanation: string | null;
};

export type UnresolvedReviewQuestion = {
  fieldName: string;
  question: string;
  reason: string;
  decisionImpact: string[];
};

export type ReviewSummaryExtractResponse = {
  reviewSummary: ReviewSummaryRequest;
  fieldEvidence: ReviewSummaryFieldEvidence[];
  unresolvedQuestions: UnresolvedReviewQuestion[];
};

export type FinalAssessmentRequest = {
  concernText: string;
  topK?: number | null;
  reviewSummary: ReviewSummaryRequest;
};

export type FinalAssessmentResponse = {
  rawIntake: RawIntake | null;
  productContext: ProductContext | null;
  investigationRequirements: InvestigationRequirements | null;
  reviewSummary: ReviewSummary | null;
  derivedAssessment: DerivedAssessment | null;
};

export type RawIntake = {
  intakeSource: string | null;
  submitterRole: string | null;
  submissionPurpose: string | null;
  concernNarrative: string | null;
  starRating: number | null;
  reviewTextPresent: boolean | null;
  submitterSelectedClassification: string | null;
};

export type ProductContext = {
  species: string | null;
  dosageForm: string | null;
  productPlaceholder: string | null;
  flavorOrAttribute: string | null;
  budPresent: boolean | null;
  batchLotPresent: boolean | null;
};

export type InvestigationRequirements = {
  recordReviewRequired: boolean | null;
  lotBatchReviewRequired: boolean | null;
  inventoryInspectionRequired: boolean | null;
  trendScanRequired: boolean | null;
  customerOutreachRequired: boolean | null;
  frontlineGuidanceLookupRequired: boolean | null;
  technicalServicesResponseRequired: boolean | null;
};

export type ReviewSummary = {
  recordReviewResult: string | null;
  lotBatchPatternSummary: string | null;
  inventoryInspectionResult: string | null;
  customerContextSummary: string | null;
  apiReferenceReviewResult: string | null;
  missingInformation: string[];
  evidenceLimitations: string[];
  severeTriggersObserved: string[];
};

export type DerivedAssessment = {
  reviewerAssignedClassification: string | null;
  reviewerAssignedCategory: string | null;
  reviewerAssignedSubcategory: string | null;
  concernType: string | null;
  riskLane: string | null;
  reviewScope: string | null;
  escalationTriggers: string[];
  handlingPath: string | null;
  resolutionReviewRequired: boolean;
  resolutionOptions: string[];
  rationale: string | null;
};

export type ApiErrorResponse = {
  timestamp: string | null;
  status: number;
  error: string | null;
  message: string | null;
  path: string | null;
  requestId: string | null;
  fieldErrors: ApiFieldErrorDetail[];
  code: string | null;
};

export type ApiFieldErrorDetail = {
  field?: string | null;
  message?: string | null;
  rejectedValue?: unknown;
  code?: string | null;
};

export type ReadinessStatus = "READY" | "NOT_READY";

export type ReadinessCheck = {
  name: string;
  status: "UP" | "DOWN";
  detail: string;
};

export type ReadinessResponse = {
  status: ReadinessStatus;
  checks: ReadinessCheck[];
  timestamp: string;
};
