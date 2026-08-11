import { getApiErrorKind } from '../../api/errors'
import type { ApiError } from '../../api/types'

type GrupoStateCardProps = {
  title: string
  message: string
  error?: ApiError | null
  onRetry?: () => void
}

export function GrupoStateCard({ title, message, error, onRetry }: GrupoStateCardProps) {
  const errorKind = getApiErrorKind(error)
  const isNotFound = errorKind === 'not-found'
  const isDenied = errorKind === 'forbidden'
  const isUnauthorized = errorKind === 'unauthorized'

  return (
    <article className="home-card grupos-state-card" role={error ? 'alert' : 'status'}>
      <p className="shell-panel-caption">Grupos</p>
      <h1>{isUnauthorized ? 'Sesión no autorizada' : isNotFound ? 'Grupo no encontrado' : isDenied ? 'Acceso denegado' : title}</h1>
      <p>{isUnauthorized ? 'Tu sesión ya no permite acceder a esta información. Inicia sesión nuevamente.' : isNotFound ? 'El grupo no existe o ya no esta disponible para tu perfil.' : isDenied ? 'El backend no permite ver este grupo.' : message}</p>
      {onRetry && errorKind === 'other' && (
        <button className="primary-button dashboard-retry-button" type="button" onClick={onRetry}>Reintentar</button>
      )}
    </article>
  )
}
