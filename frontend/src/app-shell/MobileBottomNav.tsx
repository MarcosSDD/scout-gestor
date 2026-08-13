import { NavLink } from "react-router-dom";

import { useAuth } from "../features/auth/useAuth";
import { Icon } from "./Icon";
import { getVisibleNavItems } from "./navigation";

export function MobileBottomNav() {
  const { user } = useAuth();
  const links = getVisibleNavItems(user).filter((item) => item.showInMobile);

  return (
    <nav className="shell-mobile-footer" aria-label="Navegacion movil">
      {links.map((link) => (
        <NavLink
          key={link.id}
          className={link.id === "dashboard" ? "nav-center" : undefined}
          end={link.to === "/app"}
          to={link.to}
          aria-label={link.label}
        >
          <Icon name={link.icon} />
        </NavLink>
      ))}
    </nav>
  );
}
