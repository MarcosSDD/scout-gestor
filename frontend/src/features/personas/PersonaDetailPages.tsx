import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { downloadPrivateCertificate } from '../../api/personasApi'

import type { DetailItem } from '../details/DetailView'
import { DetailView } from '../details/DetailView'
import { useAuth } from '../auth/useAuth'
import { useAdultoDetailQuery, useApoderadoDetailQuery, useBeneficiarioDetailQuery, usePersonaDetailQuery } from './usePersonasQueries'

function idFromParam(value?: string) { const id = Number(value); return Number.isInteger(id) && id > 0 ? id : 0 }
type PersonFields = { nombres?: string; apellidos?: string; estado?: string; rut?: string; fecha_nacimiento?: string; sexo?: string; direccion?: string; telefono?: string; email?: string }

function personName(person: Pick<PersonFields, 'nombres' | 'apellidos'>) {
  return [person.nombres, person.apellidos].filter(Boolean).join(' ')
}

function personItems(person: PersonFields): DetailItem[] {
  return [
    { label: 'Nombre', value: personName(person) }, { label: 'Estado', value: person.estado },
    { label: 'RUT', value: person.rut }, { label: 'Nacimiento', value: person.fecha_nacimiento }, { label: 'Sexo', value: person.sexo },
    { label: 'Dirección', value: person.direccion }, { label: 'Teléfono', value: person.telefono }, { label: 'Correo', value: person.email },
  ]
}

export function PersonaDetailPage({ own = false, forcedId }: { own?: boolean; forcedId?: number | null }) {
  const { personaId } = useParams(); const id = forcedId ?? idFromParam(personaId); const query = usePersonaDetailQuery(id)
  const data = query.data?.data
  return <>{query.data?.meta?.permissions?.can_edit && data ? <DetailActions links={[{ to: own ? '/app/perfil/editar' : `/app/personas/${data.id}/editar`, label: 'Editar persona' }]} /> : null}<DetailView title={own ? 'Mi perfil' : data ? personName(data) || 'Persona' : 'Persona'} eyebrow="Ficha personal" backTo={own ? '/app' : '/app/personas'} backLabel={own ? 'inicio' : 'personas'} items={data ? personItems(data) : []} isLoading={query.isLoading} error={query.error as never} onRetry={() => void query.refetch()} personaId={data?.id} photoAvailable={data?.foto_disponible} photoVersion={data?.updated_at} permissions={query.data?.meta?.permissions} /></>
}

export function OwnPersonaPage() {
  const { user } = useAuth()
  if (!user?.persona_id) return <section className="home-feed detail-page" aria-labelledby="account-title"><Link className="grupos-back-link" to="/app">Volver a inicio</Link><article className="home-card detail-card"><p className="shell-panel-caption">Cuenta</p><h1 id="account-title">Mi perfil</h1><p>Tu cuenta no tiene una persona asociada.</p></article></section>
  return <PersonaDetailPage own forcedId={user.persona_id} />
}

export function AdultoDetailPage() {
  const { adultoId } = useParams(); const query = useAdultoDetailQuery(idFromParam(adultoId)); const data = query.data?.data; const person = data?.persona
  return <>{data && (query.data?.meta?.permissions?.can_renew_certificate || query.data?.meta?.permissions?.can_download_certificate) ? <DetailActions links={query.data.meta.permissions?.can_renew_certificate ? [{ to: 'certificado', label: 'Renovar certificado' }] : []} certificateId={query.data.meta.permissions?.can_download_certificate ? data.id : undefined} /> : null}<DetailView title={person ? personName(person) || 'Adulto' : 'Adulto'} eyebrow="Ficha de adulto" backTo="/app/personas/adultos" backLabel="adultos" items={data ? [...personItems(data.persona), { label: 'Rol', value: data.rol_principal }] : []} isLoading={query.isLoading} error={query.error as never} onRetry={() => void query.refetch()} personaId={person?.id} photoAvailable={person?.foto_disponible} photoVersion={person?.updated_at} permissions={query.data?.meta?.permissions} /></>
}

export function BeneficiarioDetailPage() {
  const { beneficiarioId } = useParams(); const query = useBeneficiarioDetailQuery(idFromParam(beneficiarioId)); const data = query.data?.data; const person = data?.persona
  const permissions = query.data?.meta?.permissions
  return <>{data && (permissions?.can_edit || permissions?.can_reassign_unit || permissions?.can_manage_progression) ? <DetailActions links={[...(permissions.can_edit ? [{ to: 'editar', label: 'Editar beneficiario' }] : []), ...(permissions.can_reassign_unit ? [{ to: 'asignacion', label: 'Asignar unidad' }] : []), ...(permissions.can_manage_progression ? [{ to: 'progresiones', label: 'Ver progresión' }] : [])]} /> : null}<DetailView title={person ? personName(person) || 'Beneficiario' : 'Beneficiario'} eyebrow="Ficha de beneficiario" backTo="/app/personas/beneficiarios" backLabel="beneficiarios" items={data ? [...personItems(data.persona), { label: 'Rama', value: data.rama_nombre }, { label: 'Unidad', value: data.unidad_nombre }, { label: 'Grupo', value: data.grupo_nombre }, { label: 'Ingreso', value: data.fecha_ingreso }] : []} isLoading={query.isLoading} error={query.error as never} onRetry={() => void query.refetch()} personaId={person?.id} photoAvailable={person?.foto_disponible} photoVersion={person?.updated_at} permissions={permissions} /></>
}

function DetailActions({ links, certificateId }: { links: { to: string; label: string }[]; certificateId?: number }) {
  const [downloadError, setDownloadError] = useState('')
  async function downloadCertificate() { if (!certificateId) return; try { const file = await downloadPrivateCertificate(certificateId); const anchor = document.createElement('a'); anchor.href = file.url; anchor.download = file.filename ?? 'certificado'; anchor.click(); URL.revokeObjectURL(file.url) } catch { setDownloadError('No fue posible descargar el certificado.') } }
  return <nav className="detail-actions" aria-label="Acciones de la ficha">{links.map((link) => <Link key={link.to} className="secondary-link" to={link.to}>{link.label}</Link>)}{certificateId ? <button className="secondary-link" type="button" onClick={() => void downloadCertificate()}>Descargar certificado</button> : null}{downloadError ? <p role="alert">{downloadError}</p> : null}</nav>
}

export function ApoderadoDetailPage() {
  const { apoderadoId } = useParams(); const query = useApoderadoDetailQuery(idFromParam(apoderadoId)); const data = query.data?.data; const person = data?.persona
  return <DetailView title={person ? personName(person) || 'Apoderado' : 'Apoderado'} eyebrow="Ficha de apoderado" backTo="/app/personas/apoderados" backLabel="apoderados" items={data ? [...personItems(data.persona), { label: 'Miembro de comité', value: data.es_miembro_comite }, { label: 'Rol de comité', value: data.rol_comite }] : []} isLoading={query.isLoading} error={query.error as never} onRetry={() => void query.refetch()} personaId={person?.id} photoAvailable={person?.foto_disponible} permissions={query.data?.meta?.permissions} />
}
