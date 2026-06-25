import type { RetrieveEvidenceCitation } from "../api/types";
import { formatClassifier } from "../utils/classifierLabels";

type EvidenceCardProps = {
  citation: RetrieveEvidenceCitation;
  rank: number;
  selected: boolean;
  selectable: boolean;
  onToggleSelected?: (chunkId: string, selected: boolean) => void;
};

export function EvidenceCard({
  citation,
  rank,
  selected,
  selectable,
  onToggleSelected,
}: EvidenceCardProps) {
  const canSelect = selectable && citation.chunkId !== null;

  return (
    <li className="retrieval-card">
      <div className="retrieval-card-heading">
        <span className="retrieval-rank" aria-label="Rank">
          #{rank}
        </span>
        {canSelect ? (
          <label className="retrieval-select">
            <input
              type="checkbox"
              checked={selected}
              onChange={(event) =>
                onToggleSelected?.(
                  citation.chunkId ?? "",
                  event.target.checked,
                )
              }
            />
            <span>Select evidence</span>
          </label>
        ) : null}
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
            <span className="match-term" key={`${rank}-${termIndex}`}>
              {term}
            </span>
          ))}
        </div>
      ) : null}
    </li>
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
