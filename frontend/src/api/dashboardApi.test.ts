import { httpClient } from './httpClient'
import { getGrupoDashboard } from './dashboardApi'

vi.mock('./httpClient', () => ({
  httpClient: {
    get: vi.fn(),
  },
}))

describe('getGrupoDashboard', () => {
  it('calls dashboard endpoint and returns typed envelope', async () => {
    const envelope = {
      success: true,
      message: 'Dashboard del grupo',
      data: {
        grupo: { id: 7, nombre_oficial: 'Grupo We Lemu', estado_vigencia: 'ACTIVO' },
        kpis: {
          total_miembros: 14,
          total_beneficiarios_activos: 10,
          total_adultos_activos: 4,
          adultos_con_formacion: 2,
          porcentaje_adultos_con_formacion: 50,
          beneficiarios_con_apoderado_activo: 8,
          porcentaje_beneficiarios_con_apoderado_activo: 80,
        },
        alertas: { cumpleanos_semana: [] },
      },
    }

    vi.mocked(httpClient.get).mockResolvedValueOnce({ data: envelope })

    const result = await getGrupoDashboard(7)

    expect(httpClient.get).toHaveBeenCalledWith('/dashboard/grupo/7/')
    expect(result).toEqual(envelope)
  })
})
