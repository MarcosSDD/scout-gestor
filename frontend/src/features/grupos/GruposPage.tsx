import { useMemo, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";

import type { GruposQueryParams } from "../../api/gruposApi";
import { GrupoStateCard } from "./GrupoStateCard";
import { useGruposQuery } from "./useGruposQueries";

const ESTADOS = ["ACTIVO", "OBSERVACION", "SUSPENDIDO", "DISUELTO"];

export function GruposPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const params = useMemo<GruposQueryParams>(() => {
    const page = Number(searchParams.get("page") ?? "1");
    const search = searchParams.get("search")?.trim();
    const estado_vigencia = searchParams.get("estado_vigencia")?.trim();
    return {
      ...(Number.isInteger(page) && page > 1 ? { page } : {}),
      ...(search ? { search } : {}),
      ...(estado_vigencia ? { estado_vigencia } : {}),
    };
  }, [searchParams]);
  const gruposQuery = useGruposQuery(params);
  const grupos = gruposQuery.data?.data ?? [];
  const meta = gruposQuery.data?.meta;

  function updateFilters(form: HTMLFormElement) {
    const formData = new FormData(form);
    const next = new URLSearchParams();
    const search = String(formData.get("search") ?? "").trim();
    const estado = String(formData.get("estado_vigencia") ?? "").trim();
    if (search) next.set("search", search);
    if (estado) next.set("estado_vigencia", estado);
    setSearchParams(next);
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    updateFilters(event.currentTarget);
  }

  function goToPage(page: number) {
    const next = new URLSearchParams(searchParams);
    if (page <= 1) next.delete("page");
    else next.set("page", String(page));
    setSearchParams(next);
  }

  if (gruposQuery.isLoading)
    return (
      <GrupoStateCard
        title="Cargando grupos accesibles..."
        message="Estamos consultando los grupos disponibles para tu perfil."
      />
    );
  if (gruposQuery.isError)
    return (
      <GrupoStateCard
        title="No fue posible cargar los grupos"
        message="Intenta nuevamente en unos segundos."
        error={gruposQuery.error as never}
        onRetry={() => void gruposQuery.refetch()}
      />
    );

  const hasFilters = Boolean(params.search || params.estado_vigencia);
  return (
    <section className="home-feed grupos-page" aria-labelledby="grupos-title">
      <article className="home-card home-card--hero grupos-hero-card">
        <div>
          <p className="shell-panel-caption">Organizacion</p>
          <h1 id="grupos-title">Grupos accesibles</h1>
          <p>
            Consulta la ficha y estructura disponible segun el alcance
            autorizado por el backend.
          </p>
        </div>
        <span className="dashboard-status-badge">
          {meta?.count ?? grupos.length} grupos
        </span>
      </article>

      <form
        className="home-card grupos-filters"
        onSubmit={handleSubmit}
        aria-label="Filtros de grupos"
      >
        <label>
          <span>Buscar grupo</span>
          <input
            name="search"
            type="search"
            defaultValue={params.search ?? ""}
            placeholder="Nombre oficial"
          />
        </label>
        <label>
          <span>Estado de vigencia</span>
          <select
            name="estado_vigencia"
            defaultValue={params.estado_vigencia ?? ""}
          >
            <option value="">Todos los estados</option>
            {ESTADOS.map((estado) => (
              <option key={estado} value={estado}>
                {estado}
              </option>
            ))}
          </select>
        </label>
        <button className="primary-button" type="submit">
          Aplicar filtros
        </button>
      </form>

      {grupos.length === 0 ? (
        <GrupoStateCard
          title={hasFilters ? "Sin resultados" : "Sin grupos accesibles"}
          message={
            hasFilters
              ? "Prueba con otros filtros de busqueda."
              : "No hay grupos disponibles para tu perfil. Solicita revision de permisos si corresponde."
          }
        />
      ) : (
        <div className="grupos-list" aria-live="polite">
          {grupos.map((grupo) => (
            <article className="home-card grupo-list-card" key={grupo.id}>
              <div className="grupo-list-card__heading">
                <div>
                  <p className="shell-panel-caption">
                    {grupo.zona_nombre} · {grupo.distrito_nombre}
                  </p>
                  <h2>{grupo.nombre_oficial}</h2>
                </div>
                <span className="dashboard-status-badge">
                  {grupo.estado_vigencia}
                </span>
              </div>
              <p>
                {grupo.comuna} · {grupo.tipo_grupo}
              </p>
              <dl className="grupo-counts">
                <div>
                  <dt>Beneficiarios</dt>
                  <dd>{grupo.total_beneficiarios_activos}</dd>
                </div>
                <div>
                  <dt>Adultos</dt>
                  <dd>{grupo.total_adultos_activos}</dd>
                </div>
                <div>
                  <dt>Minimo calculado</dt>
                  <dd>{grupo.minimo_miembros_calculado}</dd>
                </div>
              </dl>
              <Link
                className="primary-button grupo-list-card__link"
                to={`/app/grupos/${grupo.id}`}
              >
                Ver grupo
              </Link>
            </article>
          ))}
        </div>
      )}

      {(meta?.previous || meta?.next) && (
        <nav className="grupos-pagination" aria-label="Paginacion de grupos">
          <button
            type="button"
            onClick={() => goToPage((params.page ?? 1) - 1)}
            disabled={!meta.previous}
          >
            Anterior
          </button>
          <span>Pagina {params.page ?? 1}</span>
          <button
            type="button"
            onClick={() => goToPage((params.page ?? 1) + 1)}
            disabled={!meta.next}
          >
            Siguiente
          </button>
        </nav>
      )}
    </section>
  );
}
