import { useParams } from 'react-router-dom'

import { DetailView } from '../details/DetailView'
import { useUnidadDetailQuery } from './useUnidadesQuery'

export function UnidadDetailPage() {
  const id = Number(useParams().unidadId); const query = useUnidadDetailQuery(Number.isInteger(id) && id > 0 ? id : 0); const data = query.data?.data
  return <DetailView title={data?.nombre ?? 'Unidad'} eyebrow="Ficha de unidad" backTo="/app/unidades" backLabel="unidades" items={data ? [{ label: 'Grupo', value: data.grupo_nombre }, { label: 'Rama', value: data.rama_nombre }, { label: 'Composición', value: data.tipo_composicion }, { label: 'Estado', value: data.estado }, { label: 'Cupo máximo', value: data.cupo_maximo }] : []} isLoading={query.isLoading} error={query.error as never} onRetry={() => void query.refetch()} />
}
