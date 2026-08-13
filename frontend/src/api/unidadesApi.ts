import { httpClient } from "./httpClient";
import type { ApiSuccess, DetailMeta, PaginatedMeta } from "./types";

export type UnidadListItem = {
  id: number;
  grupo: number;
  grupo_nombre: string;
  rama: number;
  rama_nombre: string;
  nombre: string;
  tipo_composicion: string;
  estado: string;
  cupo_maximo: number | null;
};

export type UnidadesQueryParams = {
  page?: number;
  search?: string;
  estado?: string;
  grupo_id?: number;
  rama_id?: number;
};

export type UnidadDetail = UnidadListItem & {
  grupo_nombre?: string;
  rama_nombre?: string;
  tipo_composicion?: string;
  cupo_maximo?: number | null;
};

export type UnidadPayload = {
  grupo: number;
  rama: number;
  nombre: string;
  tipo_composicion: string;
  estado: string;
  cupo_maximo: number | null;
};
export type Subgrupo = {
  id: number;
  nombre: string;
  unidad: number;
  unidad_nombre: string;
  lider_juvenil: number | null;
};
export type SubgrupoPayload = {
  nombre: string;
  unidad: number;
  lider_juvenil?: number | null;
};
export type SubgrupoMiembro = {
  id: number;
  subgrupo: number;
  subgrupo_nombre: string;
  beneficiario: number;
  beneficiario_persona_nombre: string;
};
export type AdultoUnidadRol = {
  id: number;
  unidad: number;
  unidad_nombre: string;
  adulto: number;
  adulto_persona_nombre: string;
  rol: string;
};
export type Opcion = { id: number; nombre: string };
export type OpcionUnidad = Opcion & {
  grupo_nombre: string;
  estado: "ACTIVA" | "INACTIVA";
};
export type OpcionDestinoMembresia = Opcion & {
  unidad: number;
  unidad_nombre: string;
};
export type StructuralPermissions = {
  can_edit?: boolean;
  can_assign_leader?: boolean;
  can_reassign?: boolean;
  can_edit_role?: boolean;
};
export type StructuralDetailMeta = { permissions?: StructuralPermissions };
export type OptionParams = {
  page?: number;
  search?: string;
  unidad_id?: number;
  rama_id?: number;
  miembro_id?: number;
  subgrupo_id?: number;
};
type List<T> = ApiSuccess<T[], PaginatedMeta>;

export async function getUnidades(
  params?: UnidadesQueryParams,
): Promise<ApiSuccess<UnidadListItem[], PaginatedMeta>> {
  const { data } = await httpClient.get<
    ApiSuccess<UnidadListItem[], PaginatedMeta>
  >("/unidades/", { params });
  return data;
}

export async function getUnidad(
  id: number,
): Promise<ApiSuccess<UnidadDetail, DetailMeta>> {
  const { data } = await httpClient.get<ApiSuccess<UnidadDetail, DetailMeta>>(
    `/unidades/${id}/`,
  );
  return data;
}

export async function createUnidad(payload: UnidadPayload) {
  const { data } = await httpClient.post<ApiSuccess<UnidadDetail>>(
    "/unidades/",
    payload,
  );
  return data;
}
export async function patchUnidad(
  id: number,
  payload: Partial<Omit<UnidadPayload, "grupo" | "rama">>,
) {
  const { data } = await httpClient.patch<ApiSuccess<UnidadDetail>>(
    `/unidades/${id}/`,
    payload,
  );
  return data;
}
export async function getSubgrupos(
  params: { unidad_id?: number; page?: number } = {},
): Promise<List<Subgrupo>> {
  const { data } = await httpClient.get<List<Subgrupo>>(
    "/unidades/subgrupos/",
    { params },
  );
  return data;
}
export async function getSubgrupo(
  id: number,
): Promise<ApiSuccess<Subgrupo, StructuralDetailMeta>> {
  const { data } = await httpClient.get<
    ApiSuccess<Subgrupo, StructuralDetailMeta>
  >(`/unidades/subgrupos/${id}/`);
  return data;
}
export async function createSubgrupo(payload: SubgrupoPayload) {
  const { data } = await httpClient.post<ApiSuccess<Subgrupo>>(
    "/unidades/subgrupos/",
    payload,
  );
  return data;
}
export async function patchSubgrupo(
  id: number,
  payload: Pick<SubgrupoPayload, "nombre" | "lider_juvenil">,
) {
  const { data } = await httpClient.patch<ApiSuccess<Subgrupo>>(
    `/unidades/subgrupos/${id}/`,
    payload,
  );
  return data;
}
export async function getSubgrupoMiembros(
  params: {
    subgrupo_id?: number;
    beneficiario_id?: number;
    page?: number;
  } = {},
): Promise<List<SubgrupoMiembro>> {
  const { data } = await httpClient.get<List<SubgrupoMiembro>>(
    "/unidades/subgrupos-miembros/",
    { params },
  );
  return data;
}
export async function getSubgrupoMiembro(
  id: number,
): Promise<ApiSuccess<SubgrupoMiembro, StructuralDetailMeta>> {
  const { data } = await httpClient.get<
    ApiSuccess<SubgrupoMiembro, StructuralDetailMeta>
  >(`/unidades/subgrupos-miembros/${id}/`);
  return data;
}
export async function createSubgrupoMiembro(payload: {
  subgrupo: number;
  beneficiario: number;
}) {
  const { data } = await httpClient.post<ApiSuccess<SubgrupoMiembro>>(
    "/unidades/subgrupos-miembros/",
    payload,
  );
  return data;
}
export async function reassignSubgrupoMiembro(id: number, subgrupo: number) {
  const { data } = await httpClient.patch<ApiSuccess<SubgrupoMiembro>>(
    `/unidades/subgrupos-miembros/${id}/reasignacion/`,
    { subgrupo },
  );
  return data;
}
export async function getAdultoUnidadRoles(
  params: { unidad_id?: number; page?: number } = {},
): Promise<List<AdultoUnidadRol>> {
  const { data } = await httpClient.get<List<AdultoUnidadRol>>(
    "/unidades/adultos-roles/",
    { params },
  );
  return data;
}
export async function getAdultoUnidadRol(
  id: number,
): Promise<ApiSuccess<AdultoUnidadRol, StructuralDetailMeta>> {
  const { data } = await httpClient.get<
    ApiSuccess<AdultoUnidadRol, StructuralDetailMeta>
  >(`/unidades/adultos-roles/${id}/`);
  return data;
}
export async function createAdultoUnidadRol(payload: {
  unidad: number;
  adulto: number;
  rol: string;
}) {
  const { data } = await httpClient.post<ApiSuccess<AdultoUnidadRol>>(
    "/unidades/adultos-roles/",
    payload,
  );
  return data;
}
export async function patchAdultoUnidadRol(id: number, rol: string) {
  const { data } = await httpClient.patch<ApiSuccess<AdultoUnidadRol>>(
    `/unidades/adultos-roles/${id}/`,
    { rol },
  );
  return data;
}
async function options<T extends Opcion>(
  path: string,
  params: OptionParams,
): Promise<List<T>> {
  const { data } = await httpClient.get<List<T>>(path, { params });
  return data;
}
export const getGrupoOptions = (params: OptionParams = {}) =>
  options("/unidades/opciones/grupos/", params);
export const getUnidadOptions = (params: Pick<OptionParams, "rama_id">) =>
  options<OpcionUnidad>("/unidades/opciones/unidades/", params);
export const getBeneficiarioOptions = (params: OptionParams) =>
  options("/unidades/opciones/beneficiarios/", params);
export const getAdultoOptions = (params: OptionParams) =>
  options("/unidades/opciones/adultos/", params);
export const getMembresiaDestinoOptions = (params: OptionParams) =>
  options<OpcionDestinoMembresia>(
    "/unidades/opciones/destinos-membresia/",
    params,
  );
