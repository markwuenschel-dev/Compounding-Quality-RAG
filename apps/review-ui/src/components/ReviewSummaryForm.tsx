import { FormEvent, useState } from "react";
import type { ReviewSummaryRequest } from "../api/types";

type ReviewSummaryFormProps = {
  isSubmitting: boolean;
  onSubmit: (reviewSummary: ReviewSummaryRequest) => Promise<void>;
};

export function ReviewSummaryForm({
  isSubmitting,
  onSubmit,
}: ReviewSummaryFormProps) {
  const [recordReviewResult, setRecordReviewResult] = useState("");
  const [lotBatchPatternSummary, setLotBatchPatternSummary] = useState("");
  const [inventoryInspectionResult, setInventoryInspectionResult] =
    useState("");
  const [customerContextSummary, setCustomerContextSummary] = useState("");
  const [apiReferenceReviewResult, setApiReferenceReviewResult] = useState("");
  const [missingInformation, setMissingInformation] = useState("");
  const [evidenceLimitations, setEvidenceLimitations] = useState("");
  const [severeTriggersObserved, setSevereTriggersObserved] = useState("");

  const requiredFieldsComplete =
    recordReviewResult.trim().length > 0 &&
    lotBatchPatternSummary.trim().length > 0 &&
    inventoryInspectionResult.trim().length > 0 &&
    apiReferenceReviewResult.trim().length > 0;

  const canSubmit = requiredFieldsComplete && !isSubmitting;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!canSubmit) {
      return;
    }

    await onSubmit({
      recordReviewResult: recordReviewResult.trim(),
      lotBatchPatternSummary: lotBatchPatternSummary.trim(),
      inventoryInspectionResult: inventoryInspectionResult.trim(),
      customerContextSummary: normalizeOptionalText(customerContextSummary),
      apiReferenceReviewResult: apiReferenceReviewResult.trim(),
      missingInformation: parseList(missingInformation),
      evidenceLimitations: parseList(evidenceLimitations),
      severeTriggersObserved: parseList(severeTriggersObserved),
    });
  }

  return (
    <section className="card workflow-card" aria-label="Reviewer findings">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Step 3</p>
          <h2>Reviewer findings</h2>
          <p>
            Record what the human reviewer confirmed before requesting the
            final structured assessment.
          </p>
        </div>
      </div>

      <form
        className="form-stack"
        aria-label="Final assessment form"
        onSubmit={handleSubmit}
      >
        <div className="form-grid">
          <TextAreaField
            id="record-review-result"
            label="Record review result"
            value={recordReviewResult}
            onChange={setRecordReviewResult}
            required
          />

          <TextAreaField
            id="lot-batch-pattern-summary"
            label="Lot or batch pattern summary"
            value={lotBatchPatternSummary}
            onChange={setLotBatchPatternSummary}
            required
          />

          <TextAreaField
            id="inventory-inspection-result"
            label="Inventory inspection result"
            value={inventoryInspectionResult}
            onChange={setInventoryInspectionResult}
            required
          />

          <TextAreaField
            id="api-reference-review-result"
            label="API reference review result"
            value={apiReferenceReviewResult}
            onChange={setApiReferenceReviewResult}
            required
          />
        </div>

        <TextAreaField
          id="customer-context-summary"
          label="Customer context summary"
          value={customerContextSummary}
          onChange={setCustomerContextSummary}
          className="field-wide"
        />

        <div className="form-grid">
          <TextAreaField
            id="missing-information"
            label="Missing information"
            value={missingInformation}
            onChange={setMissingInformation}
            placeholder="One item per line"
          />

          <TextAreaField
            id="evidence-limitations"
            label="Evidence limitations"
            value={evidenceLimitations}
            onChange={setEvidenceLimitations}
            placeholder="One item per line"
          />
        </div>

        <TextAreaField
          id="severe-triggers-observed"
          label="Severe triggers observed"
          value={severeTriggersObserved}
          onChange={setSevereTriggersObserved}
          placeholder="One item per line; leave blank when none are confirmed"
          className="field-wide"
        />

        <div className="form-actions form-actions-split">
          <p className="required-note">Fields marked * are required.</p>
          <button className="primary-button" type="submit" disabled={!canSubmit}>
            {isSubmitting
              ? "Generating final assessment..."
              : "Generate final assessment"}
          </button>
        </div>
      </form>
    </section>
  );
}

type TextAreaFieldProps = {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  placeholder?: string;
  className?: string;
};

function TextAreaField({
  id,
  label,
  value,
  onChange,
  required = false,
  placeholder,
  className = "",
}: TextAreaFieldProps) {
  return (
    <div className={`field-group ${className}`}>
      <label htmlFor={id}>
        {label}
        {required ? " *" : ""}
      </label>
      <textarea
        id={id}
        rows={4}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
      />
    </div>
  );
}

function normalizeOptionalText(value: string): string | null {
  const trimmedValue = value.trim();

  return trimmedValue.length > 0 ? trimmedValue : null;
}

function parseList(value: string): string[] {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}
