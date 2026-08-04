import axios from 'axios'

import type { ApiError } from './types'

const DEFAULT_API_ERROR: ApiError = {
  success: false,
  error: {
    code: 'network_or_unknown_error',
    message: 'No fue posible completar la solicitud',
    details: null,
    status: null,
  },
}

function isApiErrorEnvelope(payload: unknown): payload is ApiError {
  if (!payload || typeof payload !== 'object') {
    return false
  }

  const asRecord = payload as Record<string, unknown>
  const error = asRecord.error as Record<string, unknown> | undefined

  return (
    asRecord.success === false
    && !!error
    && typeof error.code === 'string'
    && typeof error.message === 'string'
    && 'details' in error
  )
}

export function toApiError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const payload = error.response?.data

    if (isApiErrorEnvelope(payload)) {
      return {
        ...payload,
        error: { ...payload.error, status: error.response?.status ?? null },
      }
    }

    return {
      ...DEFAULT_API_ERROR,
      error: {
        ...DEFAULT_API_ERROR.error,
        status: error.response?.status ?? null,
        details: {
          status: error.response?.status ?? null,
          message: error.message,
        },
      },
    }
  }

  return {
    ...DEFAULT_API_ERROR,
    error: {
      ...DEFAULT_API_ERROR.error,
      status: null,
      details: error,
    },
  }
}
