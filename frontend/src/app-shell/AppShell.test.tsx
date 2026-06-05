import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import { AuthContext } from '../features/auth/AuthContext'
import { AppShell } from './AppShell'

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

describe('AppShell', () => {
  it('renders default.html inspired shell regions and mobile footer', () => {
    render(
      <MemoryRouter>
        <AuthContext.Provider
          value={{
            status: 'authenticated',
            user: authUser,
            isAuthenticated: true,
            login: vi.fn(),
            logout: vi.fn(),
          }}
        >
          <AppShell><div>Shell content</div></AppShell>
        </AuthContext.Provider>
      </MemoryRouter>,
    )

    expect(screen.getByRole('link', { name: 'We Lemu inicio' })).toBeInTheDocument()
    expect(screen.getByLabelText('Acciones de usuario')).toBeInTheDocument()
    expect(screen.getByLabelText('Navegacion principal')).toBeInTheDocument()
    expect(screen.getByLabelText('Actividad y alertas')).toBeInTheDocument()
    expect(screen.getByLabelText('Navegacion movil')).toBeInTheDocument()
    expect(screen.getByText('Shell content')).toBeInTheDocument()
  })
})
