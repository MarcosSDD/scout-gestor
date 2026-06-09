import { NavLink } from 'react-router-dom'

import { useAuth } from '../features/auth/useAuth'
import { Icon } from './Icon'
import { getVisibleNavItems, type ShellNavGroup, type ShellNavItem } from './navigation'

type SidebarProps = {
  isOpen: boolean
  onClose: () => void
  onLogout: () => void
}

export function Sidebar({ isOpen, onClose, onLogout }: SidebarProps) {
  const { user } = useAuth()
  const visibleItems = getVisibleNavItems(user)
  const managementLinks = visibleItems.filter((item) => item.group === 'Gestion')
  const operationLinks = visibleItems.filter((item) => item.group === 'Operativo')
  const accountLinks = visibleItems.filter((item) => item.group === 'Cuenta')

  return (
    <>
      <button className={`shell-backdrop ${isOpen ? 'shell-backdrop--visible' : ''}`} type="button" aria-label="Cerrar menu" onClick={onClose} />
      <aside className={`shell-sidebar ${isOpen ? 'nav-active' : ''}`} aria-label="Navegacion principal">
        <div className="shell-sidebar__inner">
          <NavGroup caption="Gestion" links={managementLinks} />
          {operationLinks.length > 0 && <NavGroup caption="Operativo" links={operationLinks} />}
          <div className="shell-nav-card">
            <p className="shell-nav-caption">Cuenta</p>
            {accountLinks.map((link) => <NavItem key={link.id} link={link} />)}
            <button className="shell-nav-link" type="button" onClick={onLogout}><Icon name="logout" /><span>Salir</span></button>
          </div>
        </div>
      </aside>
    </>
  )
}

function NavGroup({ caption, links }: { caption: ShellNavGroup, links: ShellNavItem[] }) {
  return (
    <div className="shell-nav-card">
      <p className="shell-nav-caption">{caption}</p>
      <ul>
        {links.map((link) => (
          <li key={link.label}>
            <NavItem link={link} />
          </li>
        ))}
      </ul>
    </div>
  )
}

function NavItem({ link }: { link: ShellNavItem }) {
  return (
    <NavLink
      className={({ isActive }) => `shell-nav-link ${isActive ? 'shell-nav-link--active' : ''}`}
      end={link.to === '/app'}
      to={link.to}
    >
      <Icon name={link.icon} />
      <span>{link.label}</span>
    </NavLink>
  )
}
