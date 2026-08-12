import { useState, type FormEvent } from 'react'

import type { ApiError } from '../../api/types'
import type { LoginCredentials } from './authTypes'

type LoginFormProps = {
  onSubmit: (credentials: LoginCredentials) => void
  isSubmitting: boolean
  error?: ApiError | null
}

export function LoginForm({ onSubmit, isSubmitting, error }: LoginFormProps) {
  const [isPasswordVisible, setIsPasswordVisible] = useState(false)

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const formData = new FormData(event.currentTarget)

    onSubmit({
      email: String(formData.get('email') ?? '').trim(),
      password: String(formData.get('password') ?? ''),
    })
  }

  return (
    <form className="login-form" onSubmit={handleSubmit}>
      <div className="form-group icon-input">
        <label className="field-label" htmlFor="login-email">Correo electrónico</label>
        <span className="input-icon" aria-hidden="true">@</span>
        <input id="login-email" name="email" type="email" autoComplete="email" required placeholder="Tu E-mail" aria-label="Correo electrónico" />
      </div>

      <div className="form-group icon-input password-field">
        <label className="field-label" htmlFor="login-password">Contraseña</label>
        <span className="input-icon" aria-hidden="true">*</span>
        <input
          id="login-password"
          name="password"
          type={isPasswordVisible ? 'text' : 'password'}
          autoComplete="current-password"
          required
          placeholder="Tu contraseña"
          aria-label="Contraseña"
        />
        <button
          type="button"
          className="password-toggle"
          aria-label={isPasswordVisible ? 'Ocultar contrasena' : 'Mostrar contrasena'}
          aria-pressed={isPasswordVisible}
          onClick={() => setIsPasswordVisible((current) => !current)}
        >
          <svg aria-hidden="true" viewBox="0 0 24 24" focusable="false">
            {isPasswordVisible ? (
              <>
                <path d="M3 3l18 18" />
                <path d="M10.7 10.7a2.8 2.8 0 0 0 3.6 3.6" />
                <path d="M9.9 5.2A9.8 9.8 0 0 1 12 5c5 0 8.3 4.2 9.3 6a12.6 12.6 0 0 1-3 3.7" />
                <path d="M6.2 6.2A12.8 12.8 0 0 0 2.7 11c1 1.8 4.3 6 9.3 6 1.1 0 2.1-.2 3-.6" />
              </>
            ) : (
              <>
                <path d="M2.7 12c1-1.8 4.3-6 9.3-6s8.3 4.2 9.3 6c-1 1.8-4.3 6-9.3 6s-8.3-4.2-9.3-6Z" />
                <path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" />
              </>
            )}
          </svg>
        </button>
      </div>

      {error && <p role="alert" className="form-error">{error.error.message}</p>}

      <button className="primary-button" type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Ingresando...' : 'Ingresar'}
      </button>
    </form>
  )
}
