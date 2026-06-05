import { Icon } from './Icon'

type RightPanelProps = {
  isOpen: boolean
}

export function RightPanel({ isOpen }: RightPanelProps) {
  return (
    <aside className={`shell-right-panel ${isOpen ? 'active-sidebar' : ''}`} aria-label="Actividad y alertas">
      <div className="shell-right-card">
        <p className="shell-panel-caption">Alertas</p>
        <ul className="shell-activity-list">
          <li><span className="activity-dot activity-dot--warning" /><div><strong>Cumpleanos proximos</strong><small>Placeholder operativo</small></div></li>
          <li><span className="activity-dot activity-dot--success" /><div><strong>Unidades activas</strong><small>Vista inicial</small></div></li>
          <li><span className="activity-dot activity-dot--primary" /><div><strong>Actividad reciente</strong><small>Se conectara luego</small></div></li>
        </ul>
      </div>
      <div className="shell-right-card">
        <p className="shell-panel-caption">Accesos</p>
        <a className="shell-mini-link" href="/app"><Icon name="users" /> Grupos</a>
        <a className="shell-mini-link" href="/app"><Icon name="layers" /> Unidades</a>
      </div>
    </aside>
  )
}
