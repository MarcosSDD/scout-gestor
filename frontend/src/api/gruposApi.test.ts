import { httpClient } from './httpClient'
import { getGrupo, getGrupoEstructura, getGrupos } from './gruposApi'

vi.mock('./httpClient', () => ({
  httpClient: {
    get: vi.fn(),
  },
}))

describe('getGrupos', () => {
  beforeEach(() => {
    vi.mocked(httpClient.get).mockReset()
  })

  it('calls grupos endpoint and returns typed envelope', async () => {
    const envelope = {
      success: true,
      message: 'OK',
      data: [
        {
          id: 7,
          nombre_oficial: 'Grupo We Lemu',
          zona: 1,
          zona_nombre: 'Zona Centro',
          distrito: 2,
          distrito_nombre: 'Distrito Norte',
          tipo_grupo: 'PLURICONFESIONAL',
          estado_vigencia: 'ACTIVO',
          comuna: 'Santiago',
          logo: '',
          minimo_miembros_calculado: 0,
          total_beneficiarios_activos: 10,
          total_adultos_activos: 4,
        },
      ],
    }

    vi.mocked(httpClient.get).mockResolvedValueOnce({ data: envelope })

    const result = await getGrupos()

    expect(httpClient.get).toHaveBeenCalledWith('/grupos/', { params: undefined })
    expect(result).toEqual(envelope)
  })

  it('passes list filters to the backend', async () => {
    vi.mocked(httpClient.get).mockResolvedValueOnce({ data: { success: true, message: 'OK', data: [] } })

    await getGrupos({ page: 2, search: 'Lemu', estado_vigencia: 'ACTIVO' })

    expect(httpClient.get).toHaveBeenCalledWith('/grupos/', {
      params: { page: 2, search: 'Lemu', estado_vigencia: 'ACTIVO' },
    })
  })

  it('requests group detail and structure endpoints', async () => {
    vi.mocked(httpClient.get)
      .mockResolvedValueOnce({ data: { success: true, message: 'OK', data: { id: 7 } } })
      .mockResolvedValueOnce({ data: { success: true, message: 'OK', data: { id: 7, ramas: [] } } })

    await getGrupo(7)
    await getGrupoEstructura(7)

    expect(httpClient.get).toHaveBeenNthCalledWith(1, '/grupos/7/')
    expect(httpClient.get).toHaveBeenNthCalledWith(2, '/grupos/7/estructura/')
  })
})
