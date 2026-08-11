import { httpClient } from './httpClient'
import { getBeneficiarioOptions, getMembresiaDestinoOptions, getUnidades, patchAdultoUnidadRol, reassignSubgrupoMiembro } from './unidadesApi'

vi.mock('./httpClient', () => ({ httpClient: { get: vi.fn(), patch: vi.fn() } }))

describe('unidadesApi', () => {
  it('sends unit filters to the API', async () => {
    vi.mocked(httpClient.get).mockResolvedValueOnce({ data: { success: true, message: 'OK', data: [] } })
    await getUnidades({ search: 'Tropa', estado: 'ACTIVA', grupo_id: 2 })
    expect(httpClient.get).toHaveBeenCalledWith('/unidades/', { params: { search: 'Tropa', estado: 'ACTIVA', grupo_id: 2 } })
  })

  it('uses the exact structural option and command contracts', async () => {
    vi.mocked(httpClient.get).mockResolvedValue({ data: { success: true, message: 'OK', data: [{ id: 11, nombre: 'Patrulla Puma', unidad: 2, unidad_nombre: 'Tropa' }] } })
    vi.mocked(httpClient.patch).mockResolvedValue({ data: { success: true, message: 'OK', data: {} } })
    await getBeneficiarioOptions({ subgrupo_id: 7, page: 2 })
    const destinations = await getMembresiaDestinoOptions({ miembro_id: 9 })
    await reassignSubgrupoMiembro(9, 11)
    await patchAdultoUnidadRol(4, 'ASISTENTE')
    expect(httpClient.get).toHaveBeenCalledWith('/unidades/opciones/beneficiarios/', { params: { subgrupo_id: 7, page: 2 } })
    expect(httpClient.get).toHaveBeenCalledWith('/unidades/opciones/destinos-membresia/', { params: { miembro_id: 9 } })
    expect(httpClient.patch).toHaveBeenCalledWith('/unidades/subgrupos-miembros/9/reasignacion/', { subgrupo: 11 })
    expect(httpClient.patch).toHaveBeenCalledWith('/unidades/adultos-roles/4/', { rol: 'ASISTENTE' })
    expect(destinations.data[0]).toMatchObject({ unidad: 2, unidad_nombre: 'Tropa' })
  })
})
