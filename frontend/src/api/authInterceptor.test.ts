import { AxiosError, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'

import './authInterceptor'
import { clearAuthSession, getAccessToken, getStoredRefreshToken, setAuthTokens } from '../features/auth/authSession'
import { httpClient } from './httpClient'
import { subscribeToSessionExpired } from '../features/auth/sessionEvents'

function axios401(config: InternalAxiosRequestConfig) {
  const response: AxiosResponse = {
    status: 401,
    statusText: 'Unauthorized',
    headers: {},
    config,
    data: { success: false, error: { code: 'token_not_valid', message: 'Token expired', details: null } },
  }

  return new AxiosError('Request failed with status code 401', 'ERR_BAD_REQUEST', config, null, response)
}

describe('authInterceptor', () => {
  const originalAdapter = httpClient.defaults.adapter

  beforeEach(() => {
    clearAuthSession()
    vi.clearAllMocks()
  })

  afterEach(() => {
    clearAuthSession()
    httpClient.defaults.adapter = originalAdapter
  })

  it('refreshes an expired access token and retries the original request once', async () => {
    setAuthTokens({ access: 'old-access', refresh: 'stored-refresh' })
    let protectedCalls = 0
    let retryAuthorization: unknown

    httpClient.defaults.adapter = vi.fn(async (config) => {
      if (config.url === '/protected-resource/') {
        protectedCalls += 1

        if (protectedCalls === 1) {
          throw axios401(config)
        }

        retryAuthorization = config.headers.Authorization
        return {
          status: 200,
          statusText: 'OK',
          headers: {},
          config,
          data: { success: true, message: 'OK', data: { name: 'protected' } },
        }
      }

      if (config.url === '/auth/token/refresh/') {
        return {
          status: 200,
          statusText: 'OK',
          headers: {},
          config,
          data: { success: true, message: 'Token refreshed', data: { access: 'new-access', refresh: 'new-refresh' } },
        }
      }

      throw new Error(`Unexpected request: ${config.url}`)
    })

    const { data } = await httpClient.get('/protected-resource/')

    expect(data.data.name).toBe('protected')
    expect(protectedCalls).toBe(2)
    expect(retryAuthorization).toBe('Bearer new-access')
    expect(getAccessToken()).toBe('new-access')
    expect(getStoredRefreshToken()).toBe('new-refresh')
  })

  it('shares one refresh request for concurrent 401 responses', async () => {
    setAuthTokens({ access: 'old-access', refresh: 'stored-refresh' })
    let refreshCalls = 0
    const retriedUrls: string[] = []
    let resolveRefresh: (() => void) | undefined
    const refreshGate = new Promise<void>((resolve) => {
      resolveRefresh = resolve
    })

    httpClient.defaults.adapter = vi.fn(async (config) => {
      if (config.url === '/auth/token/refresh/') {
        refreshCalls += 1
        await refreshGate
        return {
          status: 200,
          statusText: 'OK',
          headers: {},
          config,
          data: { success: true, message: 'Token refreshed', data: { access: 'shared-access', refresh: 'shared-refresh' } },
        }
      }

      if (config.url === '/resource-a/' || config.url === '/resource-b/') {
        if (!('_retry' in config)) {
          throw axios401(config)
        }

        retriedUrls.push(config.url)
        return {
          status: 200,
          statusText: 'OK',
          headers: {},
          config,
          data: { success: true, message: 'OK', data: { url: config.url } },
        }
      }

      throw new Error(`Unexpected request: ${config.url}`)
    })

    const requests = Promise.all([
      httpClient.get('/resource-a/'),
      httpClient.get('/resource-b/'),
    ])

    await new Promise((resolve) => setTimeout(resolve, 0))
    expect(refreshCalls).toBe(1)

    resolveRefresh?.()
    await requests

    expect(refreshCalls).toBe(1)
    expect(retriedUrls).toEqual(['/resource-a/', '/resource-b/'])
    expect(getStoredRefreshToken()).toBe('shared-refresh')
  })

  it('clears the local session when refresh fails', async () => {
    setAuthTokens({ access: 'old-access', refresh: 'stored-refresh' })

    httpClient.defaults.adapter = vi.fn(async (config) => {
      throw axios401(config)
    })

    await expect(httpClient.get('/protected-resource/')).rejects.toBeInstanceOf(AxiosError)

    expect(getAccessToken()).toBeNull()
    expect(getStoredRefreshToken()).toBeNull()
    expect(httpClient.defaults.headers.common.Authorization).toBeUndefined()
  })

  it('notifies the session channel once when concurrent refresh fails', async () => {
    setAuthTokens({ access: 'old-access', refresh: 'stored-refresh' })
    const expired = vi.fn()
    const unsubscribe = subscribeToSessionExpired(expired)
    httpClient.defaults.adapter = vi.fn(async (config) => {
      if (config.url === '/auth/token/refresh/') throw axios401(config)
      throw axios401(config)
    })

    await Promise.allSettled([httpClient.get('/resource-a/'), httpClient.get('/resource-b/')])

    expect(expired).toHaveBeenCalledTimes(1)
    unsubscribe()
  })

  it('does not refresh login failures', async () => {
    setAuthTokens({ access: 'old-access', refresh: 'stored-refresh' })
    let refreshCalls = 0

    httpClient.defaults.adapter = vi.fn(async (config) => {
      if (config.url === '/auth/token/refresh/') {
        refreshCalls += 1
      }
      throw axios401(config)
    })

    await expect(httpClient.post('/auth/token/', { username: 'bad', password: 'bad' })).rejects.toBeInstanceOf(AxiosError)

    expect(refreshCalls).toBe(0)
    expect(getStoredRefreshToken()).toBe('stored-refresh')
  })

  it('does not retry a request that already used refresh', async () => {
    setAuthTokens({ access: 'old-access', refresh: 'stored-refresh' })
    let refreshCalls = 0

    httpClient.defaults.adapter = vi.fn(async (config) => {
      if (config.url === '/auth/token/refresh/') {
        refreshCalls += 1
        return {
          status: 200,
          statusText: 'OK',
          headers: {},
          config,
          data: { success: true, message: 'Token refreshed', data: { access: 'new-access', refresh: 'new-refresh' } },
        }
      }

      throw axios401(config)
    })

    await expect(httpClient.get('/protected-resource/')).rejects.toBeInstanceOf(AxiosError)

    expect(refreshCalls).toBe(1)
  })
})
