import { httpClient } from './httpClient'
import { getAdultos, getApoderados, getBeneficiarios, getPersonas } from './personasApi'

vi.mock('./httpClient', () => ({ httpClient: { get: vi.fn() } }))

describe('personasApi', () => {
  beforeEach(() => vi.mocked(httpClient.get).mockReset())

  it('sends filters to each read endpoint', async () => {
    vi.mocked(httpClient.get).mockResolvedValue({ data: { success: true, message: 'OK', data: [] } })
    await getPersonas({ search: 'Ana', estado: 'ACTIVO' })
    await getAdultos({ rol_principal: 'GUIA' })
    await getBeneficiarios({ unidad_id: 4 })
    await getApoderados({ es_miembro_comite: 'true' })

    expect(httpClient.get).toHaveBeenNthCalledWith(1, '/personas/', { params: { search: 'Ana', estado: 'ACTIVO' } })
    expect(httpClient.get).toHaveBeenNthCalledWith(2, '/personas/adultos/', { params: { rol_principal: 'GUIA' } })
    expect(httpClient.get).toHaveBeenNthCalledWith(3, '/personas/beneficiarios/', { params: { unidad_id: 4 } })
    expect(httpClient.get).toHaveBeenNthCalledWith(4, '/personas/apoderados/', { params: { es_miembro_comite: 'true' } })
  })
})
