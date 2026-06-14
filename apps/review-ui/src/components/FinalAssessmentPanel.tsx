import { useState } from "react";
import type { FinalAssessmentResponse } from "../api/types";
import { formatAssessmentSummary } from "../utils/assessmentSummary";

type FinalAssessmentPanelProps = {
  assessment: FinalAssessmentResponse;
};

type CopyState = "idle" | "copied" | "error";

export function FinalAssessmentPanel({ assessment }: FinalAssessmentPanelProps) {
  const [copyState, setCopyState] = useState<CopyState>("idle");
  const derivedAssessment = assessment.derivedAssessment;

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
    <section
      className="card workflow-card final-card"
      aria-label="Final assessment result"
    >
      <div className="section-heading">
        <div>
          <p className="eyebrow">Step 4</p>
          <h2>Final assessment result</h2>
          <p>
            Structured review-support output derived from the concern,
            retrieved evidence, and reviewer-confirmed findings.
          </p>
        </div>
        <div className="final-actions">
          <span className="success-pill">Assessment ready</span>
          <button
            className="secondary-button"
            type="button"
            onClick={handleCopyAssessment}
            disabled={!derivedAssessment}
          >
            Copy assessment summary
          </button>
        </div>
      </div>

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
                {derivedAssessment.handlingPath ?? "Not provided"}
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
              value={derivedAssessment.reviewerAssignedClassification}
            />
            <Metric
              label="Category"
              value={derivedAssessment.reviewerAssignedCategory}
            />
            <Metric
              label="Subcategory"
              value={derivedAssessment.reviewerAssignedSubcategory}
            />
            <Metric label="Concern type" value={derivedAssessment.concernType} />
            <Metric label="Risk lane" value={derivedAssessment.riskLane} />
            <Metric label="Review scope" value={derivedAssessment.reviewScope} />
          </div>

          <ListSection
            label="Escalation triggers"
            emptyMessage="No escalation triggers returned."
            items={derivedAssessment.escalationTriggers}
            tone="warning"
          />

          <ListSection
            label="Resolution options"
            emptyMessage="No resolution options returned."
            items={derivedAssessment.resolutionOptions}
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
    </section>
  );
}

type MetricProps = {
  label: string;
  value: string | null;
};

function Metric({ label, value }: MetricProps) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value ?? "Not provided"}</strong>
    </div>
  );
}

type ListSectionProps = {
  label: string;
  emptyMessage: string;
  items: string[];
  tone?: "default" | "warning";
};

function ListSection({
  label,
  emptyMessage,
  items,
  tone = "default",
}: ListSectionProps) {
  return (
    <section
      className={`result-section result-section-${tone}`}
      aria-label={label}
    >
      <div className="result-section-heading">
        <h3>{label}</h3>
        <span>{items.length}</span>
      </div>
      {items.length === 0 ? (
        <p className="empty-state">{emptyMessage}</p>
      ) : (
        <ul className="compact-list">
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      )}
    </section>
  );
}
