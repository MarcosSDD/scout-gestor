import { useMemo } from "react";
import { useSearchParams } from "react-router-dom";

export type ListSearchParams = { page?: number } & Record<
  string,
  string | number | undefined
>;

export function useListSearchParams(filterNames: readonly string[]) {
  const [searchParams, setSearchParams] = useSearchParams();
  const params = useMemo(() => {
    const pageValue = Number(searchParams.get("page") ?? "1");
    const page =
      Number.isInteger(pageValue) && pageValue > 1 ? pageValue : undefined;
    const filters = Object.fromEntries(
      filterNames.flatMap((name) => {
        const value = searchParams.get(name)?.trim();
        return value ? [[name, value]] : [];
      }),
    );
    return { ...filters, ...(page ? { page } : {}) } as ListSearchParams;
  }, [filterNames, searchParams]);

  function applyFilters(values: FormData) {
    const next = new URLSearchParams();
    for (const name of filterNames) {
      const value = String(values.get(name) ?? "").trim();
      if (value) next.set(name, value);
    }
    setSearchParams(next);
  }

  function goToPage(page: number) {
    const next = new URLSearchParams(searchParams);
    if (page <= 1) next.delete("page");
    else next.set("page", String(page));
    setSearchParams(next);
  }

  return { params, applyFilters, goToPage };
}
