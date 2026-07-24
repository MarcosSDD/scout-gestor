import { NavLink, Outlet } from 'react-router-dom'

const links = [
  { to: '/app/personas', label: 'Personas', end: true },
  { to: '/app/personas/adultos', label: 'Adultos' },
  { to: '/app/personas/beneficiarios', label: 'Beneficiarios' },
  { to: '/app/personas/apoderados', label: 'Apoderados' },
]

export function PersonasLayout() {
  return <><nav className="persona-subnav" aria-label="Tipos de personas">{links.map((link) => <NavLink key={link.to} to={link.to} end={link.end}>{link.label}</NavLink>)}</nav><Outlet /></>
}
