import { Link } from "react-router-dom";

import { useAuth } from "../features/auth/useAuth";
import { Icon } from "./Icon";
import { getVisibleNavItems } from "./navigation";

type RightPanelProps = {
  isOpen: boolean;
};

export function RightPanel({ isOpen }: RightPanelProps) {
  const { user } = useAuth();
  const links = getVisibleNavItems(user).filter(
    (item) => item.showInRightPanel,
  );

  return (
    <aside
      className={`shell-right-panel ${isOpen ? "active-sidebar" : ""}`}
      aria-label="Actividad y alertas"
    >
      <div className="shell-right-card">
        <p className="shell-panel-caption">Alertas</p>
        <ul className="shell-activity-list">
          <li>
            <span className="activity-dot activity-dot--warning" />
            <div>
              <strong>Cumpleanos proximos</strong>
              <small>Placeholder operativo</small>
            </div>
          </li>
          <li>
            <span className="activity-dot activity-dot--success" />
            <div>
              <strong>Unidades activas</strong>
              <small>Vista inicial</small>
            </div>
          </li>
          <li>
            <span className="activity-dot activity-dot--primary" />
            <div>
              <strong>Actividad reciente</strong>
              <small>Se conectara luego</small>
            </div>
          </li>
        </ul>
      </div>
      {links.length > 0 && (
        <div className="shell-right-card">
          <p className="shell-panel-caption">Accesos</p>
          {links.map((link) => (
            <Link key={link.id} className="shell-mini-link" to={link.to}>
              <Icon name={link.icon} /> {link.label}
            </Link>
          ))}
        </div>
      )}
    </aside>
  );
}
