type KpiCardProps = {
  label: string;
  value: number | string;
  detail: string;
  tone?: "primary" | "success" | "warning";
  progress?: number;
};

export function KpiCard({
  label,
  value,
  detail,
  tone = "primary",
  progress,
}: KpiCardProps) {
  const normalizedProgress =
    typeof progress === "number" ? Math.max(0, Math.min(100, progress)) : null;

  return (
    <article className={`home-card kpi-card kpi-card--${tone}`}>
      <span className="kpi-card__label">{label}</span>
      <strong className="kpi-card__value">{value}</strong>
      <p>{detail}</p>
      {normalizedProgress !== null && (
        <div
          className="kpi-card__progress"
          aria-label={`${label} ${normalizedProgress}%`}
        >
          <span style={{ width: `${normalizedProgress}%` }} />
        </div>
      )}
    </article>
  );
}
