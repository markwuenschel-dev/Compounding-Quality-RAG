import type {
  ReviewSummaryExtractResponse,
  ReviewSummaryFieldEvidence,
} from "../api/types";

type ExtractedFindingsPanelProps = {
  extraction: ReviewSummaryExtractResponse;
};

export function ExtractedFindingsPanel({
  extraction,
}: ExtractedFindingsPanelProps) {
  return (
    <section
      className="card workflow-card"
      aria-label="Extracted reviewer findings"
    >
      <div className="section-heading">
        <div>
          <p className="eyebrow">Extraction review</p>
          <h2>Extracted findings</h2>
          <p>
            Review the supporting note text, then confirm or
            correct the structured values below.
          </p>
        </div>
      </div>

      <div className="extraction-evidence-grid">
        {extraction.fieldEvidence.map((evidence) => (
          <EvidenceCard
            key={evidence.fieldName}
            evidence={evidence}
          />
        ))}
      </div>

      <div className="unresolved-section">
        <h3>Decision-relevant questions</h3>

        {extraction.unresolvedQuestions.length === 0 ? (
          <p className="empty-state">
            No unresolved decision-relevant questions were
            identified.
          </p>
        ) : (
          <ul className="question-list">
            {extraction.unresolvedQuestions.map((question) => (
              <li key={question.fieldName}>
                <strong>{question.question}</strong>
                <span>{question.reason}</span>
                {question.decisionImpact.length > 0 ? (
                  <small>
                    Could affect:{" "}
                    {question.decisionImpact
                      .map(humanize)
                      .join(", ")}
                  </small>
                ) : null}
              </li>
            ))}
          </ul>
        )}

        <p className="helper-copy">
          Update the investigation notes and extract again
          when a question can be answered. Otherwise, preserve
          the uncertainty in the editable findings.
        </p>
      </div>
    </section>
  );
}

function EvidenceCard({
  evidence,
}: {
  evidence: ReviewSummaryFieldEvidence;
}) {
  return (
    <article className="extraction-evidence-card">
      <div className="evidence-card-heading">
        <strong>{humanize(evidence.fieldName)}</strong>
        <span
          className={`evidence-status evidence-status-${evidence.status}`}
        >
          {humanize(evidence.status)}
        </span>
      </div>

      {evidence.supportingQuote ? (
        <blockquote>{evidence.supportingQuote}</blockquote>
      ) : (
        <p className="empty-state">
          No direct supporting sentence identified.
        </p>
      )}

      {evidence.explanation ? (
        <p>{evidence.explanation}</p>
      ) : null}
    </article>
  );
}

function humanize(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}
