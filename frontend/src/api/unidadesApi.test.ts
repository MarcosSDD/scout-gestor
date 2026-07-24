import { httpClient } from './httpClient'
import { getUnidades } from './unidadesApi'

vi.mock('./httpClient', () => ({ httpClient: { get: vi.fn() } }))

describe('unidadesApi', () => {
  it('sends unit filters to the API', async () => {
    vi.mocked(httpClient.get).mockResolvedValueOnce({ data: { success: true, message: 'OK', data: [] } })
    await getUnidades({ search: 'Tropa', estado: 'ACTIVA', grupo_id: 2 })
    expect(httpClient.get).toHaveBeenCalledWith('/unidades/', { params: { search: 'Tropa', estado: 'ACTIVA', grupo_id: 2 } })
  })
})
