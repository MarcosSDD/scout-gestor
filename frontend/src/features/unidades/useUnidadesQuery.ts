import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { toApiError } from '../../api/errors'
import { getUnidad, getUnidades, type UnidadesQueryParams } from '../../api/unidadesApi'
import { unidadesQueryKeys } from './unidadesQueryKeys'

export function useUnidadesQuery(params: UnidadesQueryParams) {
  return useQuery({
    queryKey: unidadesQueryKeys.list(params),
    placeholderData: keepPreviousData,
    queryFn: async () => {
      try { return await getUnidades(params) } catch (error) { throw toApiError(error) }
    },
  })
}

export function useUnidadDetailQuery(id: number) {
  return useQuery({
    queryKey: unidadesQueryKeys.detail(id),
    retry: (count, error) => {
      const status = (error as { error?: { status?: number | null } }).error?.status
      return status !== 401 && status !== 403 && status !== 404 && count < 2
    },
    queryFn: async () => { try { return await getUnidad(id) } catch (error) { throw toApiError(error) } },
  })
}
