type ListSectionProps = {
  label: string;
  emptyMessage: string;
  items: string[];
  tone?: "default" | "warning" | "muted";
};

export function ListSection({
  label,
  emptyMessage,
  items,
  tone = "default",
}: ListSectionProps) {
  return (
    <section
      className={`result-section result-section-${tone}`}
      aria-label={label}
    >
      <div className="result-section-heading">
        <h3>{label}</h3>
        <span>{items.length}</span>
      </div>
      {items.length === 0 ? (
        <p className="empty-state">{emptyMessage}</p>
      ) : (
        <ul className="compact-list">
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      )}
    </section>
  );
}
