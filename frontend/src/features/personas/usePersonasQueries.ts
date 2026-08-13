import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { toApiError } from "../../api/errors";
import {
  getAdulto,
  getAdultos,
  getApoderado,
  getApoderados,
  getBeneficiario,
  getBeneficiarios,
  getPersona,
  getPersonas,
  type AdultosQueryParams,
  type ApoderadosQueryParams,
  type BeneficiariosQueryParams,
  type PersonasQueryParams,
} from "../../api/personasApi";

function listQuery<T>(key: readonly unknown[], request: () => Promise<T>) {
  return {
    queryKey: key,
    placeholderData: keepPreviousData,
    queryFn: async () => {
      try {
        return await request();
      } catch (error) {
        throw toApiError(error);
      }
    },
  };
}

export const usePersonasQuery = (params: PersonasQueryParams) =>
  useQuery(listQuery(["personas", "list", params], () => getPersonas(params)));
export const useAdultosQuery = (params: AdultosQueryParams) =>
  useQuery(
    listQuery(["personas", "adultos", "list", params], () =>
      getAdultos(params),
    ),
  );
export const useBeneficiariosQuery = (params: BeneficiariosQueryParams) =>
  useQuery(
    listQuery(["personas", "beneficiarios", "list", params], () =>
      getBeneficiarios(params),
    ),
  );
export const useApoderadosQuery = (params: ApoderadosQueryParams) =>
  useQuery(
    listQuery(["personas", "apoderados", "list", params], () =>
      getApoderados(params),
    ),
  );

function detailQuery<T>(key: readonly unknown[], request: () => Promise<T>) {
  return {
    queryKey: key,
    retry: (count: number, error: unknown) => {
      const status = (error as { error?: { status?: number | null } }).error
        ?.status;
      return status !== 401 && status !== 403 && status !== 404 && count < 2;
    },
    queryFn: async () => {
      try {
        return await request();
      } catch (error) {
        throw toApiError(error);
      }
    },
  };
}

export const usePersonaDetailQuery = (id: number) =>
  useQuery(detailQuery(["personas", "detail", id], () => getPersona(id)));
export const useAdultoDetailQuery = (id: number) =>
  useQuery(
    detailQuery(["personas", "adultos", "detail", id], () => getAdulto(id)),
  );
export const useBeneficiarioDetailQuery = (id: number) =>
  useQuery(
    detailQuery(["personas", "beneficiarios", "detail", id], () =>
      getBeneficiario(id),
    ),
  );
export const useApoderadoDetailQuery = (id: number) =>
  useQuery(
    detailQuery(["personas", "apoderados", "detail", id], () =>
      getApoderado(id),
    ),
  );
