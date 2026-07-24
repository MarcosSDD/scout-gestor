import { httpClient } from './httpClient'
import type { ApiSuccess, PaginatedMeta } from './types'

type ListQueryParams = { page?: number; search?: string; estado?: string }

export type PersonaListItem = { id: number; nombre_completo: string; estado: string }
export type AdultoListItem = {
  id: number; persona: number; persona_nombre: string; persona_estado: string; rol_principal: string
  certificado_vigencia_hasta: string; certificado_vigente: boolean
}
export type BeneficiarioListItem = {
  id: number; persona: number; persona_nombre: string; persona_estado: string; rama_actual: number | null
  rama_nombre: string | null; unidad: number | null; unidad_nombre: string | null; grupo: number | null
  grupo_nombre: string | null; fecha_ingreso: string
}
export type ApoderadoListItem = {
  id: number; persona: number; persona_nombre: string; persona_estado: string; es_miembro_comite: boolean; rol_comite: string
}

export type PersonasQueryParams = ListQueryParams
export type AdultosQueryParams = ListQueryParams & { rol_principal?: string; certificado_vigente?: string; unidad_id?: number; grupo_id?: number }
export type BeneficiariosQueryParams = ListQueryParams & { unidad_id?: number; rama_id?: number; grupo_id?: number }
export type ApoderadosQueryParams = ListQueryParams & { es_miembro_comite?: string; beneficiario_id?: number; unidad_id?: number; grupo_id?: number }

type ListResponse<T> = ApiSuccess<T[], PaginatedMeta>

async function getList<T>(path: string, params?: object): Promise<ListResponse<T>> {
  const { data } = await httpClient.get<ListResponse<T>>(path, { params })
  return data
}

export const getPersonas = (params?: PersonasQueryParams) => getList<PersonaListItem>('/personas/', params)
export const getAdultos = (params?: AdultosQueryParams) => getList<AdultoListItem>('/personas/adultos/', params)
export const getBeneficiarios = (params?: BeneficiariosQueryParams) => getList<BeneficiarioListItem>('/personas/beneficiarios/', params)
export const getApoderados = (params?: ApoderadosQueryParams) => getList<ApoderadoListItem>('/personas/apoderados/', params)
