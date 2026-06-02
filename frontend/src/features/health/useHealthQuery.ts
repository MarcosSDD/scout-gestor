import { useQuery } from '@tanstack/react-query'

import { toApiError } from '../../api/errors'
import { getHealth } from '../../api/healthApi'

export function useHealthQuery() {
  return useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      try {
        return await getHealth()
      } catch (error) {
        throw toApiError(error)
      }
    },
  })
}
