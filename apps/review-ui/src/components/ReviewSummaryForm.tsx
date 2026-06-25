import { FormEvent, useEffect, useState } from "react";
import type { ReviewSummaryRequest } from "../api/types";
import { CollapsibleCard } from "./shared/CollapsibleCard";

type ReviewSummaryFormProps = {
  isSubmitting: boolean;
  onSubmit: (
    reviewSummary: ReviewSummaryRequest,
  ) => Promise<void>;
  initialValues?: ReviewSummaryRequest;
  isSubmissionDisabled?: boolean;
  collapsed?: boolean;
  onToggleCollapsed?: () => void;
};

type Option = {
  value: string;
  label: string;
};

const RECORD_REVIEW_OPTIONS: Option[] = [
  {
    value: "no_discrepancy_found",
    label: "No discrepancy found",
  },
  {
    value: "documentation_incomplete",
    label: "Documentation incomplete",
  },
  {
    value: "documentation_discrepancy_found",
    label: "Documentation discrepancy found",
  },
  {
    value: "not_applicable",
    label: "Not applicable",
  },
];

const LOT_BATCH_OPTIONS: Option[] = [
  {
    value: "no_similar_batch_concerns_found",
    label: "No similar batch concerns found",
  },
  {
    value: "similar_concern_same_batch_found",
    label: "Similar concern in same batch found",
  },
  {
    value:
      "similar_concern_same_medication_dosage_form_found",
    label:
      "Similar concern for same medication or dosage form",
  },
  {
    value: "trend_threshold_met",
    label: "Trend threshold met",
  },
  {
    value: "unavailable",
    label: "Unavailable",
  },
  {
    value: "not_applicable",
    label: "Not applicable",
  },
];

const INVENTORY_OPTIONS: Option[] = [
  {
    value: "no_inventory_available",
    label: "No inventory available",
  },
  {
    value: "no_visual_concern_found",
    label: "No visual concern found",
  },
  {
    value: "visual_concern_found",
    label: "Visual concern found",
  },
  {
    value: "not_checked",
    label: "Not checked",
  },
  {
    value: "not_applicable",
    label: "Not applicable",
  },
];

const API_REFERENCE_OPTIONS: Option[] = [
  {
    value: "not_needed",
    label: "Not needed",
  },
  {
    value: "synthetic_reference_consulted",
    label: "Synthetic reference consulted",
  },
  {
    value: "external_reference_consulted",
    label: "External reference consulted",
  },
  {
    value: "external_reference_needed",
    label: "External reference needed",
  },
  {
    value: "not_supported_by_public_corpus",
    label: "Not supported by public corpus",
  },
];

const SEVERE_TRIGGER_OPTIONS: Option[] = [
  {
    value: "pet_death",
    label: "Pet death",
  },
  {
    value: "pet_hospitalization",
    label: "Pet hospitalization",
  },
  {
    value: "threatened_legal_action",
    label: "Threatened legal action",
  },
  {
    value: "veterinarian_alleges_harm_from_compound",
    label: "Veterinarian alleges harm from compound",
  },
  {
    value: "possible_contamination",
    label: "Possible contamination",
  },
  {
    value: "wrong_patient_or_wrong_medication",
    label: "Wrong patient or wrong medication",
  },
  {
    value:
      "repeat_issue_same_lot_or_batch_with_conditions",
    label: "Repeat issue in same lot or batch",
  },
  {
    value: "rare_regulatory_or_compliance_concern",
    label: "Regulatory or compliance concern",
  },
];

const EMPTY_REVIEW_SUMMARY: ReviewSummaryRequest = {
  recordReviewResult: "",
  lotBatchPatternSummary: "",
  inventoryInspectionResult: "",
  customerContextSummary: null,
  apiReferenceReviewResult: "",
  missingInformation: [],
  evidenceLimitations: [],
  severeTriggersObserved: [],
};

export function ReviewSummaryForm({
  isSubmitting,
  onSubmit,
  initialValues = EMPTY_REVIEW_SUMMARY,
  isSubmissionDisabled = false,
  collapsed,
  onToggleCollapsed,
}: ReviewSummaryFormProps) {
  const [
    recordReviewResult,
    setRecordReviewResult,
  ] = useState(initialValues.recordReviewResult);
  const [
    lotBatchPatternSummary,
    setLotBatchPatternSummary,
  ] = useState(initialValues.lotBatchPatternSummary);
  const [
    inventoryInspectionResult,
    setInventoryInspectionResult,
  ] = useState(initialValues.inventoryInspectionResult);
  const [
    customerContextSummary,
    setCustomerContextSummary,
  ] = useState(initialValues.customerContextSummary ?? "");
  const [
    apiReferenceReviewResult,
    setApiReferenceReviewResult,
  ] = useState(initialValues.apiReferenceReviewResult);
  const [
    missingInformation,
    setMissingInformation,
  ] = useState(initialValues.missingInformation.join("\n"));
  const [
    evidenceLimitations,
    setEvidenceLimitations,
  ] = useState(initialValues.evidenceLimitations.join("\n"));
  const [
    severeTriggersObserved,
    setSevereTriggersObserved,
  ] = useState<string[]>(initialValues.severeTriggersObserved);

  const initialValuesKey = serializeReviewSummary(initialValues);

  useEffect(() => {
    const nextInitialValues = parseReviewSummaryKey(initialValuesKey);

    setRecordReviewResult(nextInitialValues.recordReviewResult);
    setLotBatchPatternSummary(nextInitialValues.lotBatchPatternSummary);
    setInventoryInspectionResult(nextInitialValues.inventoryInspectionResult);
    setCustomerContextSummary(
      nextInitialValues.customerContextSummary ?? "",
    );
    setApiReferenceReviewResult(
      nextInitialValues.apiReferenceReviewResult,
    );
    setMissingInformation(
      nextInitialValues.missingInformation.join("\n"),
    );
    setEvidenceLimitations(
      nextInitialValues.evidenceLimitations.join("\n"),
    );
    setSevereTriggersObserved(
      nextInitialValues.severeTriggersObserved,
    );
  }, [initialValuesKey]);

  const requiredFieldsComplete =
    recordReviewResult.length > 0 &&
    lotBatchPatternSummary.length > 0 &&
    inventoryInspectionResult.length > 0 &&
    apiReferenceReviewResult.length > 0;

  const canSubmit =
    requiredFieldsComplete && !isSubmitting && !isSubmissionDisabled;

  function toggleSevereTrigger(
    trigger: string,
    checked: boolean,
  ) {
    setSevereTriggersObserved((current) =>
      checked
        ? [...new Set([...current, trigger])]
        : current.filter((value) => value !== trigger),
    );
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!canSubmit) {
      return;
    }

    await onSubmit({
      recordReviewResult,
      lotBatchPatternSummary,
      inventoryInspectionResult,
      customerContextSummary:
        normalizeOptionalText(customerContextSummary),
      apiReferenceReviewResult,
      missingInformation: parseList(missingInformation),
      evidenceLimitations: parseList(evidenceLimitations),
      severeTriggersObserved,
    });
  }

  return (
    <CollapsibleCard
      ariaLabel="Reviewer findings"
      eyebrow="Step 3"
      title="Confirm reviewer findings"
      description="The extractor supplied valid structured values. Confirm or correct them before generating the final assessment."
      summary="Reviewer findings confirmed"
      collapsed={collapsed}
      onToggleCollapsed={onToggleCollapsed}
    >
      <form
        className="form-stack"
        aria-label="Final assessment form"
        onSubmit={handleSubmit}
        noValidate
      >
        <div className="form-grid">
          <SelectField
            id="record-review-result"
            label="Record review result"
            value={recordReviewResult}
            options={RECORD_REVIEW_OPTIONS}
            onChange={setRecordReviewResult}
            required
          />

          <SelectField
            id="lot-batch-pattern-summary"
            label="Lot or batch pattern summary"
            value={lotBatchPatternSummary}
            options={LOT_BATCH_OPTIONS}
            onChange={setLotBatchPatternSummary}
            required
          />

          <SelectField
            id="inventory-inspection-result"
            label="Inventory inspection result"
            value={inventoryInspectionResult}
            options={INVENTORY_OPTIONS}
            onChange={setInventoryInspectionResult}
            required
          />

          <SelectField
            id="api-reference-review-result"
            label="API reference review result"
            value={apiReferenceReviewResult}
            options={API_REFERENCE_OPTIONS}
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

        <fieldset className="checkbox-fieldset">
          <legend>Severe triggers observed</legend>
          <p id="severe-triggers-help">
            Leave all options unchecked when no severe trigger was
            affirmatively confirmed.
          </p>
          <div
            className="checkbox-grid"
            aria-describedby="severe-triggers-help"
          >
            {SEVERE_TRIGGER_OPTIONS.map((option) => (
              <label key={option.value}>
                <input
                  type="checkbox"
                  value={option.value}
                  checked={severeTriggersObserved.includes(
                    option.value,
                  )}
                  onChange={(event) =>
                    toggleSevereTrigger(
                      option.value,
                      event.target.checked,
                    )
                  }
                />
                <span>{option.label}</span>
              </label>
            ))}
          </div>
        </fieldset>

        <div className="form-actions form-actions-split">
          <p className="required-note" aria-live="polite">
            {requiredFieldsComplete
              ? "Structured selections are submitted as canonical enum values."
              : "Complete all required structured selections before generating the final assessment."}
          </p>
          <button
            className="primary-button"
            type="submit"
            disabled={!canSubmit}
          >
            {isSubmitting
              ? "Generating final assessment..."
              : "Generate final assessment"}
          </button>
        </div>
      </form>
    </CollapsibleCard>
  );
}

type SelectFieldProps = {
  id: string;
  label: string;
  value: string;
  options: Option[];
  onChange: (value: string) => void;
  required?: boolean;
};

function SelectField({
  id,
  label,
  value,
  options,
  onChange,
  required = false,
}: SelectFieldProps) {
  const helpId = `${id}-help`;
  const showRequired = required && value.length === 0;

  return (
    <div className="field-group">
      <label htmlFor={id}>
        {label}
        {required ? " *" : ""}
      </label>
      <select
        id={id}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        required={required}
        aria-describedby={helpId}
        aria-invalid={showRequired}
      >
        <option value="">Select a value</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <p id={helpId} className="field-helper">
        {showRequired
          ? "Required before final assessment."
          : "Submitted as a canonical enum value."}
      </p>
    </div>
  );
}

type TextAreaFieldProps = {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
};

function TextAreaField({
  id,
  label,
  value,
  onChange,
  placeholder,
  className = "",
}: TextAreaFieldProps) {
  return (
    <div className={`field-group ${className}`}>
      <label htmlFor={id}>{label}</label>
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

function serializeReviewSummary(
  reviewSummary: ReviewSummaryRequest,
): string {
  return JSON.stringify({
    recordReviewResult: reviewSummary.recordReviewResult,
    lotBatchPatternSummary: reviewSummary.lotBatchPatternSummary,
    inventoryInspectionResult: reviewSummary.inventoryInspectionResult,
    customerContextSummary: reviewSummary.customerContextSummary ?? null,
    apiReferenceReviewResult: reviewSummary.apiReferenceReviewResult,
    missingInformation: reviewSummary.missingInformation,
    evidenceLimitations: reviewSummary.evidenceLimitations,
    severeTriggersObserved: reviewSummary.severeTriggersObserved,
  });
}

function parseReviewSummaryKey(
  reviewSummaryKey: string,
): ReviewSummaryRequest {
  return JSON.parse(reviewSummaryKey) as ReviewSummaryRequest;
}
