import { useQuery } from '@tanstack/react-query'

import { toApiError } from '../../api/errors'
import { getGrupo, getGrupoEstructura, getGrupos, type GruposQueryParams } from '../../api/gruposApi'

export function useGruposQuery(params: GruposQueryParams) {
  return useQuery({
    queryKey: ['grupos', 'list', params],
    queryFn: async () => {
      try {
        return await getGrupos(params)
      } catch (error) {
        throw toApiError(error)
      }
    },
  })
}

export function useGrupoQuery(grupoId: number | null) {
  return useQuery({
    queryKey: ['grupos', 'detail', grupoId],
    enabled: grupoId !== null,
    queryFn: async () => {
      if (grupoId === null) throw new Error('grupoId is required')
      try {
        return await getGrupo(grupoId)
      } catch (error) {
        throw toApiError(error)
      }
    },
  })
}

export function useGrupoEstructuraQuery(grupoId: number | null) {
  return useQuery({
    queryKey: ['grupos', 'structure', grupoId],
    enabled: grupoId !== null,
    queryFn: async () => {
      if (grupoId === null) throw new Error('grupoId is required')
      try {
        return await getGrupoEstructura(grupoId)
      } catch (error) {
        throw toApiError(error)
      }
    },
  })
}
