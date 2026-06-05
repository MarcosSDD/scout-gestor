import { Link } from 'react-router-dom'

export function ForbiddenPage() {
  return (
    <main className="session-page">
      <section className="session-card error-page-card">
        <p className="eyebrow">Acceso denegado</p>
        <h1>403</h1>
        <p>No tienes permisos para acceder a esta seccion. Si crees que deberias verla, contacta a la administracion del grupo.</p>
        <Link className="secondary-link" to="/app">Volver al inicio</Link>
      </section>
    </main>
  )
}
