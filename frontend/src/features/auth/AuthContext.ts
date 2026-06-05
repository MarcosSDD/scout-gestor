import { createContext } from 'react'

import type { AuthUser, LoginCredentials } from './authTypes'

export type AuthStatus = 'checking' | 'authenticated' | 'anonymous'

export type AuthContextValue = {
  status: AuthStatus
  user: AuthUser | null
  isAuthenticated: boolean
  login: (credentials: LoginCredentials) => Promise<AuthUser>
  logout: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)
