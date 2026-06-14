import { FormEvent, useState } from "react";

type InvestigationNotesFormProps = {
  initialNotes?: string;
  isSubmitting: boolean;
  isSubmissionDisabled?: boolean;
  onNotesChange?: (notes: string) => void;
  onSubmit: (notes: string) => Promise<void>;
};

export function InvestigationNotesForm({
  initialNotes = "",
  isSubmitting,
  isSubmissionDisabled = false,
  onNotesChange,
  onSubmit,
}: InvestigationNotesFormProps) {
  const [notes, setNotes] = useState(initialNotes);
  const cleanNotes = notes.trim();
  const canSubmit =
    cleanNotes.length > 0 &&
    !isSubmitting &&
    !isSubmissionDisabled;

  function handleChange(value: string) {
    setNotes(value);
    onNotesChange?.(value);
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (!canSubmit) {
      return;
    }

    await onSubmit(cleanNotes);
  }

  return (
    <section
      className="card workflow-card"
      aria-label="Pharmacist investigation"
    >
      <div className="section-heading">
        <div>
          <p className="eyebrow">Step 3</p>
          <h2>Pharmacist investigation notes</h2>
          <p>
            Paste the reviewer’s natural investigation notes.
            The extractor will propose structured findings for
            pharmacist confirmation.
          </p>
        </div>
      </div>

      <form
        className="form-stack"
        aria-label="Investigation notes form"
        onSubmit={handleSubmit}
      >
        <div className="field-group">
          <label htmlFor="pharmacist-notes">
            Investigation and actions taken
          </label>
          <textarea
            id="pharmacist-notes"
            rows={10}
            maxLength={10_000}
            value={notes}
            onChange={(event) =>
              handleChange(event.target.value)
            }
            placeholder="Example: Checked formula and worksheet; no discrepancy found. No inventory remained to inspect. Owner reports the dog recovered. No hospitalization or veterinarian allegation."
            aria-describedby="pharmacist-notes-help pharmacist-notes-count"
          />
          <div className="field-meta">
            <span id="pharmacist-notes-help">
              Paste messy notes as written; do not convert
              them into enum values.
            </span>
            <span id="pharmacist-notes-count">
              {notes.length} / 10000
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
              ? "Extracting reviewer findings..."
              : "Extract reviewer findings"}
          </button>
        </div>
      </form>
    </section>
  );
}
