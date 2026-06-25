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

const MAX_CONCERN_LENGTH = 5_000;

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
  const [concernText, setConcernText] = useState(initialConcernText);
  const [submitAttempted, setSubmitAttempted] = useState(false);

  const trimmedConcernText = concernText.trim();
  const isBlank = trimmedConcernText.length === 0;
  const isTooLong = concernText.length > MAX_CONCERN_LENGTH;
  const showRequiredError = submitAttempted && isBlank;
  const showLengthError = isTooLong;
  const validationMessageId = "concern-validation-message";
  const describedByIds = [
    "concern-help",
    "concern-count",
    showRequiredError || showLengthError ? validationMessageId : null,
  ]
    .filter((id): id is string => id !== null)
    .join(" ");

  const canSubmit =
    !isBlank && !isTooLong && !isSubmitting && !isSubmissionDisabled;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitAttempted(true);

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
        noValidate
      >
        <div className="field-group">
          <label htmlFor="concern-text">Concern text</label>
          <textarea
            id="concern-text"
            name="concernText"
            rows={7}
            maxLength={MAX_CONCERN_LENGTH}
            value={concernText}
            onChange={(event) =>
              handleConcernTextChange(event.target.value)
            }
            placeholder="Example: Dog vomited once after receiving a flavored compounded oral liquid."
            aria-describedby={describedByIds}
            aria-invalid={showRequiredError || showLengthError}
          />
          <div className="field-meta">
            <span id="concern-help">Synthetic narrative only</span>
            <span id="concern-count">
              {concernText.length} / {MAX_CONCERN_LENGTH}
            </span>
          </div>
          {showRequiredError || showLengthError ? (
            <p
              id={validationMessageId}
              className="field-error"
              role="alert"
            >
              {showRequiredError
                ? "Concern text is required before generating a checklist."
                : `Concern text must be ${MAX_CONCERN_LENGTH} characters or fewer.`}
            </p>
          ) : null}
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
