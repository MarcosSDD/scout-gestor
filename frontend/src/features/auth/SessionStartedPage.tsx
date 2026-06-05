import { Link } from 'react-router-dom'

import { getCurrentUser } from './authSession'

export function SessionStartedPage() {
  const user = getCurrentUser()

  return (
    <main className="session-page">
      <section className="session-card">
        <p className="eyebrow">Sesion activa</p>
        <h1>Sesion iniciada</h1>
        <p>
          {user
            ? `Ingresaste como ${user.username}. La sesion base esta lista para continuar con /me y logout en la siguiente entrega.`
            : 'La sesion base esta lista para continuar con /me y logout en la siguiente entrega.'}
        </p>
        <Link className="secondary-link" to="/health">Ver estado de API</Link>
      </section>
    </main>
  )
}
