import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import {
  createAdultoUnidadRol,
  createSubgrupo,
  createSubgrupoMiembro,
  createUnidad,
  getAdultoOptions,
  getAdultoUnidadRol,
  getAdultoUnidadRoles,
  getBeneficiarioOptions,
  getGrupoOptions,
  getMembresiaDestinoOptions,
  getSubgrupo,
  getSubgrupoMiembro,
  getSubgrupoMiembros,
  getSubgrupos,
  getUnidadOptions,
  patchAdultoUnidadRol,
  patchSubgrupo,
  patchUnidad,
  reassignSubgrupoMiembro,
  type OptionParams,
} from "../../api/unidadesApi";
import { toApiError } from "../../api/errors";
import { unidadesQueryKeys } from "./unidadesQueryKeys";

const retry = (count: number, error: unknown) => {
  const status = (error as { error?: { status?: number } }).error?.status;
  return status !== 401 && status !== 403 && status !== 404 && count < 2;
};
const safe =
  <T>(request: () => Promise<T>) =>
  async () => {
    try {
      return await request();
    } catch (error) {
      throw toApiError(error);
    }
  };
export const useSubgruposQuery = (params: {
  unidad_id?: number;
  page?: number;
}) =>
  useQuery({
    queryKey: unidadesQueryKeys.subgrupos(params),
    placeholderData: keepPreviousData,
    queryFn: safe(() => getSubgrupos(params)),
  });
export const useSubgrupoQuery = (id: number) =>
  useQuery({
    queryKey: unidadesQueryKeys.subgrupo(id),
    enabled: id > 0,
    retry,
    queryFn: safe(() => getSubgrupo(id)),
  });
export const useMiembrosQuery = (params: {
  subgrupo_id?: number;
  beneficiario_id?: number;
  page?: number;
}) =>
  useQuery({
    queryKey: unidadesQueryKeys.miembros(params),
    placeholderData: keepPreviousData,
    queryFn: safe(() => getSubgrupoMiembros(params)),
  });
export const useMiembroQuery = (id: number) =>
  useQuery({
    queryKey: unidadesQueryKeys.miembro(id),
    enabled: id > 0,
    retry,
    queryFn: safe(() => getSubgrupoMiembro(id)),
  });
export const useAdultoRolesQuery = (params: {
  unidad_id?: number;
  page?: number;
}) =>
  useQuery({
    queryKey: unidadesQueryKeys.adultos(params),
    placeholderData: keepPreviousData,
    queryFn: safe(() => getAdultoUnidadRoles(params)),
  });
export const useAdultoRolQuery = (id: number) =>
  useQuery({
    queryKey: unidadesQueryKeys.adulto(id),
    enabled: id > 0,
    retry,
    queryFn: safe(() => getAdultoUnidadRol(id)),
  });
export function useOptionQuery(
  kind: "grupos" | "beneficiarios" | "adultos" | "destinos",
  params: OptionParams,
) {
  const request = {
    grupos: getGrupoOptions,
    beneficiarios: getBeneficiarioOptions,
    adultos: getAdultoOptions,
    destinos: getMembresiaDestinoOptions,
  }[kind];
  return useQuery({
    queryKey: unidadesQueryKeys.options(kind, params),
    enabled:
      kind === "grupos" ||
      Boolean(params.unidad_id || params.miembro_id || params.subgrupo_id),
    placeholderData: keepPreviousData,
    queryFn: safe(() => request(params)),
  });
}
export function useUnidadOptionsQuery(ramaId?: number) {
  const params = ramaId ? { rama_id: ramaId } : {};
  return useQuery({
    queryKey: unidadesQueryKeys.options("unidades", params),
    enabled: Boolean(ramaId),
    queryFn: safe(() => getUnidadOptions({ rama_id: ramaId! })),
  });
}

// Commands deliberately invalidate whole domain prefixes: a move can affect both source and destination.
export function useUnidadCommand() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      values,
    }: {
      id?: number;
      values: Parameters<typeof createUnidad>[0];
    }) => {
      if (!id) return createUnidad(values);
      const editable = Object.fromEntries(
        Object.entries(values).filter(
          ([key]) => key !== "grupo" && key !== "rama",
        ),
      );
      return patchUnidad(id, editable);
    },
    onSuccess: () => invalidate(client),
  });
}
export function useSubgrupoCommand() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      values,
    }: {
      id?: number;
      values: Parameters<typeof createSubgrupo>[0];
    }) =>
      id
        ? patchSubgrupo(id, {
            nombre: values.nombre,
            lider_juvenil: values.lider_juvenil,
          })
        : createSubgrupo(values),
    onSuccess: () => invalidate(client),
  });
}
export function useMiembroCommand() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      values,
    }: {
      id?: number;
      values: { subgrupo: number; beneficiario?: number };
    }) =>
      id
        ? reassignSubgrupoMiembro(id, values.subgrupo)
        : createSubgrupoMiembro({
            subgrupo: values.subgrupo,
            beneficiario: values.beneficiario!,
          }),
    onSuccess: () => invalidate(client),
  });
}
export function useAdultoRolCommand() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      values,
    }: {
      id?: number;
      values: { unidad: number; adulto: number; rol: string };
    }) =>
      id ? patchAdultoUnidadRol(id, values.rol) : createAdultoUnidadRol(values),
    onSuccess: () => invalidate(client),
  });
}
function invalidate(client: ReturnType<typeof useQueryClient>) {
  return Promise.all([
    client.invalidateQueries({ queryKey: unidadesQueryKeys.all }),
    client.invalidateQueries({ queryKey: ["personas"] }),
    client.invalidateQueries({ queryKey: ["grupos"] }),
    client.invalidateQueries({ queryKey: ["dashboard"] }),
  ]);
}
