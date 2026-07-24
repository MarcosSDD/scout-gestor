import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { toApiError } from '../../api/errors'
import { getUnidades, type UnidadesQueryParams } from '../../api/unidadesApi'

export function useUnidadesQuery(params: UnidadesQueryParams) {
  return useQuery({
    queryKey: ['unidades', 'list', params],
    placeholderData: keepPreviousData,
    queryFn: async () => {
      try { return await getUnidades(params) } catch (error) { throw toApiError(error) }
    },
  })
}
