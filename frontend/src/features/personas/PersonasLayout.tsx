import { NavLink, Outlet } from "react-router-dom";

const links = [
  { to: "/app/personas/beneficiarios", label: "Beneficiarios" },
  { to: "/app/personas/apoderados", label: "Apoderados" },
  { to: "/app/personas/adultos", label: "Guías y Dirigentes" },
];

type PersonasLayoutProps = {
  showSubnav?: boolean;
};

export function PersonasLayout({ showSubnav = true }: PersonasLayoutProps) {
  return (
    <>
      {showSubnav ? (
        <nav className="persona-subnav" aria-label="Tipos de personas">
          {links.map((link) => (
            <NavLink key={link.to} to={link.to}>
              {link.label}
            </NavLink>
          ))}
        </nav>
      ) : null}
      <Outlet />
    </>
  );
}
