import type { ChangeEventHandler, FormEvent, ReactNode } from 'react'
import { Link } from 'react-router-dom'

import type { ApiError, PaginatedMeta } from '../../api/types'
import { GrupoStateCard } from '../grupos/GrupoStateCard'

export type ListFilter = {
  name: string; label: string; type?: 'search' | 'select' | 'number'; placeholder?: string; options?: Array<{ value: string; label: string }>
  value?: string; onChange?: ChangeEventHandler<HTMLSelectElement>; disabled?: boolean; loading?: boolean; emptyOption?: string
}
export type ListColumn<T> = { label: string; render: (item: T) => ReactNode }

type DataListPageProps<T extends { id: number }> = {
  eyebrow: string
  title: string
  description: string
  items: T[]
  meta?: PaginatedMeta
  filters: ListFilter[]
  params: Record<string, unknown>
  columns: ListColumn<T>[]
  isLoading: boolean
  isError: boolean
  error: ApiError | null
  onRetry: () => void
  onApplyFilters: (formData: FormData) => void
  onPageChange: (page: number) => void
  detailPath?: (item: T) => string
  heroAction?: ReactNode
}

export function DataListPage<T extends { id: number }>(props: DataListPageProps<T>) {
  const { eyebrow, title, description, items, meta, filters, params, columns, isLoading, isError, error, onRetry, onApplyFilters, onPageChange, detailPath, heroAction } = props
  const page = typeof params.page === 'number' ? params.page : 1

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    onApplyFilters(new FormData(event.currentTarget))
  }

  if (isLoading) return <GrupoStateCard title={`Cargando ${title.toLowerCase()}...`} message="Estamos preparando la informacion disponible para tu perfil." />
  if (isError) return <GrupoStateCard title={`No fue posible cargar ${title.toLowerCase()}`} message="Intenta nuevamente en unos segundos." error={error} onRetry={onRetry} />

  const hasFilters = filters.some((filter) => Boolean(params[filter.name]))
  return (
    <section className="home-feed data-list-page" aria-labelledby="data-list-title">
      <article className="home-card home-card--hero grupos-hero-card">
        <div><p className="shell-panel-caption">{eyebrow}</p><h1 id="data-list-title">{title}</h1><p>{description}</p></div>
        <div className="data-list-hero-actions"><span className="dashboard-status-badge">{meta?.count ?? items.length} registros</span>{heroAction}</div>
      </article>
      <form className="home-card grupos-filters data-list-filters" onSubmit={submit} aria-label={`Filtros de ${title.toLowerCase()}`}>
        {filters.map((filter) => (
          <label key={filter.name}>
            <span>{filter.label}</span>
            {filter.type === 'select' ? (
              <select name={filter.name} value={filter.value} defaultValue={filter.value === undefined ? String(params[filter.name] ?? '') : undefined} onChange={filter.onChange} disabled={filter.disabled || filter.loading}>
                <option value="">{filter.loading ? `Cargando ${filter.label.toLowerCase()}…` : filter.emptyOption ?? 'Todos'}</option>{filter.options?.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
              </select>
            ) : <input name={filter.name} type={filter.type ?? 'search'} defaultValue={String(params[filter.name] ?? '')} placeholder={filter.placeholder ?? (filter.type === 'number' ? 'Identificador' : 'Buscar')} />}
          </label>
        ))}
        <button className="primary-button" type="submit">Aplicar filtros</button>
      </form>
      {items.length === 0 ? <GrupoStateCard title={hasFilters ? 'Sin resultados' : `Sin ${title.toLowerCase()} accesibles`} message={hasFilters ? 'Prueba con otros filtros.' : 'No hay informacion disponible para tu perfil.'} /> : (
        <ul className="data-list" aria-live="polite">
          {items.map((item) => <li className="home-card data-list__item" key={item.id}>{columns.map((column, index) => <div key={column.label}><span>{column.label}</span><strong>{index === 0 && detailPath ? <Link className="data-list__detail-link" to={detailPath(item)} aria-label={`Ver ficha de ${String(column.render(item))}`}>{column.render(item)}</Link> : column.render(item)}</strong></div>)}</li>)}
        </ul>
      )}
      {(meta?.previous || meta?.next) && <nav className="grupos-pagination" aria-label={`Paginacion de ${title.toLowerCase()}`}><button type="button" disabled={!meta.previous} onClick={() => onPageChange(page - 1)}>Anterior</button><span>Pagina {page}</span><button type="button" disabled={!meta.next} onClick={() => onPageChange(page + 1)}>Siguiente</button></nav>}
    </section>
  )
}
