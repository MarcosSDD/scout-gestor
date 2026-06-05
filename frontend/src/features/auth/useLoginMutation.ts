import { useMutation } from '@tanstack/react-query'

import { login } from '../../api/authApi'
import { toApiError } from '../../api/errors'
import type { ApiError } from '../../api/types'
import { setAuthSession } from './authSession'
import type { LoginCredentials, LoginResponse } from './authTypes'

export function useLoginMutation() {
  return useMutation<LoginResponse, ApiError, LoginCredentials>({
    mutationFn: async (credentials: LoginCredentials) => {
      try {
        return await login(credentials)
      } catch (error) {
        throw toApiError(error)
      }
    },
    onSuccess: (response) => {
      setAuthSession(response.data)
    },
  })
}
