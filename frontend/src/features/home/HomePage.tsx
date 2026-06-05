import { useAuth } from '../auth/useAuth'

export function HomePage() {
  const { user } = useAuth()
  const displayName = user?.first_name || user?.username || 'scout'

  return (
    <section className="home-feed" aria-label="Inicio We Lemu">
      <article className="home-card home-card--hero">
        <p className="shell-panel-caption">Sesion activa</p>
        <h1>Bienvenido, {displayName}</h1>
        <p>Esta es la base visual de la aplicacion autenticada. Los modulos se conectaran progresivamente en las siguientes entregas.</p>
      </article>

      <div className="home-grid">
        <article className="home-card"><strong>Dashboard</strong><span>KPIs y alertas proximamente</span></article>
        <article className="home-card"><strong>Grupos</strong><span>Acceso visual preparado</span></article>
        <article className="home-card"><strong>Personas</strong><span>Gestion de miembros pendiente</span></article>
        <article className="home-card"><strong>Unidades</strong><span>Estructura responsive lista</span></article>
      </div>
    </section>
  )
}
