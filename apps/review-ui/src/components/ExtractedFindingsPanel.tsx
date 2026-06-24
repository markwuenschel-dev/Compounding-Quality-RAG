import type {
  ReviewSummaryExtractResponse,
  ReviewSummaryFieldEvidence,
} from "../api/types";
import { formatClassifier } from "../utils/classifierLabels";
import { CollapsibleCard } from "./shared/CollapsibleCard";

type ExtractedFindingsPanelProps = {
  extraction: ReviewSummaryExtractResponse;
  collapsed?: boolean;
  onToggleCollapsed?: () => void;
};

export function ExtractedFindingsPanel({
  extraction,
  collapsed,
  onToggleCollapsed,
}: ExtractedFindingsPanelProps) {
  const summary = `${extraction.fieldEvidence.length} fields · ${extraction.unresolvedQuestions.length} questions`;

  return (
    <CollapsibleCard
      ariaLabel="Extracted reviewer findings"
      eyebrow="Extraction review"
      title="Extracted findings"
      description="Review the supporting note text, then confirm or correct the structured values below."
      summary={summary}
      collapsed={collapsed}
      onToggleCollapsed={onToggleCollapsed}
    >
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
                      .map((value) => formatClassifier(value) ?? value)
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
    </CollapsibleCard>
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
        <strong>{formatClassifier(evidence.fieldName)}</strong>
        <span
          className={`evidence-status evidence-status-${evidence.status}`}
        >
          {formatClassifier(evidence.status)}
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
