import { Link, NavLink } from 'react-router-dom'

import { getVisibleNavItems } from './navigation'
import { Icon } from './Icon'
import type { AuthUser } from '../features/auth/authTypes'

type AppHeaderProps = {
  user: AuthUser | null
  onMenuClick: () => void
  onSearchClick: () => void
  onRightPanelClick: () => void
}

export function AppHeader({ user, onMenuClick, onSearchClick, onRightPanelClick }: AppHeaderProps) {
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

        <button className="shell-mobile-icon shell-mobile-icon--spacer" type="button" onClick={onRightPanelClick} aria-label="Abrir actividad">
          <Icon name="message" />
        </button>
        <button className="shell-mobile-icon" type="button" onClick={onSearchClick} aria-label="Abrir busqueda">
          <Icon name="search" />
        </button>
        <button className="shell-menu-button" type="button" onClick={onMenuClick} aria-label="Abrir menu">
          <Icon name="menu" />
        </button>
      </div>

      <form className="shell-search" role="search">
        <Icon name="search" />
        <input type="search" placeholder="Buscar en We Lemu..." aria-label="Buscar" />
      </form>

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
        <button className="shell-action-icon" type="button" aria-label="Notificaciones"><span className="dot-count" /><Icon name="bell" /></button>
        <button className="shell-action-icon" type="button" aria-label="Mensajes" onClick={onRightPanelClick}><Icon name="message" /></button>
        <button className="shell-action-icon" type="button" aria-label="Configuracion"><Icon name="settings" /></button>
        <Link className="shell-avatar" to={profileLink?.to ?? '/app'} aria-label={`Perfil ${user?.username ?? 'usuario'}`}>{initials}</Link>
      </div>
    </header>
  )
}
