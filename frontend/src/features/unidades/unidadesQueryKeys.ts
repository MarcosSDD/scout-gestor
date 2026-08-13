export const unidadesQueryKeys = {
  all: ["unidades"] as const,
  lists: () => ["unidades", "list"] as const,
  list: (params: object) => ["unidades", "list", params] as const,
  detail: (id: number) => ["unidades", "detail", id] as const,
  subgrupos: (params: object) => ["unidades", "subgrupos", params] as const,
  subgrupo: (id: number) => ["unidades", "subgrupo", id] as const,
  miembros: (params: object) => ["unidades", "miembros", params] as const,
  miembro: (id: number) => ["unidades", "miembro", id] as const,
  adultos: (params: object) => ["unidades", "adultos", params] as const,
  adulto: (id: number) => ["unidades", "adulto", id] as const,
  options: (kind: string, params: object) =>
    ["unidades", "options", kind, params] as const,
};
