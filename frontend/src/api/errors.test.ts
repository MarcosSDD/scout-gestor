import { getApiErrorKind, toApiError } from './errors'

describe('toApiError', () => {
  it('returns backend envelope when response already matches ApiError', () => {
    const backendError = {
      success: false,
      error: {
        code: 'forbidden',
        message: 'No tiene permisos',
        details: { field: 'grupo' },
      },
    }

    const axiosError = {
      isAxiosError: true,
      response: {
        status: 403,
        data: backendError,
      },
      message: 'Request failed with status code 403',
    }

    expect(toApiError(axiosError)).toEqual({ ...backendError, error: { ...backendError.error, status: 403 } })
  })

  it('normalizes axios network/unknown response errors', () => {
    const axiosError = {
      isAxiosError: true,
      response: undefined,
      message: 'Network Error',
    }

    const normalized = toApiError(axiosError)

    expect(normalized.success).toBe(false)
    expect(normalized.error.code).toBe('network_or_unknown_error')
    expect(normalized.error.message).toBe('No fue posible completar la solicitud')
    expect(normalized.error.details).toEqual({
      status: null,
      message: 'Network Error',
    })
  })

  it('normalizes non-axios errors', () => {
    const normalized = toApiError(new Error('Boom'))

    expect(normalized.success).toBe(false)
    expect(normalized.error.code).toBe('network_or_unknown_error')
    expect(normalized.error.message).toBe('No fue posible completar la solicitud')
  })

  it.each([
    [401, 'not_authenticated', 'unauthorized'],
    [403, 'permission_denied', 'forbidden'],
    [404, 'not_found', 'not-found'],
    [null, 'network_or_unknown_error', 'other'],
  ] as const)('classifies %s responses as %s', (status, code, kind) => {
    expect(getApiErrorKind({ success: false, error: { status, code, message: '', details: null } })).toBe(kind)
  })

  it.each([
    [401, 'unauthorized'],
    [403, 'forbidden'],
    [404, 'not-found'],
  ] as const)('classifies a status nested in details (%s) as %s', (status, kind) => {
    expect(getApiErrorKind({ success: false, error: { status: null, code: 'unknown', message: '', details: { status } } })).toBe(kind)
  })
})
