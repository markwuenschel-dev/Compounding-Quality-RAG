import type { RetrieveResponse } from "../api/types";
import { EvidenceCard } from "./EvidenceCard";
import { CollapsibleCard } from "./shared/CollapsibleCard";

type RetrievedEvidencePanelProps = {
  retrieval: RetrieveResponse;
  collapsed?: boolean;
  onToggleCollapsed?: () => void;
  selectedChunkIds?: string[];
  onToggleSelected?: (chunkId: string, selected: boolean) => void;
  isStale?: boolean;
};

export function RetrievedEvidencePanel({
  retrieval,
  collapsed,
  onToggleCollapsed,
  selectedChunkIds = [],
  onToggleSelected,
  isStale = false,
}: RetrievedEvidencePanelProps) {
  const retrievalLabel = retrieval.queryText ? "Retrieved" : "Keyword";
  const summary = `${retrievalLabel} · Top ${retrieval.topK} · ${retrieval.evidence.length} chunks`;
  const selectable = onToggleSelected !== undefined;

  return (
    <CollapsibleCard
      ariaLabel="Retrieved evidence"
      eyebrow="Retrieval layer"
      title="Retrieved evidence"
      description="Ranked synthetic source chunks returned for the current retrieval request. These chunks make the grounding boundary visible to the reviewer."
      statusPill={<span className="success-pill">Top {retrieval.topK}</span>}
      summary={summary}
      collapsed={collapsed}
      onToggleCollapsed={onToggleCollapsed}
    >
      {isStale ? (
        <p className="warning-state" role="status">
          This evidence may be stale because the concern text changed after
          retrieval. Retrieve evidence again before relying on these chunks.
        </p>
      ) : null}

      {retrieval.evidence.length === 0 ? (
        <p className="empty-state">No evidence chunks were retrieved.</p>
      ) : (
        <ol className="retrieval-list">
          {retrieval.evidence.map((citation, index) => {
            const chunkId = citation.chunkId ?? `chunk-${index}`;

            return (
              <EvidenceCard
                key={chunkId}
                citation={citation}
                rank={index + 1}
                selected={
                  citation.chunkId !== null &&
                  selectedChunkIds.includes(citation.chunkId)
                }
                selectable={selectable}
                onToggleSelected={onToggleSelected}
              />
            );
          })}
        </ol>
      )}
    </CollapsibleCard>
  );
}
