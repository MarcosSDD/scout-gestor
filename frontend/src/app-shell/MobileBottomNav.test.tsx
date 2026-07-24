import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import { AuthContext, type AuthContextValue } from '../features/auth/AuthContext'
import type { AuthUser } from '../features/auth/authTypes'
import { MobileBottomNav } from './MobileBottomNav'

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

function renderMobileNav(authUser: AuthUser) {
  const value: AuthContextValue = {
    status: 'authenticated',
    user: authUser,
    isAuthenticated: true,
    login: vi.fn(),
    logout: vi.fn(),
  }

  return render(
    <MemoryRouter>
      <AuthContext.Provider value={value}>
        <MobileBottomNav />
      </AuthContext.Provider>
    </MemoryRouter>,
  )
}

describe('MobileBottomNav', () => {
  it('shows mobile management links for responsables', () => {
    renderMobileNav(user({ responsable_grupo_ids: [1], persona_id: 1 }))

    expect(screen.getByRole('link', { name: 'Dashboard' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Grupos' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Personas' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Unidades' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Mi perfil' })).toBeInTheDocument()
  })

  it('does not show management links for users without scope', () => {
    renderMobileNav(user())

    expect(screen.getByRole('link', { name: 'Dashboard' })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Grupos' })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Personas' })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Unidades' })).not.toBeInTheDocument()
  })

  it('shows groups for adults with unit scope', () => {
    renderMobileNav(user({ unidad_roles: [{ unidad_id: 3, rol: 'COLABORADOR' }] }))

    expect(screen.getByRole('link', { name: 'Grupos' })).toBeInTheDocument()
  })
})
