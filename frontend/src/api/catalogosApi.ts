import { httpClient } from "./httpClient";
import type { ApiSuccess, PaginatedMeta } from "./types";

export type RamaCatalogo = {
  id: number;
  nombre: string;
  edad_minima: number;
  edad_maxima: number;
  activa: boolean;
};

export async function getRamas(params: { activa?: boolean } = {}) {
  const { data } = await httpClient.get<
    ApiSuccess<RamaCatalogo[], PaginatedMeta>
  >("/catalogos/ramas/", { params });
  return data;
}
