import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import { AuthContext, type AuthContextValue } from '../features/auth/AuthContext'
import type { AuthUser } from '../features/auth/authTypes'
import { Sidebar } from './Sidebar'

function user(overrides: Partial<AuthUser> = {}): AuthUser {
  return {
    id: 1,
    username: 'usuario',
    email: 'usuario@scouts.cl',
    first_name: 'Ana',
    last_name: 'Rojas',
    is_staff: false,
    is_superuser: false,
    persona_id: null,
    responsable_grupo_ids: [],
    unidad_roles: [],
    is_apoderado: false,
    ...overrides,
  }
}

function renderSidebar(authUser: AuthUser) {
  const value: AuthContextValue = {
    status: 'authenticated',
    user: authUser,
    isAuthenticated: true,
    login: vi.fn(),
    logout: vi.fn(),
  }

  return render(
    <MemoryRouter initialEntries={['/app/grupos']}>
      <AuthContext.Provider value={value}>
        <Sidebar isOpen={false} onClose={vi.fn()} onLogout={vi.fn()} />
      </AuthContext.Provider>
    </MemoryRouter>,
  )
}

describe('Sidebar', () => {
  it('shows full visual navigation for admin users', () => {
    renderSidebar(user({ is_staff: true, persona_id: 1 }))

    expect(screen.getByRole('link', { name: /dashboard/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /grupos/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /personas/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /unidades/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /formacion/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /mi perfil/i })).toBeInTheDocument()
  })

  it('hides management links from apoderado-only users', () => {
    renderSidebar(user({ persona_id: 2, is_apoderado: true }))

    expect(screen.getByRole('link', { name: /dashboard/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /mi perfil/i })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /grupos/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /unidades/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /formacion/i })).not.toBeInTheDocument()
  })
})
