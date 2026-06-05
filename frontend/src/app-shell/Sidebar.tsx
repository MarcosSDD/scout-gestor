import { Icon } from './Icon'

type SidebarProps = {
  isOpen: boolean
  onClose: () => void
  onLogout: () => void
}

const managementLinks = [
  { label: 'Dashboard', icon: 'home' as const },
  { label: 'Grupos', icon: 'users' as const },
  { label: 'Personas', icon: 'user' as const },
  { label: 'Unidades', icon: 'layers' as const },
]

const operationLinks = [
  { label: 'Alertas', icon: 'bell' as const },
  { label: 'Actividad', icon: 'message' as const },
  { label: 'Formacion', icon: 'shield' as const },
]

export function Sidebar({ isOpen, onClose, onLogout }: SidebarProps) {
  return (
    <>
      <button className={`shell-backdrop ${isOpen ? 'shell-backdrop--visible' : ''}`} type="button" aria-label="Cerrar menu" onClick={onClose} />
      <aside className={`shell-sidebar ${isOpen ? 'nav-active' : ''}`} aria-label="Navegacion principal">
        <div className="shell-sidebar__inner">
          <NavGroup caption="Gestion" links={managementLinks} activeLabel="Dashboard" />
          <NavGroup caption="Operativo" links={operationLinks} />
          <div className="shell-nav-card">
            <p className="shell-nav-caption">Cuenta</p>
            <button className="shell-nav-link" type="button"><Icon name="settings" /><span>Configuracion</span></button>
            <button className="shell-nav-link" type="button" onClick={onLogout}><Icon name="logout" /><span>Salir</span></button>
          </div>
        </div>
      </aside>
    </>
  )
}

function NavGroup({ caption, links, activeLabel }: { caption: string, links: Array<{ label: string, icon: 'home' | 'users' | 'user' | 'layers' | 'bell' | 'message' | 'shield' }>, activeLabel?: string }) {
  return (
    <div className="shell-nav-card">
      <p className="shell-nav-caption">{caption}</p>
      <ul>
        {links.map((link) => (
          <li key={link.label}>
            <a className={`shell-nav-link ${link.label === activeLabel ? 'shell-nav-link--active' : ''}`} href="/app">
              <Icon name={link.icon} />
              <span>{link.label}</span>
            </a>
          </li>
        ))}
      </ul>
    </div>
  )
}
