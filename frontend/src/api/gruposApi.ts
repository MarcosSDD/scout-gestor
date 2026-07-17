import { httpClient } from './httpClient'
import type { ApiSuccess, PaginatedMeta } from './types'

export type GrupoListItem = {
  id: number
  nombre_oficial: string
  zona: number
  zona_nombre: string
  distrito: number
  distrito_nombre: string
  tipo_grupo: string
  estado_vigencia: string
  comuna: string
  logo: string
  minimo_miembros_calculado: number
  total_beneficiarios_activos: number
  total_adultos_activos: number
}

export type GruposResponse = ApiSuccess<GrupoListItem[], PaginatedMeta>

export async function getGrupos(): Promise<GruposResponse> {
  const { data } = await httpClient.get<GruposResponse>('/grupos/')
  return data
}
