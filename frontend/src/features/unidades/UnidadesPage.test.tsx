import { fireEvent, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import { getUnidades } from '../../api/unidadesApi'
import { renderWithQueryClient } from '../../test/renderWithQueryClient'
import { UnidadesPage } from './UnidadesPage'
import { AuthContext } from '../auth/AuthContext'

vi.mock('../../api/unidadesApi', () => ({ getUnidades: vi.fn() }))

describe('UnidadesPage', () => {
  it('renders accessible unit data', async () => {
    vi.mocked(getUnidades).mockResolvedValueOnce({ success: true, message: 'OK', data: [{ id: 1, grupo: 2, grupo_nombre: 'Grupo We Lemu', rama: 3, rama_nombre: 'Tropa', nombre: 'Tropa A', tipo_composicion: 'MIXTA', estado: 'ACTIVA', cupo_maximo: 32 }] })
    renderWithQueryClient(<AuthContext value={{ status: 'authenticated', isAuthenticated: true, login: vi.fn(), logout: vi.fn(), user: { id: 1, username: 'staff', email: '', first_name: '', last_name: '', is_staff: true, is_superuser: false, persona_id: 1, responsable_grupo_ids: [], unidad_roles: [], is_apoderado: false } }}><MemoryRouter><UnidadesPage /></MemoryRouter></AuthContext>)
    expect(await screen.findByText('Tropa A')).toBeInTheDocument()
    expect(screen.getByText('Grupo We Lemu')).toBeInTheDocument()
    expect(screen.getByLabelText('Nombre de unidad')).toHaveAttribute('placeholder', 'Buscar por nombre')
    expect(screen.queryByLabelText('Grupo')).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Rama')).not.toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Nombre de unidad'), { target: { value: 'Tropa' } })
    fireEvent.click(screen.getByRole('button', { name: 'Aplicar filtros' }))
    expect(getUnidades).toHaveBeenLastCalledWith({ search: 'Tropa' })
  })
})
