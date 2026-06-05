import { useCallback, useEffect, useState, type PropsWithChildren } from 'react'
import { useQueryClient } from '@tanstack/react-query'

import { getMe, login as loginRequest, logout as logoutRequest, refreshToken } from '../../api/authApi'
import { toApiError } from '../../api/errors'
import { clearAuthSession, getStoredRefreshToken, setAuthSession, setAuthTokens, setCurrentUser } from './authSession'
import { AuthContext, type AuthStatus } from './AuthContext'
import type { AuthUser, LoginCredentials } from './authTypes'

export function AuthProvider({ children }: PropsWithChildren) {
  const queryClient = useQueryClient()
  const [status, setStatus] = useState<AuthStatus>('checking')
  const [user, setUser] = useState<AuthUser | null>(null)

  const clearLocalAuth = useCallback(() => {
    clearAuthSession()
    setUser(null)
    setStatus('anonymous')
    queryClient.clear()
  }, [queryClient])

  useEffect(() => {
    let isMounted = true

    async function bootstrapAuth() {
      const refresh = getStoredRefreshToken()
      if (!refresh) {
        if (isMounted) {
          setStatus('anonymous')
        }
        return
      }

      try {
        const refreshed = await refreshToken(refresh)
        setAuthTokens(refreshed.data)

        const me = await getMe()
        setCurrentUser(me.data)

        if (isMounted) {
          setUser(me.data)
          setStatus('authenticated')
        }
      } catch {
        clearAuthSession()
        if (isMounted) {
          setUser(null)
          setStatus('anonymous')
        }
      }
    }

    bootstrapAuth()

    return () => {
      isMounted = false
    }
  }, [])

  const login = useCallback(async (credentials: LoginCredentials) => {
    try {
      const response = await loginRequest(credentials)
      setAuthSession(response.data)
      setUser(response.data.user)
      setStatus('authenticated')
      return response.data.user
    } catch (error) {
      throw toApiError(error)
    }
  }, [])

  const logout = useCallback(async () => {
    const refresh = getStoredRefreshToken()

    try {
      if (refresh) {
        await logoutRequest(refresh)
      }
    } catch {
      // Local logout must always win, even when the refresh token is already invalid.
    } finally {
      clearLocalAuth()
    }
  }, [clearLocalAuth])

  return (
    <AuthContext.Provider
      value={{
        status,
        user,
        isAuthenticated: status === 'authenticated',
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}
