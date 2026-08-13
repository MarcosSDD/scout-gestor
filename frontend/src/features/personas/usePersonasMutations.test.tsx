import { QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook } from "@testing-library/react";
import type { PropsWithChildren } from "react";
import { describe, expect, it, vi } from "vitest";
import { patchBeneficiarioAsignacion } from "../../api/personasApi";
import { createTestQueryClient } from "../../test/renderWithQueryClient";
import { useAsignacionMutation } from "./usePersonasMutations";

vi.mock("../../api/personasApi", () => ({
  patchBeneficiarioAsignacion: vi.fn(),
}));

describe("useAsignacionMutation", () => {
  it("invalida datos de persona, grupos y dashboard tras reasignar", async () => {
    vi.mocked(patchBeneficiarioAsignacion).mockResolvedValue({
      success: true,
      message: "OK",
      data: {},
    } as Awaited<ReturnType<typeof patchBeneficiarioAsignacion>>);
    const client = createTestQueryClient();
    const invalidate = vi.spyOn(client, "invalidateQueries");
    function Wrapper({ children }: PropsWithChildren) {
      return (
        <QueryClientProvider client={client}>{children}</QueryClientProvider>
      );
    }
    const { result } = renderHook(() => useAsignacionMutation(8), {
      wrapper: Wrapper,
    });
    await act(async () => {
      await result.current.mutateAsync({ rama_actual: 2, unidad: 4 });
    });
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ["grupos"] });
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ["dashboard"] });
  });
});
