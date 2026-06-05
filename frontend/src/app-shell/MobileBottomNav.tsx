import { Icon } from './Icon'

export function MobileBottomNav() {
  return (
    <nav className="shell-mobile-footer" aria-label="Navegacion movil">
      <a className="nav-center" href="/app" aria-label="Inicio"><Icon name="home" /></a>
      <a href="/app" aria-label="Grupos"><Icon name="users" /></a>
      <a href="/app" aria-label="Personas"><Icon name="user" /></a>
      <a href="/app" aria-label="Unidades"><Icon name="layers" /></a>
      <a href="/app" aria-label="Perfil"><Icon name="settings" /></a>
    </nav>
  )
}
