import { useState } from "react";
import type {
  FinalAssessmentResponse,
  InvestigationRequirements,
  ProductContext,
  RawIntake,
  ReviewSummary,
} from "../api/types";
import { formatAssessmentSummary } from "../utils/assessmentSummary";
import {
  formatClassifier,
  formatClassifierList,
} from "../utils/classifierLabels";
import { CollapsibleCard } from "./shared/CollapsibleCard";
import { ListSection } from "./shared/ListSection";
import { Metric } from "./shared/Metric";

type FinalAssessmentPanelProps = {
  assessment: FinalAssessmentResponse;
  collapsed?: boolean;
  onToggleCollapsed?: () => void;
};

type CopyState = "idle" | "copied" | "error";

export function FinalAssessmentPanel({
  assessment,
  collapsed,
  onToggleCollapsed,
}: FinalAssessmentPanelProps) {
  const [copyState, setCopyState] = useState<CopyState>("idle");
  const [pipelineOpen, setPipelineOpen] = useState(false);
  const derivedAssessment = assessment.derivedAssessment;

  const summary =
    formatClassifier(derivedAssessment?.handlingPath ?? null) ??
    "Assessment ready";

  const hasPipelineDetail = Boolean(
    assessment.rawIntake ||
      assessment.productContext ||
      assessment.investigationRequirements ||
      assessment.reviewSummary,
  );

  async function handleCopyAssessment() {
    try {
      if (!navigator.clipboard?.writeText) {
        throw new Error("Clipboard API unavailable");
      }

      await navigator.clipboard.writeText(formatAssessmentSummary(assessment));
      setCopyState("copied");
    } catch {
      setCopyState("error");
    }
  }

  return (
    <CollapsibleCard
      ariaLabel="Final assessment result"
      className="final-card"
      eyebrow="Step 4"
      title="Final assessment result"
      description="Structured review-support output derived from the concern, retrieved evidence, and reviewer-confirmed findings."
      summary={summary}
      collapsed={collapsed}
      onToggleCollapsed={onToggleCollapsed}
      statusPill={<span className="success-pill">Assessment ready</span>}
      actions={
        <button
          className="secondary-button"
          type="button"
          onClick={handleCopyAssessment}
          disabled={!derivedAssessment}
        >
          Copy assessment summary
        </button>
      }
    >
      <p className="copy-feedback" aria-live="polite">
        {copyState === "copied" ? "Copied assessment summary." : null}
        {copyState === "error"
          ? "Unable to copy assessment summary."
          : null}
      </p>

      {derivedAssessment ? (
        <>
          <div className="assessment-banner">
            <div>
              <span>Recommended handling path</span>
              <strong>
                {formatClassifier(derivedAssessment.handlingPath) ??
                  "Not provided"}
              </strong>
            </div>
            <div>
              <span>Resolution review required</span>
              <strong>
                {derivedAssessment.resolutionReviewRequired ? "Yes" : "No"}
              </strong>
            </div>
          </div>

          <div className="metric-grid">
            <Metric
              label="Classification"
              value={formatClassifier(
                derivedAssessment.reviewerAssignedClassification,
              )}
            />
            <Metric
              label="Category"
              value={formatClassifier(
                derivedAssessment.reviewerAssignedCategory,
              )}
            />
            <Metric
              label="Subcategory"
              value={formatClassifier(
                derivedAssessment.reviewerAssignedSubcategory,
              )}
            />
            <Metric
              label="Concern type"
              value={formatClassifier(derivedAssessment.concernType)}
            />
            <Metric
              label="Risk lane"
              value={formatClassifier(derivedAssessment.riskLane)}
            />
            <Metric
              label="Review scope"
              value={formatClassifier(derivedAssessment.reviewScope)}
            />
          </div>

          <ListSection
            label="Escalation triggers"
            emptyMessage="No escalation triggers returned."
            items={formatClassifierList(derivedAssessment.escalationTriggers)}
            tone="warning"
          />

          <ListSection
            label="Resolution options"
            emptyMessage="No resolution options returned."
            items={formatClassifierList(derivedAssessment.resolutionOptions)}
          />

          {derivedAssessment.rationale ? (
            <section className="callout rationale-card" aria-label="Rationale">
              <h3>Rationale</h3>
              <p>{derivedAssessment.rationale}</p>
            </section>
          ) : null}
        </>
      ) : (
        <p className="empty-state">No derived assessment returned.</p>
      )}

      {hasPipelineDetail ? (
        <div className="pipeline-detail">
          <button
            type="button"
            className="pipeline-detail-toggle"
            aria-expanded={pipelineOpen}
            onClick={() => setPipelineOpen((open) => !open)}
          >
            <span>Full pipeline output</span>
            <span
              className={`collapsible-chevron ${pipelineOpen ? "is-open" : ""}`}
              aria-hidden="true"
            >
              ▾
            </span>
          </button>

          {pipelineOpen ? (
            <>
              <p className="pipeline-detail-note">
                Every field the review pipeline produced, including the
                upstream intake, product context, and confirmed review
                summary that grounded the assessment above.
              </p>

              {assessment.rawIntake ? (
                <RawIntakeSection rawIntake={assessment.rawIntake} />
              ) : null}

              {assessment.productContext ? (
                <ProductContextSection
                  productContext={assessment.productContext}
                />
              ) : null}

              {assessment.investigationRequirements ? (
                <InvestigationRequirementsSection
                  requirements={assessment.investigationRequirements}
                />
              ) : null}

              {assessment.reviewSummary ? (
                <ReviewSummarySection
                  reviewSummary={assessment.reviewSummary}
                />
              ) : null}
            </>
          ) : null}
        </div>
      ) : null}
    </CollapsibleCard>
  );
}

function RawIntakeSection({ rawIntake }: { rawIntake: RawIntake }) {
  return (
    <section className="result-section" aria-label="Raw intake">
      <div className="result-section-heading">
        <h3>Raw intake</h3>
      </div>
      <div className="metric-grid">
        <Metric
          label="Intake source"
          value={formatClassifier(rawIntake.intakeSource)}
        />
        <Metric
          label="Submitter role"
          value={formatClassifier(rawIntake.submitterRole)}
        />
        <Metric
          label="Submission purpose"
          value={formatClassifier(rawIntake.submissionPurpose)}
        />
        <Metric
          label="Submitter classification"
          value={formatClassifier(rawIntake.submitterSelectedClassification)}
        />
        <Metric label="Star rating" value={numberOrNull(rawIntake.starRating)} />
        <Metric
          label="Review text present"
          value={boolText(rawIntake.reviewTextPresent)}
        />
      </div>
      {rawIntake.concernNarrative ? (
        <section className="callout" aria-label="Concern narrative">
          <h3>Concern narrative</h3>
          <p>{rawIntake.concernNarrative}</p>
        </section>
      ) : null}
    </section>
  );
}

function ProductContextSection({
  productContext,
}: {
  productContext: ProductContext;
}) {
  return (
    <section className="result-section" aria-label="Product context">
      <div className="result-section-heading">
        <h3>Product context</h3>
      </div>
      <div className="metric-grid">
        <Metric
          label="Species"
          value={formatClassifier(productContext.species)}
        />
        <Metric
          label="Dosage form"
          value={formatClassifier(productContext.dosageForm)}
        />
        <Metric label="Product" value={productContext.productPlaceholder} />
        <Metric
          label="Flavor or attribute"
          value={productContext.flavorOrAttribute}
        />
        <Metric
          label="BUD present"
          value={boolText(productContext.budPresent)}
        />
        <Metric
          label="Batch or lot present"
          value={boolText(productContext.batchLotPresent)}
        />
      </div>
    </section>
  );
}

function InvestigationRequirementsSection({
  requirements,
}: {
  requirements: InvestigationRequirements;
}) {
  const fields: Array<{ label: string; value: boolean | null }> = [
    { label: "Record review", value: requirements.recordReviewRequired },
    { label: "Lot or batch review", value: requirements.lotBatchReviewRequired },
    {
      label: "Inventory inspection",
      value: requirements.inventoryInspectionRequired,
    },
    { label: "Trend scan", value: requirements.trendScanRequired },
    { label: "Customer outreach", value: requirements.customerOutreachRequired },
    {
      label: "Frontline guidance lookup",
      value: requirements.frontlineGuidanceLookupRequired,
    },
    {
      label: "Technical services response",
      value: requirements.technicalServicesResponseRequired,
    },
  ];

  return (
    <section
      className="result-section"
      aria-label="Investigation requirements"
    >
      <div className="result-section-heading">
        <h3>Investigation requirements</h3>
      </div>
      <div className="metric-grid">
        {fields.map((field) => (
          <Metric
            key={field.label}
            label={field.label}
            value={boolText(field.value)}
          />
        ))}
      </div>
    </section>
  );
}

function ReviewSummarySection({
  reviewSummary,
}: {
  reviewSummary: ReviewSummary;
}) {
  return (
    <section
      className="result-section"
      aria-label="Confirmed review summary"
    >
      <div className="result-section-heading">
        <h3>Confirmed review summary</h3>
      </div>
      <div className="metric-grid">
        <Metric
          label="Record review result"
          value={formatClassifier(reviewSummary.recordReviewResult)}
        />
        <Metric
          label="Lot or batch pattern"
          value={formatClassifier(reviewSummary.lotBatchPatternSummary)}
        />
        <Metric
          label="Inventory inspection result"
          value={formatClassifier(reviewSummary.inventoryInspectionResult)}
        />
        <Metric
          label="API reference review result"
          value={formatClassifier(reviewSummary.apiReferenceReviewResult)}
        />
      </div>

      {reviewSummary.customerContextSummary ? (
        <section className="callout" aria-label="Customer context summary">
          <h3>Customer context summary</h3>
          <p>{reviewSummary.customerContextSummary}</p>
        </section>
      ) : null}

      <ListSection
        label="Missing information"
        emptyMessage="No missing information returned."
        items={reviewSummary.missingInformation}
      />

      <ListSection
        label="Evidence limitations"
        emptyMessage="No evidence limitations returned."
        items={reviewSummary.evidenceLimitations}
        tone="muted"
      />

      <ListSection
        label="Severe triggers observed"
        emptyMessage="No severe triggers observed."
        items={formatClassifierList(reviewSummary.severeTriggersObserved)}
        tone="warning"
      />
    </section>
  );
}

function numberOrNull(value: number | null): string | null {
  return value === null ? null : String(value);
}

function boolText(value: boolean | null): string {
  if (value === null) {
    return "Not provided";
  }

  return value ? "Yes" : "No";
}
