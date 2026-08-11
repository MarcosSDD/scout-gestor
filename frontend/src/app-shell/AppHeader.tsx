import { Link, NavLink } from 'react-router-dom'

import { getVisibleNavItems } from './navigation'
import { Icon } from './Icon'
import type { AuthUser } from '../features/auth/authTypes'

type AppHeaderProps = {
  user: AuthUser | null
  onMenuClick: () => void
  isMenuOpen: boolean
}

export function AppHeader({ user, onMenuClick, isMenuOpen }: AppHeaderProps) {
  const initials = user?.username.slice(0, 2).toUpperCase() ?? 'WL'
  const quickLinks = getVisibleNavItems(user).filter((item) => item.showInHeader)
  const profileLink = getVisibleNavItems(user).find((item) => item.id === 'perfil')

  return (
    <header className="shell-header">
      <div className="shell-header__top">
        <Link className="shell-brand" to="/app" aria-label="We Lemu inicio">
          <img src="/images/scout.png" alt="Grupo Guia y Scout We Lemu" />
          <span>We Lemu</span>
        </Link>

        <button className="shell-menu-button" type="button" onClick={onMenuClick} aria-label={isMenuOpen ? 'Cerrar menu' : 'Abrir menu'} aria-expanded={isMenuOpen} aria-controls="shell-sidebar">
          <Icon name="menu" />
        </button>
      </div>

      <nav className="shell-header__center" aria-label="Accesos rapidos">
        {quickLinks.map((link) => (
          <NavLink
            key={link.id}
            className={({ isActive }) => `shell-header-icon ${isActive ? 'shell-header-icon--active' : ''}`}
            end={link.to === '/app'}
            to={link.to}
            aria-label={link.label}
          >
            <Icon name={link.icon} />
          </NavLink>
        ))}
      </nav>

      <div className="shell-header__actions" aria-label="Acciones de usuario">
        <Link className="shell-avatar" to={profileLink?.to ?? '/app'} aria-label={`Perfil ${user?.username ?? 'usuario'}`}>{initials}</Link>
      </div>
    </header>
  )
}
