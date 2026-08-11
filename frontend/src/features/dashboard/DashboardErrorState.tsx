import { getApiErrorKind } from '../../api/errors'
import type { ApiError } from '../../api/types'

type DashboardErrorStateProps = {
  error: ApiError | null
  onRetry?: () => void
}

export function DashboardErrorState({ error, onRetry }: DashboardErrorStateProps) {
  const kind = getApiErrorKind(error)

  return (
    <article className="home-card dashboard-state-card" role="alert">
      <p className="shell-panel-caption">Dashboard</p>
      <h1>{kind === 'unauthorized' ? 'Sesión no autorizada' : kind === 'forbidden' ? 'Acceso denegado' : kind === 'not-found' ? 'Grupo no encontrado' : 'No fue posible cargar el dashboard'}</h1>
      <p>{kind === 'unauthorized' ? 'Tu sesión ya no permite acceder al dashboard. Inicia sesión nuevamente.' : kind === 'forbidden' ? 'El backend no permite ver el dashboard de este grupo.' : kind === 'not-found' ? 'El grupo seleccionado no existe o ya no está disponible.' : error?.error.message ?? 'Intenta nuevamente en unos segundos.'}</p>
      {onRetry && kind === 'other' && <button className="primary-button dashboard-retry-button" type="button" onClick={onRetry}>Reintentar</button>}
    </article>
  )
}
