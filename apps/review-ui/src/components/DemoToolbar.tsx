import type { DemoCaseId } from "../demo/demoCases";
import { DEMO_CASES } from "../demo/demoCases";

export const TOP_K_OPTIONS = [1, 3, 5, 8] as const;

type DemoToolbarProps = {
  selectedDemoCaseId: DemoCaseId;
  onSelectedDemoCaseChange: (demoCaseId: DemoCaseId) => void;
  onLoadDemoCase: () => void;
  onStartOver: () => void;
  canStartOver: boolean;
  topK: number;
  onTopKChange: (topK: number) => void;
};

export function DemoToolbar({
  selectedDemoCaseId,
  onSelectedDemoCaseChange,
  onLoadDemoCase,
  onStartOver,
  canStartOver,
  topK,
  onTopKChange,
}: DemoToolbarProps) {
  const selectedDemoCase = DEMO_CASES.find(
    (demoCase) => demoCase.id === selectedDemoCaseId,
  );

  return (
    <section className="card demo-toolbar" aria-label="Demo operator tools">
      <div>
        <p className="eyebrow">Demo operator tools</p>
        <h2>Run a repeatable walkthrough</h2>
        <p className="demo-toolbar-description">
          {selectedDemoCase?.description}
        </p>
      </div>

      <div className="demo-toolbar-controls">
        <div className="demo-toolbar-field">
          <label htmlFor="demo-case">Demo case</label>
          <select
            id="demo-case"
            value={selectedDemoCaseId}
            onChange={(event) =>
              onSelectedDemoCaseChange(event.target.value as DemoCaseId)
            }
          >
            {DEMO_CASES.map((demoCase) => (
              <option key={demoCase.id} value={demoCase.id}>
                {demoCase.label}
              </option>
            ))}
          </select>
        </div>

        <div className="demo-toolbar-field">
          <label htmlFor="retrieval-top-k">Chunks to retrieve</label>
          <select
            id="retrieval-top-k"
            value={topK}
            onChange={(event) => onTopKChange(Number(event.target.value))}
          >
            {TOP_K_OPTIONS.map((option) => (
              <option key={option} value={option}>
                Top {option}
              </option>
            ))}
          </select>
        </div>

        <button
          className="secondary-button"
          type="button"
          onClick={onLoadDemoCase}
        >
          Load demo case
        </button>

        <button
          className="ghost-button"
          type="button"
          onClick={onStartOver}
          disabled={!canStartOver}
        >
          Start over
        </button>
      </div>
    </section>
  );
}
