import { Link, useParams } from "react-router-dom";

import type { GrupoEstructuraUnidad } from "../../api/gruposApi";
import { GrupoStateCard } from "./GrupoStateCard";
import { useGrupoEstructuraQuery, useGrupoQuery } from "./useGruposQueries";
import { useAuth } from "../auth/useAuth";
import { isAdminUser, isGrupoResponsable } from "../auth/rbac";

export function GrupoDetailPage() {
  const { user } = useAuth();
  const rawGrupoId = useParams().grupoId;
  const grupoId =
    rawGrupoId && /^\d+$/.test(rawGrupoId) ? Number(rawGrupoId) : null;
  const detailQuery = useGrupoQuery(grupoId);
  const structureQuery = useGrupoEstructuraQuery(grupoId);

  if (grupoId === null)
    return (
      <GrupoStateCard
        title="Grupo no encontrado"
        message="El identificador de grupo no es valido."
      />
    );
  if (detailQuery.isLoading || structureQuery.isLoading)
    return (
      <GrupoStateCard
        title="Cargando grupo..."
        message="Estamos preparando la ficha y estructura visible."
      />
    );
  if (detailQuery.isError)
    return (
      <GrupoStateCard
        title="No fue posible cargar el grupo"
        message="Intenta nuevamente en unos segundos."
        error={detailQuery.error as never}
        onRetry={() => void detailQuery.refetch()}
      />
    );
  if (structureQuery.isError)
    return (
      <GrupoStateCard
        title="No fue posible cargar la estructura"
        message="Intenta nuevamente en unos segundos."
        error={structureQuery.error as never}
        onRetry={() => void structureQuery.refetch()}
      />
    );

  const grupo = detailQuery.data?.data;
  const estructura = structureQuery.data?.data;
  if (!grupo || !estructura)
    return (
      <GrupoStateCard
        title="Cargando grupo..."
        message="Estamos preparando la ficha y estructura visible."
      />
    );

  return (
    <section
      className="home-feed grupos-page"
      aria-labelledby="grupo-detail-title"
    >
      <Link className="grupos-back-link" to="/app/grupos">
        ← Volver a grupos
      </Link>
      <article className="home-card home-card--hero grupos-hero-card">
        <div>
          <p className="shell-panel-caption">
            {grupo.zona_nombre} · {grupo.distrito_nombre}
          </p>
          <h1 id="grupo-detail-title">{grupo.nombre_oficial}</h1>
          <p>Ficha institucional y estructura visible segun tus permisos.</p>
        </div>
        <div>
          <span className="dashboard-status-badge">
            {grupo.estado_vigencia}
          </span>
          {isAdminUser(user) || isGrupoResponsable(user) ? (
            <Link
              className="secondary-link"
              to={`/app/unidades/nueva?grupo_id=${grupo.id}`}
            >
              Nueva unidad
            </Link>
          ) : null}
        </div>
      </article>

      <nav className="grupo-section-nav" aria-label="Secciones del grupo">
        <a href="#detalle">Detalle</a>
        <a href="#estructura">Estructura visible</a>
      </nav>

      <article className="home-card grupo-detail-card" id="detalle">
        <p className="shell-panel-caption">Detalle</p>
        <h2>Ficha del grupo</h2>
        <dl className="grupo-detail-list">
          <div>
            <dt>Tipo de grupo</dt>
            <dd>{grupo.tipo_grupo}</dd>
          </div>
          {grupo.religion && (
            <div>
              <dt>Religion</dt>
              <dd>{grupo.religion}</dd>
            </div>
          )}
          <div>
            <dt>Ubicacion</dt>
            <dd>
              {grupo.direccion}, {grupo.comuna}
            </dd>
          </div>
          {grupo.referencia && (
            <div>
              <dt>Referencia</dt>
              <dd>{grupo.referencia}</dd>
            </div>
          )}
          <div>
            <dt>Minimo de miembros</dt>
            <dd>{grupo.minimo_miembros_calculado}</dd>
          </div>
        </dl>
      </article>

      <section
        className="home-card grupo-structure-card"
        id="estructura"
        aria-labelledby="estructura-title"
      >
        <div className="dashboard-section-heading">
          <div>
            <p className="shell-panel-caption">Estructura</p>
            <h2 id="estructura-title">Estructura visible</h2>
          </div>
          <span className="dashboard-pill">
            {estructura.resumen.total_alertas_etarias} alertas RN-05
          </span>
        </div>
        <p className="grupo-structure-intro">
          Los totales y ramas incluyen solo la informacion autorizada para tu
          perfil.
        </p>
        <dl className="grupo-counts grupo-counts--summary">
          <div>
            <dt>Ramas</dt>
            <dd>{estructura.resumen.total_ramas}</dd>
          </div>
          <div>
            <dt>Unidades</dt>
            <dd>{estructura.resumen.total_unidades}</dd>
          </div>
          <div>
            <dt>Beneficiarios</dt>
            <dd>{estructura.resumen.total_beneficiarios}</dd>
          </div>
          <div>
            <dt>Adultos</dt>
            <dd>{estructura.resumen.total_adultos}</dd>
          </div>
        </dl>
        {estructura.ramas.length === 0 ? (
          <p className="dashboard-empty-text">
            No hay unidades visibles para este grupo.
          </p>
        ) : (
          <div className="grupo-tree">
            {estructura.ramas.map((rama) => (
              <details key={rama.id} open>
                <summary>
                  {rama.nombre}{" "}
                  <span>
                    {rama.edad_minima}–{rama.edad_maxima} anos ·{" "}
                    {rama.unidades.length} unidades
                  </span>
                </summary>
                <p className="grupo-tree__meta">
                  Composicion: {rama.composicion_permitida}
                </p>
                {rama.unidades.map((unidad) => (
                  <UnidadTree key={unidad.id} unidad={unidad} />
                ))}
              </details>
            ))}
          </div>
        )}
      </section>
    </section>
  );
}

function UnidadTree({ unidad }: { unidad: GrupoEstructuraUnidad }) {
  return (
    <details className="grupo-tree__unidad">
      <summary>
        <Link to={`/app/unidades/${unidad.id}`}>{unidad.nombre}</Link>{" "}
        <span>
          {unidad.estado} · {unidad.tipo_composicion}
        </span>
      </summary>
      <div className="grupo-tree__content">
        <section aria-label={`Beneficiarios de ${unidad.nombre}`}>
          <h3>Beneficiarios ({unidad.beneficiarios.length})</h3>
          {unidad.beneficiarios.length === 0 ? (
            <p>Sin beneficiarios registrados.</p>
          ) : (
            <ul className="grupo-person-list">
              {unidad.beneficiarios.map((beneficiario) => (
                <li key={beneficiario.id}>
                  <strong>
                    {beneficiario.nombres} {beneficiario.apellidos}
                  </strong>
                  <span>
                    {beneficiario.edad} anos · {beneficiario.estado}
                  </span>
                  {beneficiario.alertas.map((alerta) => (
                    <p className="grupo-age-alert" key={alerta.code}>
                      <b>Alerta RN-05:</b> {alerta.message}
                    </p>
                  ))}
                </li>
              ))}
            </ul>
          )}
        </section>
        <section aria-label={`Equipo adulto de ${unidad.nombre}`}>
          <h3>Equipo adulto ({unidad.equipo_adulto.length})</h3>
          {unidad.equipo_adulto.length === 0 ? (
            <p>Sin adultos asignados.</p>
          ) : (
            <ul className="grupo-person-list">
              {unidad.equipo_adulto.map((asignacion) => (
                <li key={asignacion.id}>
                  <strong>
                    {asignacion.persona.nombres} {asignacion.persona.apellidos}
                  </strong>
                  <span>
                    {asignacion.rol} · {asignacion.persona.estado}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>
        <section aria-label={`Subgrupos de ${unidad.nombre}`}>
          <h3>Subgrupos ({unidad.subgrupos.length})</h3>
          {unidad.subgrupos.length === 0 ? (
            <p>Sin subgrupos registrados.</p>
          ) : (
            <ul className="grupo-subgroup-list">
              {unidad.subgrupos.map((subgrupo) => (
                <li key={subgrupo.id}>
                  <strong>{subgrupo.nombre}</strong>
                  <span>
                    {subgrupo.miembros.length === 0
                      ? "Sin miembros"
                      : subgrupo.miembros
                          .map((miembro) => miembro.beneficiario_nombre)
                          .join(", ")}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </details>
  );
}
