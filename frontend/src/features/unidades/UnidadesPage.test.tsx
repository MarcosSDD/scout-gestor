import { screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import { getUnidades } from '../../api/unidadesApi'
import { renderWithQueryClient } from '../../test/renderWithQueryClient'
import { UnidadesPage } from './UnidadesPage'

vi.mock('../../api/unidadesApi', () => ({ getUnidades: vi.fn() }))

describe('UnidadesPage', () => {
  it('renders accessible unit data', async () => {
    vi.mocked(getUnidades).mockResolvedValueOnce({ success: true, message: 'OK', data: [{ id: 1, grupo: 2, grupo_nombre: 'Grupo We Lemu', rama: 3, rama_nombre: 'Tropa', nombre: 'Tropa A', tipo_composicion: 'MIXTA', estado: 'ACTIVA', cupo_maximo: 32 }] })
    renderWithQueryClient(<MemoryRouter><UnidadesPage /></MemoryRouter>)
    expect(await screen.findByText('Tropa A')).toBeInTheDocument()
    expect(screen.getByText('Grupo We Lemu')).toBeInTheDocument()
  })
})
