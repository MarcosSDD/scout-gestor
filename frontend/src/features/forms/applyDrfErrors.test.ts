import { applyDrfErrors } from './applyDrfErrors'

type LoginForm = { username: string; password: string }

describe('applyDrfErrors', () => {
  it('sets errors only for explicit allowed fields and returns all other DRF errors globally', () => {
    const setError = vi.fn()

    const globalErrors = applyDrfErrors<LoginForm>({
      username: ['Este usuario no existe.'],
      non_field_errors: ['No fue posible iniciar sesión.'],
      detail: 'Solicitud inválida.',
      unexpected_field: ['No permitido.'],
      nested: { code: ['Error anidado.'] },
    }, setError, ['username'])

    expect(setError).toHaveBeenCalledTimes(1)
    expect(setError).toHaveBeenCalledWith('username', { type: 'server', message: 'Este usuario no existe.' })
    expect(globalErrors).toEqual(['No fue posible iniciar sesión.', 'Solicitud inválida.', 'No permitido.', 'Error anidado.'])
  })

  it('keeps a scalar error response in the global collection', () => {
    const setError = vi.fn()

    expect(applyDrfErrors<LoginForm>('No fue posible procesar la solicitud.', setError, ['username', 'password'])).toEqual(['No fue posible procesar la solicitud.'])
    expect(setError).not.toHaveBeenCalled()
  })
})
