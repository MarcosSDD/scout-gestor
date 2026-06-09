import { useAuth } from '../auth/useAuth'
import { hasUnidadRole, isAdminUser, isApoderado, isGrupoResponsable } from '../auth/rbac'

export function HomePage() {
  const { user } = useAuth()
  const displayName = user?.first_name || user?.username || 'scout'
  const roleSummary = getRoleSummary(user)
  const cards = getHomeCards(user)

  return (
    <section className="home-feed" aria-label="Inicio We Lemu">
      <article className="home-card home-card--hero">
        <p className="shell-panel-caption">Sesion activa</p>
        <h1>Bienvenido, {displayName}</h1>
        <p>{roleSummary}</p>
      </article>

      <div className="home-grid">
        {cards.map((card) => <article key={card.title} className="home-card"><strong>{card.title}</strong><span>{card.text}</span></article>)}
      </div>
    </section>
  )
}

function getRoleSummary(user: ReturnType<typeof useAuth>['user']) {
  if (isAdminUser(user)) {
    return 'Tienes acceso visual amplio para administrar grupos, personas, unidades y modulos operativos.'
  }

  if (isGrupoResponsable(user)) {
    return 'Tienes acceso visual de responsable de grupo para revisar gestion, personas y unidades asociadas.'
  }

  if (hasUnidadRole(user)) {
    return 'Tienes acceso visual de unidad para revisar personas, unidades y formacion asociada.'
  }

  if (isApoderado(user)) {
    return 'Tienes acceso visual de apoderado para revisar tu informacion y accesos familiares proximamente.'
  }

  return 'Tu sesion esta activa. Los accesos disponibles dependen de tu perfil y permisos del backend.'
}

function getHomeCards(user: ReturnType<typeof useAuth>['user']) {
  if (isAdminUser(user) || isGrupoResponsable(user)) {
    return [
      { title: 'Dashboard', text: 'KPIs y alertas proximamente' },
      { title: 'Grupos', text: 'Gestion de grupos proximamente' },
      { title: 'Personas', text: 'Gestion de miembros proximamente' },
      { title: 'Unidades', text: 'Estructura de unidades proximamente' },
    ]
  }

  if (hasUnidadRole(user)) {
    return [
      { title: 'Dashboard', text: 'Resumen operativo proximamente' },
      { title: 'Personas', text: 'Miembros de unidad proximamente' },
      { title: 'Unidades', text: 'Detalle de unidad proximamente' },
      { title: 'Formacion', text: 'Seguimiento formativo proximamente' },
    ]
  }

  if (isApoderado(user)) {
    return [
      { title: 'Perfil', text: 'Informacion personal proximamente' },
      { title: 'Familia', text: 'Vinculos familiares proximamente' },
      { title: 'Alertas', text: 'Notificaciones proximamente' },
      { title: 'Contacto', text: 'Canales del grupo proximamente' },
    ]
  }

  return [
    { title: 'Inicio', text: 'Vista autenticada disponible' },
    { title: 'Perfil', text: 'Informacion personal si existe una persona asociada' },
    { title: 'Permisos', text: 'Accesos definidos por el backend' },
    { title: 'Proximamente', text: 'Nuevas vistas disponibles segun tu rol' },
  ]
}
