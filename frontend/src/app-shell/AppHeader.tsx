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

  return (
    <header className="shell-header">
      <div className="shell-header__top">
        <a className="shell-brand" href="/app" aria-label="We Lemu inicio">
          <img src="/images/scout.png" alt="Grupo Guia y Scout We Lemu" />
          <span>We Lemu</span>
        </a>

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
        <a className="shell-header-icon shell-header-icon--active" href="/app" aria-label="Inicio"><Icon name="home" /></a>
        <a className="shell-header-icon" href="/app" aria-label="Grupos"><Icon name="users" /></a>
        <a className="shell-header-icon" href="/app" aria-label="Unidades"><Icon name="layers" /></a>
        <a className="shell-header-icon" href="/app" aria-label="Panel"><Icon name="layout" /></a>
      </nav>

      <div className="shell-header__actions" aria-label="Acciones de usuario">
        <button className="shell-action-icon" type="button" aria-label="Notificaciones"><span className="dot-count" /><Icon name="bell" /></button>
        <button className="shell-action-icon" type="button" aria-label="Mensajes" onClick={onRightPanelClick}><Icon name="message" /></button>
        <button className="shell-action-icon" type="button" aria-label="Configuracion"><Icon name="settings" /></button>
        <a className="shell-avatar" href="/app" aria-label={`Perfil ${user?.username ?? 'usuario'}`}>{initials}</a>
      </div>
    </header>
  )
}
