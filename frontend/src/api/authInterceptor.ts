import axios, { type InternalAxiosRequestConfig } from 'axios'

import { clearAuthSession, getStoredRefreshToken, setAuthTokens } from '../features/auth/authSession'
import type { RefreshTokenData, RefreshTokenResponse } from '../features/auth/authTypes'
import { httpClient } from './httpClient'

type RetriableRequestConfig = InternalAxiosRequestConfig & {
  _retry?: boolean
}

const AUTH_ENDPOINTS_WITHOUT_REFRESH = [
  '/auth/token/',
  '/auth/token/refresh/',
  '/auth/logout/',
]

let refreshPromise: Promise<RefreshTokenData> | null = null

function shouldSkipRefresh(url?: string) {
  if (!url) {
    return true
  }

  return AUTH_ENDPOINTS_WITHOUT_REFRESH.some((endpoint) => url.includes(endpoint))
}

async function requestTokenRefresh(refresh: string) {
  const { data } = await httpClient.post<RefreshTokenResponse>('/auth/token/refresh/', { refresh })
  return data.data
}

httpClient.interceptors.response.use(
  (response) => response,
  async (error: unknown) => {
    if (!axios.isAxiosError(error)) {
      return Promise.reject(error)
    }

    const status = error.response?.status
    const originalRequest = error.config as RetriableRequestConfig | undefined

    if (status !== 401 || !originalRequest || originalRequest._retry || shouldSkipRefresh(originalRequest.url)) {
      return Promise.reject(error)
    }

    const refresh = getStoredRefreshToken()
    if (!refresh) {
      clearAuthSession()
      return Promise.reject(error)
    }

    originalRequest._retry = true

    try {
      refreshPromise ??= requestTokenRefresh(refresh).finally(() => {
        refreshPromise = null
      })

      const tokens = await refreshPromise
      setAuthTokens(tokens)

      originalRequest.headers.Authorization = `Bearer ${tokens.access}`
      return httpClient(originalRequest)
    } catch (refreshError) {
      clearAuthSession()
      return Promise.reject(refreshError)
    }
  },
)
