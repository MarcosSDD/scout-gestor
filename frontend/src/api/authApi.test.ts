import { httpClient } from './httpClient'
import { getMe, login, logout, refreshToken } from './authApi'

vi.mock('./httpClient', () => ({
  httpClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

describe('login', () => {
  it('calls auth token endpoint and returns typed envelope', async () => {
    const envelope = {
      success: true,
      message: 'Token issued',
      data: {
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
      },
    }

    vi.mocked(httpClient.post).mockResolvedValueOnce({ data: envelope })

    const credentials = { username: 'responsable1', password: 'testpass123' }
    const result = await login(credentials)

    expect(httpClient.post).toHaveBeenCalledWith('/auth/token/', credentials)
    expect(result).toEqual(envelope)
  })

  it('refreshes access token with refresh token', async () => {
    const envelope = {
      success: true,
      message: 'Token refreshed',
      data: { access: 'new-access', refresh: 'new-refresh' },
    }

    vi.mocked(httpClient.post).mockResolvedValueOnce({ data: envelope })

    const result = await refreshToken('refresh-token')

    expect(httpClient.post).toHaveBeenCalledWith('/auth/token/refresh/', { refresh: 'refresh-token' })
    expect(result).toEqual(envelope)
  })

  it('loads authenticated user from /me', async () => {
    const envelope = {
      success: true,
      message: 'Authenticated user',
      data: {
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

    vi.mocked(httpClient.get).mockResolvedValueOnce({ data: envelope })

    const result = await getMe()

    expect(httpClient.get).toHaveBeenCalledWith('/auth/me/')
    expect(result).toEqual(envelope)
  })

  it('posts refresh token to logout endpoint', async () => {
    const envelope = { success: true, message: 'Logout successful', data: null }

    vi.mocked(httpClient.post).mockResolvedValueOnce({ data: envelope })

    const result = await logout('refresh-token')

    expect(httpClient.post).toHaveBeenCalledWith('/auth/logout/', { refresh: 'refresh-token' })
    expect(result).toEqual(envelope)
  })
})
