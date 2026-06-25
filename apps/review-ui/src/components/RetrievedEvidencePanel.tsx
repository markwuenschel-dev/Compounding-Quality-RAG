import type { RetrieveResponse } from "../api/types";
import { formatClassifier } from "../utils/classifierLabels";
import { CollapsibleCard } from "./shared/CollapsibleCard";

type RetrievedEvidencePanelProps = {
  retrieval: RetrieveResponse;
  collapsed?: boolean;
  onToggleCollapsed?: () => void;
};

export function RetrievedEvidencePanel({
  retrieval,
  collapsed,
  onToggleCollapsed,
}: RetrievedEvidencePanelProps) {
  const summary = `Keyword · Top ${retrieval.topK} · ${retrieval.evidence.length} chunks`;

  return (
    <CollapsibleCard
      ariaLabel="Retrieved evidence"
      eyebrow="Retrieval layer"
      title="Retrieved evidence"
      description="Ranked synthetic source chunks the retriever returned for this concern. These chunks are what ground the checklist above."
      statusPill={<span className="success-pill">Top {retrieval.topK}</span>}
      summary={summary}
      collapsed={collapsed}
      onToggleCollapsed={onToggleCollapsed}
    >
      {retrieval.evidence.length === 0 ? (
        <p className="empty-state">No evidence chunks were retrieved.</p>
      ) : (
        <ol className="retrieval-list">
          {retrieval.evidence.map((citation, index) => (
            <li
              className="retrieval-card"
              key={citation.chunkId ?? `chunk-${index}`}
            >
              <div className="retrieval-card-heading">
                <span className="retrieval-rank" aria-label="Rank">
                  #{index + 1}
                </span>
                <div className="retrieval-source">
                  <span className="source-id">
                    {citation.sourceId ?? "Unknown source"}
                  </span>
                  <h4>{citation.sourceTitle ?? "Untitled source"}</h4>
                  <p className="retrieval-meta">
                    {formatMeta(citation.sourceType, citation.sectionHeading)}
                  </p>
                </div>
                <span className="retrieval-score" title="Retrieval score">
                  {formatScore(citation.score)}
                </span>
              </div>

              {citation.supportingText ? (
                <blockquote className="retrieval-quote">
                  {citation.supportingText}
                </blockquote>
              ) : (
                <p className="empty-state">No supporting text returned.</p>
              )}

              {citation.matchedTerms.length > 0 ? (
                <div className="retrieval-terms" aria-label="Matched terms">
                  {citation.matchedTerms.map((term, termIndex) => (
                    <span
                      className="match-term"
                      key={`${index}-${termIndex}`}
                    >
                      {term}
                    </span>
                  ))}
                </div>
              ) : null}
            </li>
          ))}
        </ol>
      )}
    </CollapsibleCard>
  );
}

function formatMeta(
  sourceType: string | null,
  sectionHeading: string | null,
): string {
  const parts = [
    sourceType ? formatClassifier(sourceType) : null,
    sectionHeading ? `Section: ${sectionHeading}` : "Section not provided",
  ].filter((part): part is string => part !== null);

  return parts.join(" · ");
}

function formatScore(score: number | null): string {
  return score === null || !Number.isFinite(score)
    ? "—"
    : score.toFixed(3);
}
