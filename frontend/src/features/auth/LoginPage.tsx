import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'react-toastify'

import type { ApiError } from '../../api/types'
import { LoginForm } from './LoginForm'
import type { LoginCredentials } from './authTypes'
import { useAuth } from './useAuth'

export function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [loginError, setLoginError] = useState<ApiError | null>(null)

  async function handleLogin(credentials: LoginCredentials) {
    setIsSubmitting(true)
    setLoginError(null)

    try {
      const user = await login(credentials)
      toast.success(`Sesion iniciada como ${user.username}`)
      navigate('/app')
    } catch (error) {
      const apiError = error as ApiError
      setLoginError(apiError)
      toast.error(apiError.error.message)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="main-wrap">
      <header className="nav-header" aria-label="Marca">
        <a className="brand-link" href="/login">
          <img className="brand-logo" src="/images/scout.png" alt="Grupo Guia y Scout We Lemu" />
          <span className="brand-text">Grupo Guías y Scouts We Lemu</span>
        </a>
      </header>

      <div className="login-row">
        <section className="login-visual" aria-label="Bienvenida">
          <div className="login-visual__content">
            <p className="auth-hero__badge">Gestion scout</p>
            <h2>Jugamos en equipo, también en la información.</h2>
            <p>Personas, unidades y alertas, We Lemu siempre conectados.</p>
          </div>
        </section>

        <section className="login-panel" aria-label="Inicio de sesion">
          <div className="login-card">
            <div className="login-card__body">
              <h1>INGRESA <br />A TU CUENTA</h1>

              <LoginForm
                onSubmit={handleLogin}
                isSubmitting={isSubmitting}
                error={loginError}
              />
            </div>
          </div>

        </section>
      </div>
    </main>
  )
}
