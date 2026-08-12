import { NavLink, Outlet } from 'react-router-dom'

const links = [
  { to: '/app/personas/beneficiarios', label: 'Beneficiarios' },
  { to: '/app/personas/apoderados', label: 'Apoderados' },
  { to: '/app/personas/adultos', label: 'Guías y Dirigentes' },
]

export function PersonasLayout() {
  return <><nav className="persona-subnav" aria-label="Tipos de personas">{links.map((link) => <NavLink key={link.to} to={link.to}>{link.label}</NavLink>)}</nav><Outlet /></>
}
