import { FormEvent, ReactNode, useState } from "react";
import { CollapsibleCard } from "./shared/CollapsibleCard";

type ConcernInputFormProps = {
  isSubmitting: boolean;
  isSubmissionDisabled?: boolean;
  onSubmit: (concernText: string) => Promise<void>;
  initialConcernText?: string;
  onConcernTextChange?: (concernText: string) => void;
  collapsed?: boolean;
  onToggleCollapsed?: () => void;
  summary?: ReactNode;
};

export function ConcernInputForm({
  isSubmitting,
  isSubmissionDisabled = false,
  onSubmit,
  initialConcernText = "",
  onConcernTextChange,
  collapsed,
  onToggleCollapsed,
  summary,
}: ConcernInputFormProps) {
  const [concernText, setConcernText] =
    useState(initialConcernText);

  const trimmedConcernText = concernText.trim();
  const canSubmit =
    trimmedConcernText.length > 0 &&
    !isSubmitting &&
    !isSubmissionDisabled;

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (!canSubmit) {
      return;
    }

    await onSubmit(trimmedConcernText);
  }

  function handleConcernTextChange(value: string) {
    setConcernText(value);
    onConcernTextChange?.(value);
  }

  return (
    <CollapsibleCard
      ariaLabel="Concern narrative"
      eyebrow="Step 1"
      title="Concern narrative"
      description="Enter a synthetic concern exactly as it might arrive through an intake workflow."
      summary={summary}
      collapsed={collapsed}
      onToggleCollapsed={onToggleCollapsed}
    >
      <form
        className="form-stack"
        aria-label="Concern checklist form"
        onSubmit={handleSubmit}
      >
        <div className="field-group">
          <label htmlFor="concern-text">
            Concern text
          </label>
          <textarea
            id="concern-text"
            name="concernText"
            rows={7}
            maxLength={5_000}
            value={concernText}
            onChange={(event) =>
              handleConcernTextChange(event.target.value)
            }
            placeholder="Example: Dog vomited once after receiving a flavored compounded oral liquid."
            aria-describedby="concern-help concern-count"
          />
          <div className="field-meta">
            <span id="concern-help">
              Synthetic narrative only
            </span>
            <span id="concern-count">
              {concernText.length} / 5000
            </span>
          </div>
        </div>

        <div className="form-actions">
          <button
            className="primary-button"
            type="submit"
            disabled={!canSubmit}
          >
            {isSubmitting
              ? "Generating checklist..."
              : "Generate checklist"}
          </button>
        </div>
      </form>
    </CollapsibleCard>
  );
}
