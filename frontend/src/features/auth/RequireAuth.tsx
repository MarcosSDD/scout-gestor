import type { PropsWithChildren } from 'react'
import { Navigate } from 'react-router-dom'

import { useAuth } from './useAuth'

export function RequireAuth({ children }: PropsWithChildren) {
  const { status, isAuthenticated } = useAuth()

  if (status === 'checking') {
    return (
      <main className="auth-checking-page">
        <p role="status">Restaurando sesion...</p>
      </main>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return children
}

export const ProtectedRoute = RequireAuth
