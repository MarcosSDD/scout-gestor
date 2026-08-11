import { useId, useState } from 'react'
import type { Opcion, Subgrupo } from '../../api/unidadesApi'

type Props = { label: string; value: number | null; onChange: (id: number) => void; query: { data?: { data: Array<Opcion | Subgrupo>; meta?: { next: string | null; previous: string | null; count: number } }; isLoading: boolean; isError: boolean }; onSearch?: (search: string) => void; onPageChange?: (page: number) => void; error?: string; disabled?: boolean }
export function PaginatedOptionPicker({ label, value, onChange, query, onSearch, onPageChange, error, disabled }: Props) {
  const id = useId(); const [search, setSearch] = useState(''); const options = query.data?.data ?? []; const meta = query.data?.meta
  return <fieldset className="option-picker" aria-describedby={`${id}-status ${error ? `${id}-error` : ''}`}><legend>{label}</legend>
    {onSearch ? <label className="visually-hidden" htmlFor={`${id}-search`}>Buscar {label}</label> : null}
    {onSearch ? <input id={`${id}-search`} type="search" value={search} onChange={(e) => { setSearch(e.target.value); onSearch(e.target.value) }} placeholder="Buscar…" disabled={disabled} /> : null}
    <div className="option-picker__options" role="radiogroup" aria-label={label}>{options.map((option) => <label key={option.id}><input type="radio" name={id} checked={value === option.id} disabled={disabled} onChange={() => onChange(option.id)} /><span>{'unidad_nombre' in option ? `${option.unidad_nombre} · ${option.nombre}` : option.nombre}</span></label>)}</div>
    <p id={`${id}-status`} className="option-picker__status" aria-live="polite">{query.isLoading ? 'Cargando opciones…' : query.isError ? 'No fue posible cargar las opciones permitidas.' : `${meta?.count ?? options.length} opciones disponibles.`}</p>
    {onPageChange ? <div className="option-picker__pagination"><button type="button" onClick={() => onPageChange(-1)} disabled={!meta?.previous}>Anterior</button><button type="button" onClick={() => onPageChange(1)} disabled={!meta?.next}>Siguiente</button></div> : null}
    {error ? <p id={`${id}-error`} className="form-control__error" role="alert">{error}</p> : null}
  </fieldset>
}
