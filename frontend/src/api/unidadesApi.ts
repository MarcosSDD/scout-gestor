import { httpClient } from './httpClient'
import type { ApiSuccess, PaginatedMeta } from './types'

export type UnidadListItem = {
  id: number; grupo: number; grupo_nombre: string; rama: number; rama_nombre: string; nombre: string
  tipo_composicion: string; estado: string; cupo_maximo: number | null
}

export type UnidadesQueryParams = {
  page?: number; search?: string; estado?: string; grupo_id?: number; rama_id?: number
}

export async function getUnidades(params?: UnidadesQueryParams): Promise<ApiSuccess<UnidadListItem[], PaginatedMeta>> {
  const { data } = await httpClient.get<ApiSuccess<UnidadListItem[], PaginatedMeta>>('/unidades/', { params })
  return data
}
