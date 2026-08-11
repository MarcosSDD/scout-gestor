import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toApiError } from '../../api/errors'
import { getRamas } from '../../api/catalogosApi'
import { getUnidades } from '../../api/unidadesApi'
import { createProgresion, getAreasDesarrollo, getProgresion, getProgresiones, patchBeneficiario, patchBeneficiarioAsignacion, patchCertificado, patchPersona, patchProgresion, type BeneficiarioAsignacion, type BeneficiarioPatch, type CertificadoPatch, type PersonaPatch, type ProgresionPayload } from '../../api/personasApi'
import { personasQueryKeys } from './personasQueryKeys'
import { unidadesQueryKeys } from '../unidades/unidadesQueryKeys'

const request = async <T>(fn: () => Promise<T>) => { try { return await fn() } catch (error) { throw toApiError(error) } }
function invalidarPersona(queryClient: ReturnType<typeof useQueryClient>, personaId?: number, beneficiarioId?: number, adultoId?: number) {
  if (personaId) void queryClient.invalidateQueries({ queryKey: personasQueryKeys.persona(personaId) })
  if (beneficiarioId) void queryClient.invalidateQueries({ queryKey: personasQueryKeys.beneficiario(beneficiarioId) })
  if (adultoId) void queryClient.invalidateQueries({ queryKey: personasQueryKeys.adulto(adultoId) })
  void queryClient.invalidateQueries({ queryKey: ['personas'] })
}
export function usePersonaMutation(personaId: number) { const queryClient = useQueryClient(); return useMutation({ mutationFn: (values: PersonaPatch) => request(() => patchPersona(personaId, values)), onSuccess: () => invalidarPersona(queryClient, personaId) }) }
export function useBeneficiarioMutation(id: number) { const queryClient = useQueryClient(); return useMutation({ mutationFn: (values: BeneficiarioPatch) => request(() => patchBeneficiario(id, values)), onSuccess: () => invalidarPersona(queryClient, undefined, id) }) }
export function useAsignacionMutation(id: number) { const queryClient = useQueryClient(); return useMutation({ mutationFn: (values: BeneficiarioAsignacion) => request(() => patchBeneficiarioAsignacion(id, values)), onSuccess: () => { invalidarPersona(queryClient, undefined, id); void queryClient.invalidateQueries({ queryKey: ['unidades', 'list'] }); void queryClient.invalidateQueries({ queryKey: ['grupos'] }); void queryClient.invalidateQueries({ queryKey: ['dashboard'] }) } }) }
export function useCertificadoMutation(id: number) { const queryClient = useQueryClient(); return useMutation({ mutationFn: (values: CertificadoPatch) => request(() => patchCertificado(id, values)), onSuccess: () => invalidarPersona(queryClient, undefined, undefined, id) }) }
export const useAreasDesarrolloQuery = () => useQuery({ queryKey: ['personas', 'areas-desarrollo'], queryFn: () => request(getAreasDesarrollo) })
export const useRamasQuery = () => useQuery({ queryKey: personasQueryKeys.ramas, queryFn: () => request(() => getRamas({ activa: true })) })
export const useUnidadesSeleccionQuery = (ramaId?: number, page = 1) => useQuery({ queryKey: unidadesQueryKeys.list({ rama_id: ramaId, estado: 'ACTIVA', page }), enabled: Boolean(ramaId), queryFn: () => request(() => getUnidades({ rama_id: ramaId, estado: 'ACTIVA', page })) })
export const useProgresionesQuery = (beneficiario: number) => useQuery({ queryKey: personasQueryKeys.progresiones(beneficiario), queryFn: () => request(() => getProgresiones({ beneficiario })), enabled: beneficiario > 0 })
export const useProgresionQuery = (id: number) => useQuery({ queryKey: personasQueryKeys.progresion(id), queryFn: () => request(() => getProgresion(id)), enabled: id > 0 })
export function useProgresionMutation(beneficiario: number, id?: number) { const queryClient = useQueryClient(); return useMutation({ mutationFn: (values: ProgresionPayload) => request(() => id ? patchProgresion(id, values) : createProgresion(values)), onSuccess: () => { void queryClient.invalidateQueries({ queryKey: personasQueryKeys.progresiones(beneficiario) }); if (id) void queryClient.invalidateQueries({ queryKey: personasQueryKeys.progresion(id) }); invalidarPersona(queryClient, undefined, beneficiario) } }) }
