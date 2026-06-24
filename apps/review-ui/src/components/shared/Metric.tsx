type MetricProps = {
  label: string;
  value: string | null;
};

export function Metric({ label, value }: MetricProps) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value ?? "Not provided"}</strong>
    </div>
  );
}
