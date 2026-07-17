import type { DashboardBirthdayAlert } from '../../api/dashboardApi'

type BirthdayAlertsProps = {
  alerts: DashboardBirthdayAlert[]
}

export function BirthdayAlerts({ alerts }: BirthdayAlertsProps) {
  return (
    <article className="home-card dashboard-alerts-card">
      <div className="dashboard-section-heading">
        <div>
          <p className="shell-panel-caption">Alertas</p>
          <h2>Cumpleanos de la semana</h2>
        </div>
        <span className="dashboard-pill">{alerts.length}</span>
      </div>

      {alerts.length === 0 ? (
        <p className="dashboard-empty-text">No hay cumpleanos en los proximos 7 dias.</p>
      ) : (
        <ul className="dashboard-birthday-list">
          {alerts.map((alert) => (
            <li key={`${alert.tipo}-${alert.persona_id}`}>
              <span className="dashboard-birthday-day">{formatDays(alert.dias_restantes)}</span>
              <div>
                <strong>{alert.nombres} {alert.apellidos}</strong>
                <small>
                  {alert.tipo === 'BENEFICIARIO' ? 'Beneficiario' : 'Adulto'} · cumple {alert.edad_cumple} anos
                  {alert.unidad ? ` · ${alert.unidad.nombre}` : ''}
                </small>
              </div>
            </li>
          ))}
        </ul>
      )}
    </article>
  )
}

function formatDays(days: number) {
  if (days === 0) {
    return 'Hoy'
  }

  if (days === 1) {
    return '1 dia'
  }

  return `${days} dias`
}
