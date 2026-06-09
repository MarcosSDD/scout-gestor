import { useAuth } from '../auth/useAuth'
import { PlaceholderPage } from './PlaceholderPage'

export function ProfilePage() {
  const { user } = useAuth()

  return (
    <PlaceholderPage
      eyebrow="Cuenta"
      title="Mi perfil"
      description="Aqui se mostrara la informacion del usuario autenticado."
    >
      <div className="home-grid">
        <article className="home-card"><strong>Usuario</strong><span>{user?.username ?? 'Sin usuario'}</span></article>
        <article className="home-card"><strong>Correo</strong><span>{user?.email || 'Sin correo registrado'}</span></article>
        <article className="home-card"><strong>Persona</strong><span>{user?.persona_id ? `ID ${user.persona_id}` : 'Sin persona asociada'}</span></article>
        <article className="home-card"><strong>Rol visual</strong><span>{user?.is_staff || user?.is_superuser ? 'Administracion' : 'Usuario autenticado'}</span></article>
      </div>
    </PlaceholderPage>
  )
}
