import { httpClient } from './httpClient'
import { getGrupos } from './gruposApi'

vi.mock('./httpClient', () => ({
  httpClient: {
    get: vi.fn(),
  },
}))

describe('getGrupos', () => {
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

    expect(httpClient.get).toHaveBeenCalledWith('/grupos/')
    expect(result).toEqual(envelope)
  })
})
