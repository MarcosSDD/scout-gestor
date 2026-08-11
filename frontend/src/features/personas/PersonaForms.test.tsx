import { screen } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { vi } from 'vitest'
import { AuthContext } from '../auth/AuthContext'
import { renderWithQueryClient } from '../../test/renderWithQueryClient'
import { PersonaFormPage } from './PersonaForms'
import { usePersonaDetailQuery } from './usePersonasQueries'

vi.mock('./usePersonasQueries', () => ({ usePersonaDetailQuery: vi.fn(), useBeneficiarioDetailQuery: vi.fn(), useAdultoDetailQuery: vi.fn() }))
vi.mock('./usePersonasMutations', () => ({ usePersonaMutation: vi.fn(() => ({ mutateAsync: vi.fn(), isPending: false })), useBeneficiarioMutation: vi.fn(), useAsignacionMutation: vi.fn(), useCertificadoMutation: vi.fn(), useRamasQuery: vi.fn(), useUnidadesSeleccionQuery: vi.fn() }))

const auth = { status: 'authenticated' as const, isAuthenticated: true, login: vi.fn(), logout: vi.fn(), user: { id: 1, username: 'apoderado', email: '', first_name: '', last_name: '', is_staff: false, is_superuser: false, persona_id: 8, responsable_grupo_ids: [], unidad_roles: [], is_apoderado: true } }

describe('PersonaFormPage', () => {
  it('usa la persona autenticada y vuelve al perfil en la ruta de edición propia', () => {
    vi.mocked(usePersonaDetailQuery).mockReturnValue({ isLoading: false, isError: false, data: { data: { id: 8, email: 'guardian@example.test' }, meta: { permissions: { can_edit_contact: true } } } } as ReturnType<typeof usePersonaDetailQuery>)
    const router = createMemoryRouter([{ path: '/app/perfil/editar', element: <PersonaFormPage /> }], { initialEntries: ['/app/perfil/editar'] })
    renderWithQueryClient(<AuthContext value={auth}><RouterProvider router={router} /></AuthContext>)
    expect(usePersonaDetailQuery).toHaveBeenCalledWith(8)
    expect(screen.getByRole('link', { name: 'Volver' })).toHaveAttribute('href', '/app/perfil')
    expect(screen.getByLabelText('Correo')).toBeInTheDocument()
  })
})
