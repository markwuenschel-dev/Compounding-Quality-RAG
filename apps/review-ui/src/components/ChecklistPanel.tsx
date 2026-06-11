import type { ChecklistResponse } from "../api/types";

type ChecklistPanelProps = {
  checklist: ChecklistResponse;
};

export function ChecklistPanel({ checklist }: ChecklistPanelProps) {
  return (
    <section aria-label="Checklist result">
      <h2>Checklist result</h2>

      <dl>
        <div>
          <dt>Concern type</dt>
          <dd>{checklist.concernType ?? "Not provided"}</dd>
        </div>
        <div>
          <dt>Risk lane</dt>
          <dd>{checklist.riskLane ?? "Not provided"}</dd>
        </div>
        <div>
          <dt>Review scope</dt>
          <dd>{checklist.reviewScope ?? "Not provided"}</dd>
        </div>
      </dl>

      {checklist.initialTakeaway ? (
        <section aria-label="Initial takeaway">
          <h3>Initial takeaway</h3>
          <p>{checklist.initialTakeaway}</p>
        </section>
      ) : null}

      <section aria-label="Required checks">
        <h3>Required checks</h3>
        {checklist.requiredChecks.length === 0 ? (
          <p>No required checks returned.</p>
        ) : (
          <ul>
            {checklist.requiredChecks.map((check) => (
              <li key={check.key ?? check.label ?? check.reason}>
                <strong>{check.label ?? check.key ?? "Unnamed check"}</strong>
                {check.required ? " — required" : " — optional"}
                {check.reason ? <p>{check.reason}</p> : null}
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
      />

      <section aria-label="Evidence">
        <h3>Evidence</h3>
        {checklist.evidence.length === 0 ? (
          <p>No evidence returned.</p>
        ) : (
          <ul>
            {checklist.evidence.map((citation) => (
              <li
                key={`${citation.sourceId}-${citation.sectionHeading}-${citation.sourceTitle}`}
              >
                <strong>{citation.sourceId ?? "Unknown source"}</strong>
                {citation.sourceTitle ? ` — ${citation.sourceTitle}` : null}
                {citation.sectionHeading ? (
                  <p>Section: {citation.sectionHeading}</p>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </section>

      <ListSection
        label="Limitations"
        emptyMessage="No limitations returned."
        items={checklist.limitations}
      />
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