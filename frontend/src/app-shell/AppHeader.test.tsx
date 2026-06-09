import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import type { AuthUser } from '../features/auth/authTypes'
import { AppHeader } from './AppHeader'

function user(overrides: Partial<AuthUser> = {}): AuthUser {
  return {
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
    ...overrides,
  }
}

function renderHeader(authUser: AuthUser) {
  return render(
    <MemoryRouter>
      <AppHeader user={authUser} onMenuClick={vi.fn()} onSearchClick={vi.fn()} onRightPanelClick={vi.fn()} />
    </MemoryRouter>,
  )
}

describe('AppHeader', () => {
  it('filters quick links for unidad users', () => {
    renderHeader(user({ unidad_roles: [{ unidad_id: 4, rol: 'ASISTENTE' }] }))

    expect(screen.getByRole('link', { name: 'Dashboard' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Unidades' })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Grupos' })).not.toBeInTheDocument()
  })

  it('links avatar to profile when a persona exists', () => {
    renderHeader(user({ persona_id: 9 }))

    expect(screen.getByRole('link', { name: /perfil responsable1/i })).toHaveAttribute('href', '/app/perfil')
  })
})
