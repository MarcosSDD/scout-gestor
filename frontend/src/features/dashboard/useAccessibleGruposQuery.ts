import { useQuery } from '@tanstack/react-query'

import { toApiError } from '../../api/errors'
import { getGrupos } from '../../api/gruposApi'

export function useAccessibleGruposQuery() {
  return useQuery({
    queryKey: ['grupos', 'accessible'],
    queryFn: async () => {
      try {
        return await getGrupos()
      } catch (error) {
        throw toApiError(error)
      }
    },
  })
}
