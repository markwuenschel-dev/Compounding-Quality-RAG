import type { ChecklistResponse } from "../api/types";

type ChecklistPanelProps = {
  checklist: ChecklistResponse;
};

export function ChecklistPanel({ checklist }: ChecklistPanelProps) {
  return (
    <section className="card workflow-card" aria-label="Checklist result">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Step 2</p>
          <h2>Checklist result</h2>
          <p>
            Initial review guidance based on retrieved synthetic source
            evidence.
          </p>
        </div>
        <span className="success-pill">Checklist ready</span>
      </div>

      <div className="metric-grid">
        <Metric label="Concern type" value={checklist.concernType} />
        <Metric label="Risk lane" value={checklist.riskLane} />
        <Metric label="Review scope" value={checklist.reviewScope} />
      </div>

      {checklist.initialTakeaway ? (
        <section className="callout" aria-label="Initial takeaway">
          <h3>Initial takeaway</h3>
          <p>{checklist.initialTakeaway}</p>
        </section>
      ) : null}

      <section className="result-section" aria-label="Required checks">
        <div className="result-section-heading">
          <h3>Required checks</h3>
          <span>{checklist.requiredChecks.length}</span>
        </div>
        {checklist.requiredChecks.length === 0 ? (
          <p className="empty-state">No required checks returned.</p>
        ) : (
          <ul className="check-list">
            {checklist.requiredChecks.map((check) => (
              <li key={check.key ?? check.label ?? check.reason}>
                <span
                  className={`check-indicator ${
                    check.required ? "check-required" : "check-optional"
                  }`}
                  aria-hidden="true"
                >
                  {check.required ? "!" : "·"}
                </span>
                <div>
                  <strong>{check.label ?? check.key ?? "Unnamed check"}</strong>
                  <span className="item-tag">
                    {check.required ? "Required" : "Optional"}
                  </span>
                  {check.reason ? <p>{check.reason}</p> : null}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <ListSection
        label="Missing information"
        emptyMessage="No missing information returned."
        items={checklist.missingInformation}
      />

      <ListSection
        label="Escalation triggers to rule out"
        emptyMessage="No escalation triggers returned."
        items={checklist.escalationTriggersToRuleOut}
        tone="warning"
      />

      <section className="result-section" aria-label="Evidence">
        <div className="result-section-heading">
          <h3>Evidence</h3>
          <span>{checklist.evidence.length}</span>
        </div>
        {checklist.evidence.length === 0 ? (
          <p className="empty-state">No evidence returned.</p>
        ) : (
          <div className="evidence-grid">
            {checklist.evidence.map((citation) => (
              <article
                className="evidence-card"
                key={`${citation.sourceId}-${citation.sectionHeading}-${citation.sourceTitle}`}
              >
                <span className="source-id">
                  {citation.sourceId ?? "Unknown source"}
                </span>
                <h4>{citation.sourceTitle ?? "Untitled source"}</h4>
                <p>
                  {citation.sectionHeading
                    ? `Section: ${citation.sectionHeading}`
                    : "Section not provided"}
                </p>
              </article>
            ))}
          </div>
        )}
      </section>

      <ListSection
        label="Limitations"
        emptyMessage="No limitations returned."
        items={checklist.limitations}
        tone="muted"
      />
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
  tone?: "default" | "warning" | "muted";
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
