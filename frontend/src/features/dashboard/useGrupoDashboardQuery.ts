import { useQuery } from '@tanstack/react-query'

import { getGrupoDashboard } from '../../api/dashboardApi'
import { toApiError } from '../../api/errors'

export function useGrupoDashboardQuery(grupoId: number | null) {
  return useQuery({
    queryKey: ['dashboard', 'grupo', grupoId],
    enabled: grupoId !== null,
    queryFn: async () => {
      if (grupoId === null) {
        throw new Error('grupoId is required')
      }

      try {
        return await getGrupoDashboard(grupoId)
      } catch (error) {
        throw toApiError(error)
      }
    },
  })
}
