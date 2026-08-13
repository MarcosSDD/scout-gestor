import { Link, useParams } from "react-router-dom";

import { DetailView } from "../details/DetailView";
import { useUnidadDetailQuery } from "./useUnidadesQuery";
import {
  useAdultoRolQuery,
  useAdultoRolesQuery,
  useMiembroQuery,
  useMiembrosQuery,
  useSubgrupoQuery,
  useSubgruposQuery,
} from "./useStructuralQueries";

export function UnidadDetailPage() {
  const id = Number(useParams().unidadId);
  const query = useUnidadDetailQuery(Number.isInteger(id) && id > 0 ? id : 0);
  const data = query.data?.data;
  const permissions = query.data?.meta?.permissions;
  return (
    <>
      <DetailView
        title={data?.nombre ?? "Unidad"}
        eyebrow="Ficha de unidad"
        backTo="/app/unidades"
        backLabel="unidades"
        items={
          data
            ? [
                { label: "Grupo", value: data.grupo_nombre },
                { label: "Rama", value: data.rama_nombre },
                { label: "Composición", value: data.tipo_composicion },
                { label: "Estado", value: data.estado },
                { label: "Cupo máximo", value: data.cupo_maximo },
              ]
            : []
        }
        isLoading={query.isLoading}
        error={query.error as never}
        onRetry={() => void query.refetch()}
      />
      {data?.id ? (
        <>
          <p className="detail-actions">
            {permissions?.can_edit ? (
              <Link
                className="secondary-link"
                to={`/app/unidades/${data.id}/editar`}
              >
                Editar unidad
              </Link>
            ) : null}
            {permissions?.can_create_subgroup ? (
              <Link
                className="secondary-link"
                to={`/app/unidades/${data.id}/subgrupos/nuevo`}
              >
                Nuevo subgrupo
              </Link>
            ) : null}
            {permissions?.can_manage_adult_assignments ? (
              <Link
                className="secondary-link"
                to={`/app/unidades/${data.id}/adultos/nuevo`}
              >
                Asignar adulto
              </Link>
            ) : null}
          </p>
          <UnitOperations
            unidadId={data.id}
            canManageMemberships={Boolean(permissions?.can_manage_memberships)}
          />
        </>
      ) : null}
    </>
  );
}

function UnitOperations({
  unidadId,
  canManageMemberships,
}: {
  unidadId: number;
  canManageMemberships: boolean;
}) {
  const subgroups = useSubgruposQuery({ unidad_id: unidadId });
  const adults = useAdultoRolesQuery({ unidad_id: unidadId });
  return (
    <section className="home-card" aria-labelledby="unit-operations-title">
      <h2 id="unit-operations-title">Operación de unidad</h2>
      <h3>Subgrupos</h3>
      {subgroups.data?.data.map((subgroup) => (
        <SubgroupOperation
          key={subgroup.id}
          subgroupId={subgroup.id}
          unidadId={unidadId}
          canManageMemberships={canManageMemberships}
        />
      ))}
      <h3>Equipo adulto</h3>
      {adults.data?.data.map((assignment) => (
        <AdultOperation key={assignment.id} assignmentId={assignment.id} />
      ))}
    </section>
  );
}
function SubgroupOperation({
  subgroupId,
  unidadId,
  canManageMemberships,
}: {
  subgroupId: number;
  unidadId: number;
  canManageMemberships: boolean;
}) {
  const subgroup = useSubgrupoQuery(subgroupId);
  const members = useMiembrosQuery({ subgrupo_id: subgroupId });
  return (
    <article>
      <h4>{subgroup.data?.data.nombre ?? "Subgrupo"}</h4>
      {subgroup.data?.meta?.permissions?.can_assign_leader ? (
        <Link to={`/app/unidades/subgrupos/${subgroupId}/editar`}>
          Editar subgrupo
        </Link>
      ) : null}
      {canManageMemberships ? (
        <Link
          to={`/app/unidades/${unidadId}/subgrupos/${subgroupId}/miembros/nuevo`}
        >
          Agregar integrante
        </Link>
      ) : null}
      {members.data?.data.map((member) => (
        <MemberOperation key={member.id} memberId={member.id} />
      ))}
    </article>
  );
}
function MemberOperation({ memberId }: { memberId: number }) {
  const member = useMiembroQuery(memberId);
  return (
    <p>
      {member.data?.data.beneficiario_persona_nombre}
      {member.data?.meta?.permissions?.can_reassign ? (
        <Link to={`/app/unidades/miembros/${memberId}/reasignar`}>
          {" "}
          Reasignar
        </Link>
      ) : null}
    </p>
  );
}
function AdultOperation({ assignmentId }: { assignmentId: number }) {
  const assignment = useAdultoRolQuery(assignmentId);
  return (
    <p>
      {assignment.data?.data.adulto_persona_nombre}
      {assignment.data?.meta?.permissions?.can_edit_role ? (
        <Link to={`/app/unidades/adultos/${assignmentId}/editar`}>
          {" "}
          Editar rol
        </Link>
      ) : null}
    </p>
  );
}
