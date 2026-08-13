import { useMemo, useState } from "react";

import type { ApiError } from "../../api/types";
import { BirthdayAlerts } from "./BirthdayAlerts";
import { DashboardErrorState } from "./DashboardErrorState";
import { KpiCard } from "./KpiCard";
import { useAccessibleGruposQuery } from "./useAccessibleGruposQuery";
import { useGrupoDashboardQuery } from "./useGrupoDashboardQuery";

export function DashboardPage() {
  const [manualGrupoId, setManualGrupoId] = useState<number | null>(null);
  const gruposQuery = useAccessibleGruposQuery();
  const grupos = useMemo(
    () => gruposQuery.data?.data ?? [],
    [gruposQuery.data],
  );
  const selectedGrupoId = useMemo(() => {
    if (grupos.length === 0) {
      return null;
    }

    const manualGrupoExists = grupos.some(
      (grupo) => grupo.id === manualGrupoId,
    );
    return manualGrupoExists ? manualGrupoId : grupos[0].id;
  }, [grupos, manualGrupoId]);

  const dashboardQuery = useGrupoDashboardQuery(selectedGrupoId);
  const dashboard = dashboardQuery.data?.data;

  if (gruposQuery.isLoading) {
    return <DashboardLoadingState message="Cargando grupos accesibles..." />;
  }

  if (gruposQuery.isError) {
    return (
      <DashboardErrorState
        error={gruposQuery.error as unknown as ApiError}
        onRetry={() => void gruposQuery.refetch()}
      />
    );
  }

  if (grupos.length === 0) {
    return (
      <article className="home-card dashboard-state-card">
        <p className="shell-panel-caption">Dashboard</p>
        <h1>Sin grupos accesibles</h1>
        <p>
          No hay grupos disponibles para tu perfil. Si necesitas acceso,
          solicita revision de permisos al responsable del sistema.
        </p>
      </article>
    );
  }

  if (dashboardQuery.isError) {
    return (
      <DashboardErrorState
        error={dashboardQuery.error as unknown as ApiError}
        onRetry={() => void dashboardQuery.refetch()}
      />
    );
  }

  if (dashboardQuery.isLoading || !dashboard) {
    return <DashboardLoadingState message="Cargando KPIs del grupo..." />;
  }

  const { grupo, kpis, alertas } = dashboard;

  return (
    <section
      className="home-feed dashboard-page"
      aria-label="Dashboard inicial"
    >
      <article className="home-card home-card--hero dashboard-hero-card">
        <div>
          <p className="shell-panel-caption">Dashboard</p>
          <h1>{grupo.nombre_oficial}</h1>
          <p>
            Resumen inicial del grupo, KPIs operativos y alertas de cumpleanos
            de los proximos 7 dias.
          </p>
        </div>

        <div className="dashboard-hero-actions">
          <span className="dashboard-status-badge">
            {grupo.estado_vigencia}
          </span>
          {grupos.length > 1 && (
            <label className="dashboard-group-select">
              <span>Grupo</span>
              <select
                value={selectedGrupoId ?? ""}
                onChange={(event) =>
                  setManualGrupoId(Number(event.target.value))
                }
              >
                {grupos.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.nombre_oficial}
                  </option>
                ))}
              </select>
            </label>
          )}
        </div>
      </article>

      <div className="dashboard-kpi-grid">
        <KpiCard
          label="Miembros"
          value={kpis.total_miembros}
          detail="Beneficiarios y adultos activos"
        />
        <KpiCard
          label="Beneficiarios"
          value={kpis.total_beneficiarios_activos}
          detail="Beneficiarios activos del grupo"
          tone="success"
        />
        <KpiCard
          label="Adultos"
          value={kpis.total_adultos_activos}
          detail="Adultos activos con rol en unidad"
        />
        <KpiCard
          label="Formacion adultos"
          value={`${kpis.porcentaje_adultos_con_formacion}%`}
          detail={`${kpis.adultos_con_formacion} adultos con formacion registrada`}
          tone="warning"
          progress={kpis.porcentaje_adultos_con_formacion}
        />
        <KpiCard
          label="Apoderados"
          value={`${kpis.porcentaje_beneficiarios_con_apoderado_activo}%`}
          detail={`${kpis.beneficiarios_con_apoderado_activo} beneficiarios con apoderado activo`}
          tone="success"
          progress={kpis.porcentaje_beneficiarios_con_apoderado_activo}
        />
      </div>

      <BirthdayAlerts alerts={alertas.cumpleanos_semana} />
    </section>
  );
}

function DashboardLoadingState({ message }: { message: string }) {
  return (
    <article className="home-card dashboard-state-card" role="status">
      <p className="shell-panel-caption">Dashboard</p>
      <h1>{message}</h1>
      <p>Estamos preparando la informacion inicial.</p>
    </article>
  );
}
