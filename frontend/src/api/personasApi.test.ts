import { httpClient } from './httpClient'
import { getAdultos, getApoderados, getBeneficiarios, getPersonas, patchBeneficiario, patchPersona, patchProgresion } from './personasApi'

vi.mock('./httpClient', () => ({ httpClient: { get: vi.fn(), patch: vi.fn() } }))

describe('personasApi', () => {
  beforeEach(() => { vi.mocked(httpClient.get).mockReset(); vi.mocked(httpClient.patch).mockReset() })

  it('sends filters to each read endpoint', async () => {
    vi.mocked(httpClient.get).mockResolvedValue({ data: { success: true, message: 'OK', data: [] } })
    await getPersonas({ search: 'Ana', estado: 'ACTIVO' })
    await getAdultos({ rol_principal: 'GUIADORA' })
    await getBeneficiarios({ unidad_id: 4 })
    await getApoderados({ es_miembro_comite: 'true' })

    expect(httpClient.get).toHaveBeenNthCalledWith(1, '/personas/', { params: { search: 'Ana', estado: 'ACTIVO' } })
    expect(httpClient.get).toHaveBeenNthCalledWith(2, '/personas/adultos/', { params: { rol_principal: 'GUIADORA' } })
    expect(httpClient.get).toHaveBeenNthCalledWith(3, '/personas/beneficiarios/', { params: { unidad_id: 4 } })
    expect(httpClient.get).toHaveBeenNthCalledWith(4, '/personas/apoderados/', { params: { es_miembro_comite: 'true' } })
  })

  it('envía PATCH de beneficiario y progresión con los contratos acotados', async () => {
    vi.mocked(httpClient.patch).mockResolvedValue({ data: { success: true, message: 'OK', data: {} } })
    await patchBeneficiario(4, { fecha_ingreso: '2020-01-01' })
    await patchProgresion(7, { beneficiario: 4, fecha: '2025-01-01', tipo: 'DURANTE_CICLO', texto: 'Avance observado', areas: [1, 2] })
    expect(httpClient.patch).toHaveBeenNthCalledWith(1, '/personas/beneficiarios/4/', { fecha_ingreso: '2020-01-01' })
    expect(httpClient.patch).toHaveBeenNthCalledWith(2, '/personas/progresiones/7/', { beneficiario: 4, fecha: '2025-01-01', tipo: 'DURANTE_CICLO', texto: 'Avance observado', areas: [1, 2] })
  })

  it('usa FormData para una foto seleccionada', async () => {
    vi.mocked(httpClient.patch).mockResolvedValue({ data: { success: true, message: 'OK', data: {} } })
    await patchPersona(2, { foto: new File(['x'], 'foto.jpg', { type: 'image/jpeg' }) })
    expect(vi.mocked(httpClient.patch).mock.calls[0]?.[1]).toBeInstanceOf(FormData)
  })
})
