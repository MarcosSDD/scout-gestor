import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { LoginForm } from './LoginForm'

describe('LoginForm', () => {
  it('submits email and password', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()

    render(<LoginForm onSubmit={onSubmit} isSubmitting={false} />)

    await user.type(screen.getByLabelText('Correo electrónico'), ' responsable1@scouts.cl ')
    await user.type(screen.getByLabelText('Contraseña'), 'testpass123')
    await user.click(screen.getByRole('button', { name: 'Ingresar' }))

    expect(onSubmit).toHaveBeenCalledWith({ email: 'responsable1@scouts.cl', password: 'testpass123' })
  })

  it('uses an email input with email autocomplete', () => {
    render(<LoginForm onSubmit={vi.fn()} isSubmitting={false} />)

    expect(screen.getByLabelText('Correo electrónico')).toHaveAttribute('type', 'email')
    expect(screen.getByLabelText('Correo electrónico')).toHaveAttribute('autocomplete', 'email')
  })

  it('shows backend error message', () => {
    render(
      <LoginForm
        onSubmit={vi.fn()}
        isSubmitting={false}
        error={{
          success: false,
          error: {
            code: 'authentication_failed',
            message: 'No active account found with the given credentials',
            details: null,
            status: 401,
          },
        }}
      />,
    )

    expect(screen.getByRole('alert')).toHaveTextContent('No active account found with the given credentials')
  })

  it('disables submit while pending', () => {
    render(<LoginForm onSubmit={vi.fn()} isSubmitting />)

    expect(screen.getByRole('button', { name: 'Ingresando...' })).toBeDisabled()
  })

  it('toggles password visibility', async () => {
    const user = userEvent.setup()

    render(<LoginForm onSubmit={vi.fn()} isSubmitting={false} />)

    const passwordInput = screen.getByLabelText('Contraseña')
    expect(passwordInput).toHaveAttribute('type', 'password')

    await user.click(screen.getByRole('button', { name: 'Mostrar contrasena' }))
    expect(passwordInput).toHaveAttribute('type', 'text')

    await user.click(screen.getByRole('button', { name: 'Ocultar contrasena' }))
    expect(passwordInput).toHaveAttribute('type', 'password')
  })

  it('does not present unavailable remember-me or password-reset controls', () => {
    render(<LoginForm onSubmit={vi.fn()} isSubmitting={false} />)

    expect(screen.queryByLabelText(/recordarme/i)).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /olvidaste/i })).not.toBeInTheDocument()
  })
})
