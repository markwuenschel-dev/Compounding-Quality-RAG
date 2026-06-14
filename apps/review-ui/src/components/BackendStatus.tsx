import type { BackendReadinessState } from "../hooks/useBackendReadiness";

type BackendStatusProps = {
  readiness: BackendReadinessState;
};

export function BackendStatus({
  readiness,
}: BackendStatusProps) {
  const className = `backend-status backend-status-${readiness.status}`;
  const title =
    readiness.status === "checking"
      ? "Checking backend"
      : readiness.status === "ready"
        ? "Backend ready"
        : "Backend unavailable";
  const showDetail = readiness.message.trim() !== title;

  return (
    <section
      className={className}
      aria-label="Backend readiness"
      aria-live="polite"
    >
      <div>
        <strong>{title}</strong>
        {showDetail ? <p>{readiness.message}</p> : null}
      </div>

      {readiness.status === "unavailable" ? (
        <button
          className="ghost-button"
          type="button"
          onClick={() => void readiness.refresh()}
          disabled={readiness.isRefreshing}
        >
          {readiness.isRefreshing ? "Checking..." : "Check again"}
        </button>
      ) : null}
    </section>
  );
}
