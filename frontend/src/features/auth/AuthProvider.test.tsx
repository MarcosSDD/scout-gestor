import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { getMe, logout as logoutRequest, refreshToken } from '../../api/authApi'
import { clearAuthSession, getAccessToken, getStoredRefreshToken, setAuthTokens } from './authSession'
import { AuthProvider } from './AuthProvider'
import { useAuth } from './useAuth'
import { renderWithQueryClient } from '../../test/renderWithQueryClient'

vi.mock('../../api/authApi', () => ({
  getMe: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
  refreshToken: vi.fn(),
}))

const authUser = {
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
}

function AuthProbe() {
  const { status, user, logout } = useAuth()

  return (
    <div>
      <p>Status: {status}</p>
      <p>User: {user?.username ?? 'none'}</p>
      <button type="button" onClick={() => void logout()}>Logout</button>
    </div>
  )
}

describe('AuthProvider', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    clearAuthSession()
  })

  it('starts anonymous when there is no refresh token', async () => {
    renderWithQueryClient(
      <AuthProvider>
        <AuthProbe />
      </AuthProvider>,
    )

    await waitFor(() => expect(screen.getByText('Status: anonymous')).toBeInTheDocument())
    expect(refreshToken).not.toHaveBeenCalled()
  })

  it('restores session with refresh token and /me', async () => {
    setAuthTokens({ access: 'old-access', refresh: 'stored-refresh' })
    vi.mocked(refreshToken).mockResolvedValueOnce({
      success: true,
      message: 'Token refreshed',
      data: { access: 'new-access', refresh: 'new-refresh' },
    })
    vi.mocked(getMe).mockResolvedValueOnce({ success: true, message: 'Authenticated user', data: authUser })

    renderWithQueryClient(
      <AuthProvider>
        <AuthProbe />
      </AuthProvider>,
    )

    await waitFor(() => expect(screen.getByText('Status: authenticated')).toBeInTheDocument())
    expect(screen.getByText('User: responsable1')).toBeInTheDocument()
    expect(getAccessToken()).toBe('new-access')
    expect(getStoredRefreshToken()).toBe('new-refresh')
  })

  it('clears local state on logout even if backend fails', async () => {
    const user = userEvent.setup()
    setAuthTokens({ access: 'access-token', refresh: 'stored-refresh' })
    vi.mocked(refreshToken).mockResolvedValueOnce({
      success: true,
      message: 'Token refreshed',
      data: { access: 'new-access', refresh: 'new-refresh' },
    })
    vi.mocked(getMe).mockResolvedValueOnce({ success: true, message: 'Authenticated user', data: authUser })
    vi.mocked(logoutRequest).mockRejectedValueOnce(new Error('logout failed'))

    renderWithQueryClient(
      <AuthProvider>
        <AuthProbe />
      </AuthProvider>,
    )

    await waitFor(() => expect(screen.getByText('Status: authenticated')).toBeInTheDocument())
    await user.click(screen.getByRole('button', { name: 'Logout' }))

    await waitFor(() => expect(screen.getByText('Status: anonymous')).toBeInTheDocument())
    expect(getAccessToken()).toBeNull()
    expect(getStoredRefreshToken()).toBeNull()
  })
})
