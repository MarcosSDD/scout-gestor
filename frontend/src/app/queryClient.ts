import { QueryClient } from '@tanstack/react-query'
import axios from 'axios'

import type { ApiError } from '../api/types'

function isNonRetryableApiError(error: unknown) {
  if (axios.isAxiosError(error)) {
    return [401, 403, 404].includes(error.response?.status ?? 0)
  }

  const apiError = error as ApiError | null
  return apiError?.success === false && ['not_authenticated', 'permission_denied', 'not_found'].includes(apiError.error.code)
}

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error) => {
        if (isNonRetryableApiError(error)) {
          return false
        }
        return failureCount < 2
      },
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
})
