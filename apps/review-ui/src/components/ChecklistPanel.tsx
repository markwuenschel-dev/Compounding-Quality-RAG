import { useState } from "react";
import type { ChecklistItem, ChecklistResponse } from "../api/types";
import {
  formatClassifier,
  formatClassifierList,
} from "../utils/classifierLabels";
import { CollapsibleCard } from "./shared/CollapsibleCard";

type ChecklistPanelProps = {
  checklist: ChecklistResponse;
  collapsed?: boolean;
  onToggleCollapsed?: () => void;
};

export function ChecklistPanel({
  checklist,
  collapsed,
  onToggleCollapsed,
}: ChecklistPanelProps) {
  const [optionalOpen, setOptionalOpen] = useState(false);
  const [detailOpen, setDetailOpen] = useState(false);

  const concernTypeLabel = formatClassifier(checklist.concernType);
  const requiredChecks = checklist.requiredChecks.filter(
    (check) => check.required,
  );
  const optionalChecks = checklist.requiredChecks.filter(
    (check) => !check.required,
  );

  const gaps = [
    {
      label: "Missing information",
      items: checklist.missingInformation,
    },
    {
      label: "Escalation triggers to rule out",
      items: formatClassifierList(checklist.escalationTriggersToRuleOut),
    },
    { label: "Limitations", items: checklist.limitations },
  ].filter((group) => group.items.length > 0);

  const summary = `${concernTypeLabel ?? "Checklist ready"} · ${
    checklist.requiredChecks.length
  } checks`;

  return (
    <CollapsibleCard
      ariaLabel="Checklist result"
      eyebrow="Step 2"
      title="Checklist result"
      statusPill={<span className="success-pill">Checklist ready</span>}
      summary={summary}
      collapsed={collapsed}
      onToggleCollapsed={onToggleCollapsed}
    >
      <div className="checklist-lead">
        <div className="checklist-tags">
          {concernTypeLabel ? (
            <span className="checklist-tag checklist-tag-primary">
              {concernTypeLabel}
            </span>
          ) : null}
          {checklist.riskLane ? (
            <span className="checklist-tag">
              {formatClassifier(checklist.riskLane)}
            </span>
          ) : null}
          {checklist.reviewScope ? (
            <span className="checklist-tag">
              {formatClassifier(checklist.reviewScope)}
            </span>
          ) : null}
        </div>
        {checklist.initialTakeaway ? (
          <p className="checklist-takeaway">{checklist.initialTakeaway}</p>
        ) : null}
      </div>

      <section className="checklist-checks" aria-label="Required checks">
        <h3>What to check</h3>
        {checklist.requiredChecks.length === 0 ? (
          <p className="empty-state">No checks returned.</p>
        ) : (
          <>
            <ul className="check-list">
              {requiredChecks.map((check, index) => (
                <CheckRow key={`required-${index}`} check={check} />
              ))}
            </ul>

            {optionalChecks.length > 0 ? (
              <div className="checklist-optional">
                <button
                  type="button"
                  className="disclosure-toggle"
                  aria-expanded={optionalOpen}
                  onClick={() => setOptionalOpen((open) => !open)}
                >
                  <span>
                    {optionalOpen ? "Hide" : "Show"} {optionalChecks.length}{" "}
                    optional {optionalChecks.length === 1 ? "check" : "checks"}
                  </span>
                  <span
                    className={`collapsible-chevron ${
                      optionalOpen ? "is-open" : ""
                    }`}
                    aria-hidden="true"
                  >
                    ▾
                  </span>
                </button>
                {optionalOpen ? (
                  <ul className="check-list">
                    {optionalChecks.map((check, index) => (
                      <CheckRow
                        key={`optional-${index}`}
                        check={check}
                        optional
                      />
                    ))}
                  </ul>
                ) : null}
              </div>
            ) : null}
          </>
        )}
      </section>

      {gaps.length > 0 ? (
        <div className="checklist-detail">
          <button
            type="button"
            className="disclosure-toggle"
            aria-expanded={detailOpen}
            onClick={() => setDetailOpen((open) => !open)}
          >
            <span>Gaps &amp; caveats</span>
            <span
              className={`collapsible-chevron ${detailOpen ? "is-open" : ""}`}
              aria-hidden="true"
            >
              ▾
            </span>
          </button>
          {detailOpen ? (
            <div className="checklist-gaps">
              {gaps.map((group) => (
                <div className="checklist-gap" key={group.label}>
                  <h4>{group.label}</h4>
                  <ul className="compact-list">
                    {group.items.map((item, index) => (
                      <li key={`${group.label}-${index}`}>{item}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}
    </CollapsibleCard>
  );
}

function CheckRow({
  check,
  optional = false,
}: {
  check: ChecklistItem;
  optional?: boolean;
}) {
  return (
    <li>
      <span
        className={`check-indicator ${
          optional ? "check-optional" : "check-required"
        }`}
        aria-hidden="true"
      >
        {optional ? "○" : "✓"}
      </span>
      <div>
        <strong>{check.label ?? check.key ?? "Unnamed check"}</strong>
        {check.reason ? <p>{check.reason}</p> : null}
      </div>
    </li>
  );
}
