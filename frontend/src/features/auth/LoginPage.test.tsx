import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'

import { LoginPage } from './LoginPage'
import { useAuth } from './useAuth'

const navigate = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useNavigate: () => navigate,
  }
})

vi.mock('react-toastify', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

vi.mock('./useAuth', () => ({
  useAuth: vi.fn(),
}))

describe('LoginPage', () => {
  beforeEach(() => {
    navigate.mockClear()
  })

  it('redirects to app after successful login', async () => {
    const user = userEvent.setup()
    const login = vi.fn().mockResolvedValue({ username: 'responsable1' })

    vi.mocked(useAuth).mockReturnValue({
      status: 'anonymous',
      user: null,
      isAuthenticated: false,
      login,
      logout: vi.fn(),
    } as unknown as ReturnType<typeof useAuth>)

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    )

    await user.type(screen.getByLabelText('Correo electrónico'), 'responsable1@scouts.cl')
    await user.type(screen.getByLabelText('Contraseña'), 'testpass123')
    await user.click(screen.getByRole('button', { name: 'Ingresar' }))

    expect(login).toHaveBeenCalledWith({ email: 'responsable1@scouts.cl', password: 'testpass123' })
    expect(navigate).toHaveBeenCalledWith('/app')
  })
})
