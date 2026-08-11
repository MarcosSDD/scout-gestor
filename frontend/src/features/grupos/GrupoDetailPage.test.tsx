import { screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import { getGrupo, getGrupoEstructura } from '../../api/gruposApi'
import { renderWithQueryClient } from '../../test/renderWithQueryClient'
import { GrupoDetailPage } from './GrupoDetailPage'
import { AuthContext } from '../auth/AuthContext'

const auth = { status: 'authenticated' as const, isAuthenticated: true, login: vi.fn(), logout: vi.fn(), user: { id: 1, username: 'staff', email: '', first_name: '', last_name: '', is_staff: true, is_superuser: false, persona_id: 1, responsable_grupo_ids: [], unidad_roles: [], is_apoderado: false } }

vi.mock('../../api/gruposApi', () => ({ getGrupo: vi.fn(), getGrupoEstructura: vi.fn() }))

describe('GrupoDetailPage', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders detail and the visible hierarchy with RN-05 alerts', async () => {
    vi.mocked(getGrupo).mockResolvedValue({ success: true, message: 'OK', data: {
      id: 7, nombre_oficial: 'Grupo We Lemu', zona: 1, zona_nombre: 'Zona Centro', distrito: 2,
      distrito_nombre: 'Distrito Norte', tipo_grupo: 'PLURICONFESIONAL', religion: '', estado_vigencia: 'ACTIVO',
      direccion: 'Av. Scout 123', comuna: 'Santiago', referencia: '', latitud: null, longitud: null, logo: '',
      minimo_miembros_calculado: 20, created_at: '2026-01-01', updated_at: '2026-01-01',
    } })
    vi.mocked(getGrupoEstructura).mockResolvedValue({ success: true, message: 'OK', data: {
      id: 7, nombre_oficial: 'Grupo We Lemu', zona: { id: 1, nombre: 'Zona Centro' }, distrito: { id: 2, nombre: 'Distrito Norte' },
      resumen: { total_ramas: 1, total_unidades: 1, total_subgrupos: 0, total_beneficiarios: 1, total_adultos: 0, total_alertas_etarias: 1 },
      ramas: [{ id: 3, nombre: 'Tropa', edad_minima: 11, edad_maxima: 15, composicion_permitida: 'MIXTA', unidades: [{
        id: 4, nombre: 'Tropa A', estado: 'ACTIVA', tipo_composicion: 'MIXTA', es_activa: true, equipo_adulto: [], subgrupos: [],
        beneficiarios: [{ id: 5, persona_id: 6, rut: '11.111.111-1', nombres: 'Sofi', apellidos: 'Perez', sexo: 'FEMENINO', estado: 'ACTIVO', edad: 16, alertas: [{ code: 'EDAD_FUERA_DE_RANGO', message: 'Beneficiario fuera del rango etario de la rama' }] }],
      }] }],
    } })

    renderWithQueryClient(<AuthContext value={auth}><MemoryRouter initialEntries={['/app/grupos/7']}><Routes><Route path="/app/grupos/:grupoId" element={<GrupoDetailPage />} /></Routes></MemoryRouter></AuthContext>)

    expect(await screen.findByRole('heading', { name: 'Grupo We Lemu' })).toBeInTheDocument()
    expect(screen.getByText('Sofi Perez')).toBeInTheDocument()
    expect(screen.getByText(/Alerta RN-05/i)).toBeInTheDocument()
    expect(screen.queryByText('11.111.111-1')).not.toBeInTheDocument()
  })

  it('rejects invalid ids without issuing requests', async () => {
    renderWithQueryClient(<AuthContext value={auth}><MemoryRouter initialEntries={['/app/grupos/invalido']}><Routes><Route path="/app/grupos/:grupoId" element={<GrupoDetailPage />} /></Routes></MemoryRouter></AuthContext>)

    expect(screen.getByRole('heading', { name: 'Grupo no encontrado' })).toBeInTheDocument()
    expect(getGrupo).not.toHaveBeenCalled()
    expect(getGrupoEstructura).not.toHaveBeenCalled()
  })
})
