import type { ApiError } from '../../api/types'

type GrupoStateCardProps = {
  title: string
  message: string
  error?: ApiError | null
  onRetry?: () => void
}

export function GrupoStateCard({ title, message, error, onRetry }: GrupoStateCardProps) {
  const isNotFound = error?.error.code === 'not_found'
  const isDenied = error?.error.code === 'permission_denied' || error?.error.code === 'not_authenticated'

  return (
    <article className="home-card grupos-state-card" role={error ? 'alert' : 'status'}>
      <p className="shell-panel-caption">Grupos</p>
      <h1>{isNotFound ? 'Grupo no encontrado' : isDenied ? 'Acceso denegado' : title}</h1>
      <p>{isNotFound ? 'El grupo no existe o ya no esta disponible para tu perfil.' : isDenied ? 'El backend no permite ver este grupo.' : message}</p>
      {onRetry && !isNotFound && !isDenied && (
        <button className="primary-button dashboard-retry-button" type="button" onClick={onRetry}>Reintentar</button>
      )}
    </article>
  )
}
