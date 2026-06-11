import { FormEvent, useState } from "react";

type ConcernInputFormProps = {
  isSubmitting: boolean;
  onSubmit: (concernText: string) => Promise<void>;
};

export function ConcernInputForm({
  isSubmitting,
  onSubmit,
}: ConcernInputFormProps) {
  const [concernText, setConcernText] = useState("");

  const trimmedConcernText = concernText.trim();
  const canSubmit = trimmedConcernText.length > 0 && !isSubmitting;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!canSubmit) {
      return;
    }

    await onSubmit(trimmedConcernText);
  }

  return (
    <form aria-label="Concern checklist form" onSubmit={handleSubmit}>
      <label htmlFor="concern-text">Concern text</label>
      <textarea
        id="concern-text"
        name="concernText"
        rows={6}
        value={concernText}
        onChange={(event) => setConcernText(event.target.value)}
        placeholder="Example: Dog vomited once after receiving a flavored compounded oral liquid."
      />

      <button type="submit" disabled={!canSubmit}>
        {isSubmitting ? "Generating checklist..." : "Generate checklist"}
      </button>
    </form>
  );
}