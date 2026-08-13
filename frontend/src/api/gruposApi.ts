import { httpClient } from "./httpClient";
import type { ApiSuccess, DetailMeta, PaginatedMeta } from "./types";

export type GrupoListItem = {
  id: number;
  nombre_oficial: string;
  zona: number;
  zona_nombre: string;
  distrito: number;
  distrito_nombre: string;
  tipo_grupo: string;
  estado_vigencia: string;
  comuna: string;
  logo: string;
  minimo_miembros_calculado: number;
  total_beneficiarios_activos: number;
  total_adultos_activos: number;
};

export type GruposResponse = ApiSuccess<GrupoListItem[], PaginatedMeta>;

export type GruposQueryParams = {
  page?: number;
  search?: string;
  estado_vigencia?: string;
  zona_id?: number;
  distrito_id?: number;
};

export type GrupoDetail = {
  id: number;
  nombre_oficial: string;
  zona: number;
  zona_nombre: string;
  distrito: number;
  distrito_nombre: string;
  tipo_grupo: string;
  religion: string;
  estado_vigencia: string;
  direccion: string;
  comuna: string;
  referencia: string;
  latitud: number | null;
  longitud: number | null;
  logo: string;
  minimo_miembros_calculado: number;
  created_at: string;
  updated_at: string;
};

export type GrupoEstructuraAlerta = {
  code: "EDAD_FUERA_DE_RANGO";
  message: string;
};

export type GrupoEstructuraBeneficiario = {
  id: number;
  persona_id: number;
  rut: string;
  nombres: string;
  apellidos: string;
  sexo: string;
  estado: string;
  edad: number;
  alertas: GrupoEstructuraAlerta[];
};

export type GrupoEstructuraAdulto = {
  id: number;
  adulto_id: number;
  rol: string;
  persona: {
    id: number;
    rut: string;
    nombres: string;
    apellidos: string;
    sexo: string;
    estado: string;
  };
};

export type GrupoEstructuraSubgrupo = {
  id: number;
  nombre: string;
  lider_juvenil_id: number | null;
  miembros: Array<{
    id: number;
    beneficiario_id: number;
    beneficiario_nombre: string;
  }>;
};

export type GrupoEstructuraUnidad = {
  id: number;
  nombre: string;
  estado: string;
  tipo_composicion: string;
  es_activa: boolean;
  beneficiarios: GrupoEstructuraBeneficiario[];
  equipo_adulto: GrupoEstructuraAdulto[];
  subgrupos: GrupoEstructuraSubgrupo[];
};

export type GrupoEstructuraRama = {
  id: number;
  nombre: string;
  edad_minima: number;
  edad_maxima: number;
  composicion_permitida: string;
  unidades: GrupoEstructuraUnidad[];
};

export type GrupoEstructura = {
  id: number;
  nombre_oficial: string;
  zona: { id: number; nombre: string };
  distrito: { id: number; nombre: string };
  resumen: {
    total_ramas: number;
    total_unidades: number;
    total_subgrupos: number;
    total_beneficiarios: number;
    total_adultos: number;
    total_alertas_etarias: number;
  };
  ramas: GrupoEstructuraRama[];
};

export type GrupoDetailResponse = ApiSuccess<GrupoDetail, DetailMeta>;
export type GrupoEstructuraResponse = ApiSuccess<GrupoEstructura>;

export async function getGrupos(
  params?: GruposQueryParams,
): Promise<GruposResponse> {
  const { data } = await httpClient.get<GruposResponse>("/grupos/", { params });
  return data;
}

export async function getGrupo(grupoId: number): Promise<GrupoDetailResponse> {
  const { data } = await httpClient.get<GrupoDetailResponse>(
    `/grupos/${grupoId}/`,
  );
  return data;
}

export async function getGrupoEstructura(
  grupoId: number,
): Promise<GrupoEstructuraResponse> {
  const { data } = await httpClient.get<GrupoEstructuraResponse>(
    `/grupos/${grupoId}/estructura/`,
  );
  return data;
}
