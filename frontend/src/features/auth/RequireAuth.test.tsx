import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import { AuthContext, type AuthContextValue } from './AuthContext'
import { RequireAuth } from './RequireAuth'

function renderWithAuth(value: Partial<AuthContextValue>) {
  return render(
    <MemoryRouter>
      <AuthContext.Provider
        value={{
          status: 'anonymous',
          user: null,
          isAuthenticated: false,
          login: vi.fn(),
          logout: vi.fn(),
          ...value,
        }}
      >
        <RequireAuth><div>Protected content</div></RequireAuth>
      </AuthContext.Provider>
    </MemoryRouter>,
  )
}

function renderRouteWithAuth(value: Partial<AuthContextValue>) {
  return render(
    <MemoryRouter initialEntries={['/app']}>
      <AuthContext.Provider
        value={{
          status: 'anonymous',
          user: null,
          isAuthenticated: false,
          login: vi.fn(),
          logout: vi.fn(),
          ...value,
        }}
      >
        <Routes>
          <Route path="/app" element={<RequireAuth><div>Protected content</div></RequireAuth>} />
          <Route path="/login" element={<div>Login page</div>} />
        </Routes>
      </AuthContext.Provider>
    </MemoryRouter>,
  )
}

describe('RequireAuth', () => {
  it('shows bootstrap loading state', () => {
    renderWithAuth({ status: 'checking' })

    expect(screen.getByRole('status')).toHaveTextContent('Restaurando sesion...')
  })

  it('renders children when authenticated', () => {
    renderWithAuth({ status: 'authenticated', isAuthenticated: true })

    expect(screen.getByText('Protected content')).toBeInTheDocument()
  })

  it('redirects anonymous users to login', () => {
    renderRouteWithAuth({ status: 'anonymous', isAuthenticated: false })

    expect(screen.getByText('Login page')).toBeInTheDocument()
  })
})
