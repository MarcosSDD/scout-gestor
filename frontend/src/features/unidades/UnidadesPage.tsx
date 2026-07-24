import type { UnidadListItem, UnidadesQueryParams } from '../../api/unidadesApi'
import { DataListPage, type ListColumn, type ListFilter } from '../data-list/DataListPage'
import { useListSearchParams } from '../data-list/useListSearchParams'
import { useUnidadesQuery } from './useUnidadesQuery'

export function UnidadesPage() {
  const list = useListSearchParams(['search', 'estado', 'grupo_id', 'rama_id'])
  const query = useUnidadesQuery({ ...list.params, grupo_id: numberOrUndefined(list.params.grupo_id), rama_id: numberOrUndefined(list.params.rama_id) } as UnidadesQueryParams)
  const filters: ListFilter[] = [{ name: 'search', label: 'Buscar', type: 'search' }, { name: 'estado', label: 'Estado', type: 'select', options: [{ value: 'ACTIVA', label: 'Activa' }, { value: 'INACTIVA', label: 'Inactiva' }] }, { name: 'grupo_id', label: 'Grupo', type: 'number' }, { name: 'rama_id', label: 'Rama', type: 'number' }]
  const columns: ListColumn<UnidadListItem>[] = [{ label: 'Unidad', render: (item) => item.nombre }, { label: 'Grupo', render: (item) => item.grupo_nombre }, { label: 'Rama', render: (item) => item.rama_nombre }, { label: 'Estado', render: (item) => item.estado }, { label: 'Cupo', render: (item) => item.cupo_maximo ?? 'Sin limite' }]
  return <DataListPage eyebrow="Organizacion" title="Unidades" description="Unidades visibles para tu perfil y sus datos operativos de lectura." items={query.data?.data ?? []} meta={query.data?.meta} filters={filters} params={list.params} columns={columns} isLoading={query.isLoading} isError={query.isError} error={query.error as never} onRetry={() => void query.refetch()} onApplyFilters={list.applyFilters} onPageChange={list.goToPage} />
}

function numberOrUndefined(value: unknown) {
  const number = Number(value)
  return Number.isInteger(number) && number > 0 ? number : undefined
}
