import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <main className="session-page">
      <section className="session-card error-page-card">
        <p className="eyebrow">Ruta no encontrada</p>
        <h1>404</h1>
        <p>La pagina que buscas no existe o fue movida dentro de SCOUTS-GESTOR.</p>
        <Link className="secondary-link" to="/app">Ir al inicio</Link>
      </section>
    </main>
  )
}
