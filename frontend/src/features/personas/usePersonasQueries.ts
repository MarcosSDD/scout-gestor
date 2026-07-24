import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { toApiError } from '../../api/errors'
import { getAdultos, getApoderados, getBeneficiarios, getPersonas, type AdultosQueryParams, type ApoderadosQueryParams, type BeneficiariosQueryParams, type PersonasQueryParams } from '../../api/personasApi'

function listQuery<T>(key: readonly unknown[], request: () => Promise<T>) {
  return { queryKey: key, placeholderData: keepPreviousData, queryFn: async () => {
    try { return await request() } catch (error) { throw toApiError(error) }
  } }
}

export const usePersonasQuery = (params: PersonasQueryParams) => useQuery(listQuery(['personas', 'list', params], () => getPersonas(params)))
export const useAdultosQuery = (params: AdultosQueryParams) => useQuery(listQuery(['personas', 'adultos', 'list', params], () => getAdultos(params)))
export const useBeneficiariosQuery = (params: BeneficiariosQueryParams) => useQuery(listQuery(['personas', 'beneficiarios', 'list', params], () => getBeneficiarios(params)))
export const useApoderadosQuery = (params: ApoderadosQueryParams) => useQuery(listQuery(['personas', 'apoderados', 'list', params], () => getApoderados(params)))
