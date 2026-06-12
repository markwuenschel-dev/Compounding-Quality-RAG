import type { FinalAssessmentResponse } from "../api/types";

type FinalAssessmentPanelProps = {
  assessment: FinalAssessmentResponse;
};

export function FinalAssessmentPanel({ assessment }: FinalAssessmentPanelProps) {
  const derivedAssessment = assessment.derivedAssessment;

  return (
    <section aria-label="Final assessment result">
      <h2>Final assessment result</h2>

      {derivedAssessment ? (
        <>
          <dl>
            <div>
              <dt>Reviewer assigned classification</dt>
              <dd>
                {derivedAssessment.reviewerAssignedClassification ??
                  "Not provided"}
              </dd>
            </div>
            <div>
              <dt>Reviewer assigned category</dt>
              <dd>
                {derivedAssessment.reviewerAssignedCategory ?? "Not provided"}
              </dd>
            </div>
            <div>
              <dt>Reviewer assigned subcategory</dt>
              <dd>
                {derivedAssessment.reviewerAssignedSubcategory ??
                  "Not provided"}
              </dd>
            </div>
            <div>
              <dt>Concern type</dt>
              <dd>{derivedAssessment.concernType ?? "Not provided"}</dd>
            </div>
            <div>
              <dt>Risk lane</dt>
              <dd>{derivedAssessment.riskLane ?? "Not provided"}</dd>
            </div>
            <div>
              <dt>Review scope</dt>
              <dd>{derivedAssessment.reviewScope ?? "Not provided"}</dd>
            </div>
            <div>
              <dt>Handling path</dt>
              <dd>{derivedAssessment.handlingPath ?? "Not provided"}</dd>
            </div>
            <div>
              <dt>Resolution review required</dt>
              <dd>{formatBoolean(derivedAssessment.resolutionReviewRequired)}</dd>
            </div>
          </dl>

          <ListSection
            label="Escalation triggers"
            emptyMessage="No escalation triggers returned."
            items={derivedAssessment.escalationTriggers}
          />

          <ListSection
            label="Resolution options"
            emptyMessage="No resolution options returned."
            items={derivedAssessment.resolutionOptions}
          />

          {derivedAssessment.rationale ? (
            <section aria-label="Rationale">
              <h3>Rationale</h3>
              <p>{derivedAssessment.rationale}</p>
            </section>
          ) : null}
        </>
      ) : (
        <p>No derived assessment returned.</p>
      )}
    </section>
  );
}

type ListSectionProps = {
  label: string;
  emptyMessage: string;
  items: string[];
};

function ListSection({ label, emptyMessage, items }: ListSectionProps) {
  return (
    <section aria-label={label}>
      <h3>{label}</h3>
      {items.length === 0 ? (
        <p>{emptyMessage}</p>
      ) : (
        <ul>
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      )}
    </section>
  );
}

function formatBoolean(value: boolean): string {
  return value ? "Yes" : "No";
}