import type { ApiError } from '../../api/types'

type DashboardErrorStateProps = {
  error: ApiError | null
  onRetry?: () => void
}

export function DashboardErrorState({ error, onRetry }: DashboardErrorStateProps) {
  const status = getErrorStatus(error)
  const message = getErrorMessage(status, error)

  return (
    <article className="home-card dashboard-state-card" role="alert">
      <p className="shell-panel-caption">Dashboard</p>
      <h1>{status === 403 ? 'Acceso denegado' : status === 404 ? 'Grupo no encontrado' : 'No fue posible cargar el dashboard'}</h1>
      <p>{message}</p>
      {onRetry && <button className="primary-button dashboard-retry-button" type="button" onClick={onRetry}>Reintentar</button>}
    </article>
  )
}

function getErrorStatus(error: ApiError | null) {
  if (error?.error.code === 'permission_denied' || error?.error.code === 'not_authenticated') {
    return 403
  }

  if (error?.error.code === 'not_found') {
    return 404
  }

  const details = error?.error.details

  if (details && typeof details === 'object' && 'status' in details) {
    const status = (details as { status?: unknown }).status
    return typeof status === 'number' ? status : null
  }

  return null
}

function getErrorMessage(status: number | null, error: ApiError | null) {
  if (status === 403) {
    return 'El backend no permite ver el dashboard de este grupo.'
  }

  if (status === 404) {
    return 'El grupo seleccionado no existe o ya no esta disponible.'
  }

  return error?.error.message ?? 'Intenta nuevamente en unos segundos.'
}
