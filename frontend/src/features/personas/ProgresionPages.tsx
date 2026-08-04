import { zodResolver } from '@hookform/resolvers/zod'
import { useEffect, useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { toast } from 'react-toastify'
import { toApiError } from '../../api/errors'
import { FormActions } from '../forms/FormActions'
import { applyDrfErrors } from '../forms/applyDrfErrors'
import { FormCheckboxGroup } from '../forms/FormCheckboxGroup'
import { FormErrorSummary } from '../forms/FormErrorSummary'
import { FormField } from '../forms/FormField'
import { FormSelect } from '../forms/FormSelect'
import { FormTextarea } from '../forms/FormTextarea'
import { useUnsavedChanges } from '../forms/useUnsavedChanges'
import { progresionSchema, type ProgresionFormValues } from './personasSchemas'
import { useAreasDesarrolloQuery, useProgresionMutation, useProgresionQuery, useProgresionesQuery } from './usePersonasMutations'

const id = (value?: string) => Number.isInteger(Number(value)) && Number(value) > 0 ? Number(value) : 0
const summaryErrors = (errors: Record<string, { message?: string }>, global: string[]) => [...Object.entries(errors).map(([name, error]) => ({ name, message: error.message })), ...global.map((message) => ({ message }))]
const tipoLabels = { INICIO_CICLO: 'Inicio de ciclo', DURANTE_CICLO: 'Durante el ciclo', FINAL_CICLO: 'Final de ciclo' }
export function ProgresionesPage() { const beneficiario = id(useParams().beneficiarioId); const query = useProgresionesQuery(beneficiario); return <section className="home-feed" aria-labelledby="progress-title"><article className="home-card"><div className="page-heading"><div><p className="shell-panel-caption">Progresión scout</p><h1 id="progress-title">Registros de progresión</h1></div><Link className="secondary-link" to="nuevo">Registrar avance</Link></div>{query.isLoading ? <p role="status">Cargando registros…</p> : query.isError ? <p role="alert">{toApiError(query.error).error.message}</p> : <ul className="progress-list">{query.data?.data.length ? query.data.data.map((registro) => <li key={registro.id}><strong>{tipoLabels[registro.tipo]}</strong><span>{registro.fecha} · {registro.areas.map((area) => area.nombre).join(', ')}</span><p>{registro.texto}</p><Link to={`${registro.id}/editar`}>Editar registro</Link></li>) : <li>No hay registros de progresión disponibles.</li>}</ul>}</article></section> }

export function ProgresionFormPage() {
  const { beneficiarioId, progresionId } = useParams(); const beneficiario = id(beneficiarioId); const progresionIdNumber = id(progresionId); const detail = useProgresionQuery(progresionIdNumber); const areas = useAreasDesarrolloQuery(); const mutation = useProgresionMutation(beneficiario, progresionIdNumber || undefined); const navigate = useNavigate(); const [globalErrors, setGlobalErrors] = useState<string[]>([])
  const form = useForm<ProgresionFormValues>({ resolver: zodResolver(progresionSchema), defaultValues: { beneficiario, fecha: '', tipo: 'DURANTE_CICLO', texto: '', areas: [] } }); useEffect(() => { if (progresionIdNumber && detail.data?.data) { const registro = detail.data.data; form.reset({ beneficiario, fecha: registro.fecha, tipo: registro.tipo, texto: registro.texto, areas: registro.areas.map((area) => area.id) }) } }, [beneficiario, detail.data, form, progresionIdNumber]); useUnsavedChanges(form.formState.isDirty)
  const selectedAreas = useWatch({ control: form.control, name: 'areas' }); const errors = form.formState.errors
  function toggleArea(areaId: number) { form.setValue('areas', selectedAreas.includes(areaId) ? selectedAreas.filter((value) => value !== areaId) : [...selectedAreas, areaId], { shouldDirty: true, shouldValidate: true }) }
  return <section className="home-feed form-page" aria-labelledby="progress-form-title"><Link className="grupos-back-link" to="..">Volver</Link><article className="home-card"><h1 id="progress-form-title">{progresionIdNumber ? 'Editar progreso' : 'Registrar progreso'}</h1><form className="domain-form" noValidate onSubmit={form.handleSubmit(async (values) => { try { await mutation.mutateAsync(values); toast.success('Registro guardado.'); navigate(`/app/personas/beneficiarios/${beneficiario}/progresiones`) } catch (error) { const apiError = toApiError(error); setGlobalErrors(applyDrfErrors(apiError.error.details, form.setError, ['beneficiario', 'fecha', 'tipo', 'texto', 'areas'])) } })}><FormErrorSummary errors={summaryErrors(errors, globalErrors)} /><fieldset><legend>Avance observado</legend><div className="form-grid"><FormSelect label="Momento del ciclo" options={Object.entries(tipoLabels).map(([value, label]) => ({ value, label }))} {...form.register('tipo')} error={errors.tipo?.message} /><FormField label="Fecha" type="date" max={new Date().toISOString().slice(0, 10)} {...form.register('fecha')} error={errors.fecha?.message} /><FormTextarea label="Descripción del avance" rows={5} {...form.register('texto')} error={errors.texto?.message} /></div></fieldset><FormCheckboxGroup legend="Áreas de desarrollo" error={errors.areas?.message} options={(areas.data?.data ?? []).map((area) => ({ value: String(area.id), checked: selectedAreas.includes(area.id), onChange: () => toggleArea(area.id), label: <><strong>{area.nombre}</strong>{area.lema ? ` — ${area.lema}` : ''}</> }))} />{areas.isError ? <p role="alert">No fue posible cargar las áreas de desarrollo.</p> : null}<FormActions isSubmitting={mutation.isPending} submitLabel="Guardar registro" /></form></article></section>
}
