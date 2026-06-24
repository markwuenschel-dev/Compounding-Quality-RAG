import type { ReactNode } from "react";

type CollapsibleCardProps = {
  ariaLabel: string;
  eyebrow?: string;
  title: string;
  description?: ReactNode;
  /** Shown on the right of the header (e.g. a status pill). */
  statusPill?: ReactNode;
  /** Extra header controls rendered next to the pill (kept outside the toggle button). */
  actions?: ReactNode;
  /** One-line recap shown when the card is collapsed. */
  summary?: ReactNode;
  /** Extra className(s) for the outer card. */
  className?: string;
  /**
   * Collapse wiring. When `onToggleCollapsed` is omitted the card is a plain,
   * always-expanded card (so standalone usage/tests are unchanged).
   */
  collapsed?: boolean;
  onToggleCollapsed?: () => void;
  children: ReactNode;
};

export function CollapsibleCard({
  ariaLabel,
  eyebrow,
  title,
  description,
  statusPill,
  actions,
  summary,
  className = "",
  collapsed = false,
  onToggleCollapsed,
  children,
}: CollapsibleCardProps) {
  const collapsible = typeof onToggleCollapsed === "function";
  const open = collapsible ? !collapsed : true;

  const headingMain = (
    <div className="collapsible-heading-main">
      {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
      <h2>{title}</h2>
      {open && description ? (
        <p className="collapsible-description">{description}</p>
      ) : null}
      {!open && summary ? (
        <p className="collapsible-summary">{summary}</p>
      ) : null}
    </div>
  );

  const aside =
    statusPill || actions ? (
      <div className="collapsible-heading-aside">
        {statusPill}
        {actions}
      </div>
    ) : null;

  return (
    <section
      className={`card workflow-card ${className}`.trim()}
      aria-label={ariaLabel}
    >
      <div className="section-heading collapsible-heading">
        {collapsible ? (
          <button
            type="button"
            className="collapsible-toggle"
            aria-expanded={open}
            onClick={onToggleCollapsed}
          >
            {headingMain}
            <span
              className={`collapsible-chevron ${open ? "is-open" : ""}`}
              aria-hidden="true"
            >
              ▾
            </span>
          </button>
        ) : (
          headingMain
        )}
        {aside}
      </div>

      {open ? <div className="collapsible-body">{children}</div> : null}
    </section>
  );
}
