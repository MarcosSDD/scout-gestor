import type { AdultoListItem, AdultosQueryParams, ApoderadoListItem, ApoderadosQueryParams, BeneficiarioListItem, BeneficiariosQueryParams, PersonaListItem, PersonasQueryParams } from '../../api/personasApi'
import { DataListPage, type ListColumn, type ListFilter } from '../data-list/DataListPage'
import { useListSearchParams } from '../data-list/useListSearchParams'
import { useAdultosQuery, useApoderadosQuery, useBeneficiariosQuery, usePersonasQuery } from './usePersonasQueries'

const stateFilter: ListFilter = { name: 'estado', label: 'Estado', type: 'select', options: [{ value: 'ACTIVO', label: 'Activo' }, { value: 'INACTIVO', label: 'Inactivo' }] }
const searchFilter: ListFilter = { name: 'search', label: 'Buscar', type: 'search' }

export function PersonasPage() {
  const list = useListSearchParams(['search', 'estado'])
  const query = usePersonasQuery(list.params as PersonasQueryParams)
  return <DataListPage<PersonaListItem> eyebrow="Gestion" title="Personas" description="Personas disponibles para tu perfil, con datos de identificacion minima." items={query.data?.data ?? []} meta={query.data?.meta} filters={[searchFilter, stateFilter]} params={list.params} columns={[{ label: 'Nombre', render: (item) => item.nombre_completo }, { label: 'Estado', render: (item) => item.estado }]} detailPath={(item) => `/app/personas/${item.id}`} isLoading={query.isLoading} isError={query.isError} error={query.error as never} onRetry={() => void query.refetch()} onApplyFilters={list.applyFilters} onPageChange={list.goToPage} />
}

export function AdultosPage() {
  const list = useListSearchParams(['search', 'estado', 'rol_principal', 'certificado_vigente'])
  const query = useAdultosQuery(list.params as AdultosQueryParams)
  const filters: ListFilter[] = [searchFilter, stateFilter, { name: 'rol_principal', label: 'Rol', type: 'select', options: [{ value: 'GUIA', label: 'Guia' }, { value: 'DIRIGENTE', label: 'Dirigente' }, { value: 'RESP_GRUPO', label: 'Responsable de grupo' }, { value: 'APODERADO', label: 'Apoderado' }, { value: 'COLABORADOR', label: 'Colaborador' }] }, { name: 'certificado_vigente', label: 'Certificado', type: 'select', options: [{ value: 'true', label: 'Vigente' }, { value: 'false', label: 'Vencido' }] }]
  const columns: ListColumn<AdultoListItem>[] = [{ label: 'Nombre', render: (item) => item.persona_nombre }, { label: 'Rol', render: (item) => item.rol_principal }, { label: 'Certificado', render: (item) => item.certificado_vigente ? `Vigente hasta ${item.certificado_vigencia_hasta}` : 'Vencido' }]
  return <DataListPage eyebrow="Gestion de personas" title="Adultos" description="Equipo adulto visible sin exponer documentos sensibles." items={query.data?.data ?? []} meta={query.data?.meta} filters={filters} params={list.params} columns={columns} detailPath={(item) => `/app/personas/adultos/${item.id}`} isLoading={query.isLoading} isError={query.isError} error={query.error as never} onRetry={() => void query.refetch()} onApplyFilters={list.applyFilters} onPageChange={list.goToPage} />
}

export function BeneficiariosPage() {
  const list = useListSearchParams(['search', 'estado', 'unidad_id', 'rama_id'])
  const query = useBeneficiariosQuery({ ...list.params, unidad_id: numberOrUndefined(list.params.unidad_id), rama_id: numberOrUndefined(list.params.rama_id) } as BeneficiariosQueryParams)
  const filters: ListFilter[] = [searchFilter, stateFilter, { name: 'unidad_id', label: 'Unidad', type: 'number' }, { name: 'rama_id', label: 'Rama', type: 'number' }]
  const columns: ListColumn<BeneficiarioListItem>[] = [{ label: 'Nombre', render: (item) => item.persona_nombre }, { label: 'Rama', render: (item) => item.rama_nombre ?? 'Sin rama' }, { label: 'Unidad', render: (item) => item.unidad_nombre ?? 'Sin unidad' }, { label: 'Ingreso', render: (item) => item.fecha_ingreso }]
  return <DataListPage eyebrow="Gestion de personas" title="Beneficiarios" description="Beneficiarios dentro de las unidades autorizadas." items={query.data?.data ?? []} meta={query.data?.meta} filters={filters} params={list.params} columns={columns} detailPath={(item) => `/app/personas/beneficiarios/${item.id}`} isLoading={query.isLoading} isError={query.isError} error={query.error as never} onRetry={() => void query.refetch()} onApplyFilters={list.applyFilters} onPageChange={list.goToPage} />
}

export function ApoderadosPage() {
  const list = useListSearchParams(['search', 'estado', 'es_miembro_comite'])
  const query = useApoderadosQuery(list.params as ApoderadosQueryParams)
  const filters: ListFilter[] = [searchFilter, stateFilter, { name: 'es_miembro_comite', label: 'Comite', type: 'select', options: [{ value: 'true', label: 'Miembro' }, { value: 'false', label: 'No miembro' }] }]
  const columns: ListColumn<ApoderadoListItem>[] = [{ label: 'Nombre', render: (item) => item.persona_nombre }, { label: 'Comite', render: (item) => item.es_miembro_comite ? (item.rol_comite || 'Miembro') : 'No pertenece' }, { label: 'Estado', render: (item) => item.persona_estado }]
  return <DataListPage eyebrow="Gestion de personas" title="Apoderados" description="Apoderados disponibles segun tu alcance de datos." items={query.data?.data ?? []} meta={query.data?.meta} filters={filters} params={list.params} columns={columns} detailPath={(item) => `/app/personas/apoderados/${item.id}`} isLoading={query.isLoading} isError={query.isError} error={query.error as never} onRetry={() => void query.refetch()} onApplyFilters={list.applyFilters} onPageChange={list.goToPage} />
}

function numberOrUndefined(value: unknown) {
  const number = Number(value)
  return Number.isInteger(number) && number > 0 ? number : undefined
}
