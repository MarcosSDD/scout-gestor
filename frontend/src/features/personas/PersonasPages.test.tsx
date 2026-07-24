import { fireEvent, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import { getPersonas } from '../../api/personasApi'
import { renderWithQueryClient } from '../../test/renderWithQueryClient'
import { PersonasPage } from './PersonasPages'

vi.mock('../../api/personasApi', () => ({ getPersonas: vi.fn(), getAdultos: vi.fn(), getBeneficiarios: vi.fn(), getApoderados: vi.fn() }))

describe('PersonasPage', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders minimal PII and persists filters through the URL query', async () => {
    vi.mocked(getPersonas).mockResolvedValue({ success: true, message: 'OK', meta: { count: 1, next: null, previous: null }, data: [{ id: 1, nombre_completo: 'Ana Rojas', estado: 'ACTIVO' }] })
    renderWithQueryClient(<MemoryRouter><PersonasPage /></MemoryRouter>)

    expect(await screen.findByText('Ana Rojas')).toBeInTheDocument()
    expect(screen.queryByText('11.111.111-1')).not.toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Buscar'), { target: { value: 'Ana' } })
    fireEvent.click(screen.getByRole('button', { name: 'Aplicar filtros' }))
    expect(getPersonas).toHaveBeenLastCalledWith({ search: 'Ana' })
  })
})
