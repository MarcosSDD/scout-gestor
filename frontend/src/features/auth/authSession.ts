import { httpClient } from '../../api/httpClient'
import { resetSessionExpiredNotification } from './sessionEvents'
import type { AuthUser, LoginData, RefreshTokenData } from './authTypes'

const REFRESH_TOKEN_KEY = 'scout-gestor.refreshToken'

let accessToken: string | null = null
let currentUser: AuthUser | null = null

export function getAccessToken() {
  return accessToken
}

export function getCurrentUser() {
  return currentUser
}

export function getStoredRefreshToken() {
  return sessionStorage.getItem(REFRESH_TOKEN_KEY)
}

export function setAuthTokens(data: RefreshTokenData) {
  resetSessionExpiredNotification()
  accessToken = data.access
  sessionStorage.setItem(REFRESH_TOKEN_KEY, data.refresh)
  httpClient.defaults.headers.common.Authorization = `Bearer ${data.access}`
}

export function setCurrentUser(user: AuthUser | null) {
  currentUser = user
}

export function setAuthSession(data: LoginData) {
  setAuthTokens({ access: data.access, refresh: data.refresh })
  setCurrentUser(data.user)
}

export function clearAuthSession() {
  accessToken = null
  currentUser = null
  sessionStorage.removeItem(REFRESH_TOKEN_KEY)
  delete httpClient.defaults.headers.common.Authorization
}
