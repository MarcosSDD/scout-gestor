import { useId } from "react";
import { Link } from "react-router-dom";

type CircularActionLinkProps = {
  to: string;
  label: string;
  symbol?: string;
};

export function CircularActionLink({
  to,
  label,
  symbol = "+",
}: CircularActionLinkProps) {
  const tooltipId = useId();

  return (
    <Link
      className="circular-action-link"
      to={to}
      aria-label={label}
      aria-describedby={tooltipId}
    >
      <span aria-hidden="true">{symbol}</span>
      <span
        id={tooltipId}
        className="circular-action-link__tooltip"
        role="tooltip"
      >
        {label}
      </span>
    </Link>
  );
}
