import { fireEvent, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import { getGrupos } from '../../api/gruposApi'
import { renderWithQueryClient } from '../../test/renderWithQueryClient'
import { GruposPage } from './GruposPage'

vi.mock('../../api/gruposApi', () => ({ getGrupos: vi.fn() }))

const envelope = {
  success: true as const,
  message: 'OK',
  meta: { count: 2, next: 'http://test/api/v1/grupos/?page=2', previous: null },
  data: [{
    id: 7, nombre_oficial: 'Grupo We Lemu', zona: 1, zona_nombre: 'Zona Centro', distrito: 2,
    distrito_nombre: 'Distrito Norte', tipo_grupo: 'PLURICONFESIONAL', estado_vigencia: 'ACTIVO',
    comuna: 'Santiago', logo: '', minimo_miembros_calculado: 20, total_beneficiarios_activos: 10, total_adultos_activos: 4,
  }],
}

describe('GruposPage', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders accessible groups and submits filters', async () => {
    vi.mocked(getGrupos).mockResolvedValue(envelope)
    renderWithQueryClient(<MemoryRouter><GruposPage /></MemoryRouter>)

    expect(await screen.findByRole('heading', { name: 'Grupo We Lemu' })).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Buscar grupo'), { target: { value: 'Lemu' } })
    fireEvent.change(screen.getByLabelText('Estado de vigencia'), { target: { value: 'ACTIVO' } })
    fireEvent.click(screen.getByRole('button', { name: 'Aplicar filtros' }))

    expect(await screen.findByRole('link', { name: 'Ver grupo' })).toHaveAttribute('href', '/app/grupos/7')
    expect(getGrupos).toHaveBeenLastCalledWith({ search: 'Lemu', estado_vigencia: 'ACTIVO' })
  })

  it('shows an empty accessible state', async () => {
    vi.mocked(getGrupos).mockResolvedValue({ success: true, message: 'OK', data: [] })
    renderWithQueryClient(<MemoryRouter><GruposPage /></MemoryRouter>)

    expect(await screen.findByRole('heading', { name: 'Sin grupos accesibles' })).toBeInTheDocument()
  })
})
