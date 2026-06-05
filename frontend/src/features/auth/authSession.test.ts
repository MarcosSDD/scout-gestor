import { httpClient } from '../../api/httpClient'
import { clearAuthSession, getAccessToken, getCurrentUser, getStoredRefreshToken, setAuthSession, setAuthTokens, setCurrentUser } from './authSession'
import type { LoginData } from './authTypes'

const loginData: LoginData = {
  access: 'access-token',
  refresh: 'refresh-token',
  user: {
    id: 1,
    username: 'responsable1',
    email: 'resp1@scouts.cl',
    first_name: 'Ana',
    last_name: 'Rojas',
    is_staff: false,
    is_superuser: false,
    persona_id: null,
    responsable_grupo_ids: [],
    unidad_roles: [],
    is_apoderado: false,
  },
}

describe('authSession', () => {
  beforeEach(() => {
    clearAuthSession()
  })

  it('stores access in memory and refresh in sessionStorage', () => {
    setAuthSession(loginData)

    expect(getAccessToken()).toBe('access-token')
    expect(getStoredRefreshToken()).toBe('refresh-token')
    expect(getCurrentUser()?.username).toBe('responsable1')
    expect(httpClient.defaults.headers.common.Authorization).toBe('Bearer access-token')
  })

  it('clears local session data', () => {
    setAuthSession(loginData)
    clearAuthSession()

    expect(getAccessToken()).toBeNull()
    expect(getStoredRefreshToken()).toBeNull()
    expect(getCurrentUser()).toBeNull()
    expect(httpClient.defaults.headers.common.Authorization).toBeUndefined()
  })

  it('replaces rotated tokens without setting a user', () => {
    setAuthTokens({ access: 'new-access-token', refresh: 'new-refresh-token' })

    expect(getAccessToken()).toBe('new-access-token')
    expect(getStoredRefreshToken()).toBe('new-refresh-token')
    expect(getCurrentUser()).toBeNull()
    expect(httpClient.defaults.headers.common.Authorization).toBe('Bearer new-access-token')
  })

  it('sets current user independently from tokens', () => {
    setCurrentUser(loginData.user)

    expect(getCurrentUser()?.username).toBe('responsable1')
    expect(getAccessToken()).toBeNull()
  })
})
