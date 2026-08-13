import { httpClient } from "./httpClient";
import type { ApiSuccess } from "./types";

export type DashboardBirthdayAlert = {
  persona_id: number;
  tipo: "BENEFICIARIO" | "ADULTO";
  rut: string;
  nombres: string;
  apellidos: string;
  fecha_nacimiento: string;
  cumpleanos: string;
  edad_cumple: number;
  dias_restantes: number;
  unidad?: {
    id: number;
    nombre: string;
  };
};

export type GrupoDashboard = {
  grupo: {
    id: number;
    nombre_oficial: string;
    estado_vigencia: string;
  };
  kpis: {
    total_miembros: number;
    total_beneficiarios_activos: number;
    total_adultos_activos: number;
    adultos_con_formacion: number;
    porcentaje_adultos_con_formacion: number;
    beneficiarios_con_apoderado_activo: number;
    porcentaje_beneficiarios_con_apoderado_activo: number;
  };
  alertas: {
    cumpleanos_semana: DashboardBirthdayAlert[];
  };
};

export type GrupoDashboardResponse = ApiSuccess<GrupoDashboard>;

export async function getGrupoDashboard(
  grupoId: number,
): Promise<GrupoDashboardResponse> {
  const { data } = await httpClient.get<GrupoDashboardResponse>(
    `/dashboard/grupo/${grupoId}/`,
  );
  return data;
}
