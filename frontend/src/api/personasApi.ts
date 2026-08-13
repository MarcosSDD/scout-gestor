import { httpClient } from "./httpClient";
import { downloadPrivateFile } from "./privateFileApi";
import type { ApiSuccess, DetailMeta, PaginatedMeta } from "./types";

type ListQueryParams = { page?: number; search?: string; estado?: string };

export type PersonaListItem = {
  id: number;
  nombre_completo: string;
  estado: string;
};
export type AdultoListItem = {
  id: number;
  persona: number;
  persona_nombre: string;
  persona_estado: string;
  rol_principal: string;
  /** Optional while API deployments transition to the display contract. */
  rol_principal_display?: string;
  certificado_vigencia_hasta: string;
  certificado_vigente: boolean;
};
export type BeneficiarioListItem = {
  id: number;
  persona: number;
  persona_nombre: string;
  persona_estado: string;
  rama_actual: number | null;
  rama_nombre: string | null;
  unidad: number | null;
  unidad_nombre: string | null;
  grupo: number | null;
  grupo_nombre: string | null;
  fecha_ingreso: string;
};
export type ApoderadoListItem = {
  id: number;
  persona: number;
  persona_nombre: string;
  persona_estado: string;
  es_miembro_comite: boolean;
  rol_comite: string;
};

/** Detail contracts intentionally leave sensitive fields optional: their presence is actor-scoped. */
export type PersonaDetail = {
  id: number;
  nombres?: string;
  apellidos?: string;
  estado?: string;
  rut?: string;
  fecha_nacimiento?: string;
  sexo?: string;
  direccion?: string;
  telefono?: string;
  email?: string;
  foto_disponible?: boolean;
  updated_at?: string;
};
export type AdultoDetail = {
  id: number;
  persona: PersonaDetail;
  rol_principal?: string;
  certificado_vigencia_hasta?: string;
  certificado_vigente?: boolean;
  certificado_disponible?: boolean;
};
export type BeneficiarioDetail = {
  id: number;
  persona: PersonaDetail;
  rama_actual?: number | null;
  rama_nombre?: string | null;
  unidad?: number | null;
  unidad_nombre?: string | null;
  grupo_nombre?: string | null;
  fecha_ingreso?: string;
  registros_progresion_recientes?: unknown[];
};
export type AreaDesarrollo = {
  id: number;
  codigo: string;
  nombre: string;
  definicion: string;
  personaje_simbolo: string;
  lema: string;
};
export type RegistroProgresion = {
  id: number;
  beneficiario: number;
  fecha: string;
  tipo: "INICIO_CICLO" | "DURANTE_CICLO" | "FINAL_CICLO";
  texto: string;
  areas: AreaDesarrollo[];
};
export type PersonaPatch = Partial<
  Omit<PersonaDetail, "id" | "foto_disponible">
> & { foto?: File };
export type BeneficiarioPatch = { fecha_ingreso?: string };
export type BeneficiarioAsignacion = { unidad: number; rama_actual?: number };
export type CertificadoPatch = {
  certificado_vigencia_hasta?: string;
  certificado_inhabilidades?: File;
};
export type ProgresionPayload = {
  beneficiario: number;
  fecha: string;
  tipo: RegistroProgresion["tipo"];
  texto: string;
  areas: number[];
};
export type ApoderadoDetail = {
  id: number;
  persona: PersonaDetail;
  es_miembro_comite?: boolean;
  rol_comite?: string;
};

export type PersonasQueryParams = ListQueryParams;
export type AdultosQueryParams = ListQueryParams & {
  rol_principal?: string;
  certificado_vigente?: string;
  unidad_id?: number;
  grupo_id?: number;
};
export type BeneficiariosQueryParams = ListQueryParams & {
  unidad_id?: number;
  rama_id?: number;
  grupo_id?: number;
};
export type ApoderadosQueryParams = ListQueryParams & {
  es_miembro_comite?: string;
  beneficiario_id?: number;
  unidad_id?: number;
  grupo_id?: number;
};

type ListResponse<T> = ApiSuccess<T[], PaginatedMeta>;

async function getList<T>(
  path: string,
  params?: object,
): Promise<ListResponse<T>> {
  const { data } = await httpClient.get<ListResponse<T>>(path, { params });
  return data;
}

export const getPersonas = (params?: PersonasQueryParams) =>
  getList<PersonaListItem>("/personas/", params);
export const getAdultos = (params?: AdultosQueryParams) =>
  getList<AdultoListItem>("/personas/adultos/", params);
export const getBeneficiarios = (params?: BeneficiariosQueryParams) =>
  getList<BeneficiarioListItem>("/personas/beneficiarios/", params);
export const getApoderados = (params?: ApoderadosQueryParams) =>
  getList<ApoderadoListItem>("/personas/apoderados/", params);

async function getDetail<T>(path: string): Promise<ApiSuccess<T, DetailMeta>> {
  const { data } = await httpClient.get<ApiSuccess<T, DetailMeta>>(path);
  return data;
}

export const getPersona = (id: number) =>
  getDetail<PersonaDetail>(`/personas/${id}/`);
export const getAdulto = (id: number) =>
  getDetail<AdultoDetail>(`/personas/adultos/${id}/`);
export const getBeneficiario = (id: number) =>
  getDetail<BeneficiarioDetail>(`/personas/beneficiarios/${id}/`);
export const getApoderado = (id: number) =>
  getDetail<ApoderadoDetail>(`/personas/apoderados/${id}/`);

function asFormData(values: Record<string, unknown>) {
  const form = new FormData();
  Object.entries(values).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "")
      form.append(key, value instanceof File ? value : String(value));
  });
  return form;
}
async function patch<T>(path: string, payload: unknown, multipart = false) {
  const { data } = await httpClient.patch<ApiSuccess<T, DetailMeta>>(
    path,
    multipart ? asFormData(payload as Record<string, unknown>) : payload,
  );
  return data;
}
export const patchPersona = (id: number, payload: PersonaPatch) =>
  patch<PersonaDetail>(
    `/personas/${id}/`,
    payload,
    payload.foto instanceof File,
  );
export const patchBeneficiario = (id: number, payload: BeneficiarioPatch) =>
  patch<BeneficiarioDetail>(`/personas/beneficiarios/${id}/`, payload);
export const patchBeneficiarioAsignacion = (
  id: number,
  payload: BeneficiarioAsignacion,
) =>
  patch<BeneficiarioDetail>(
    `/personas/beneficiarios/${id}/asignacion/`,
    payload,
  );
export const downloadPrivateCertificate = (id: number) =>
  downloadPrivateFile(`/personas/adultos/${id}/certificado/`);
export const patchCertificado = (id: number, payload: CertificadoPatch) =>
  patch<AdultoDetail>(
    `/personas/adultos/${id}/certificado/`,
    payload,
    payload.certificado_inhabilidades instanceof File,
  );
export async function getAreasDesarrollo() {
  const { data } = await httpClient.get<ApiSuccess<AreaDesarrollo[]>>(
    "/personas/areas-desarrollo/",
  );
  return data;
}
export async function getProgresiones(params: { beneficiario?: number } = {}) {
  return getList<RegistroProgresion>("/personas/progresiones/", params);
}
export const getProgresion = (id: number) =>
  getDetail<RegistroProgresion>(`/personas/progresiones/${id}/`);
export async function createProgresion(payload: ProgresionPayload) {
  const { data } = await httpClient.post<ApiSuccess<RegistroProgresion>>(
    "/personas/progresiones/",
    payload,
  );
  return data;
}
export const patchProgresion = (
  id: number,
  payload: Partial<ProgresionPayload>,
) => patch<RegistroProgresion>(`/personas/progresiones/${id}/`, payload);
