import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { PropsWithChildren } from "react";

import { getHealth } from "../../api/healthApi";
import { useHealthQuery } from "./useHealthQuery";

vi.mock("../../api/healthApi", () => ({
  getHealth: vi.fn(),
}));

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });

  return function Wrapper({ children }: PropsWithChildren) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

describe("useHealthQuery", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns health data on success", async () => {
    vi.mocked(getHealth).mockResolvedValueOnce({
      success: true,
      message: "API healthy",
      data: { status: "ok", version: "v1" },
    });

    const { result } = renderHook(() => useHealthQuery(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.data.status).toBe("ok");
    expect(result.current.data?.data.version).toBe("v1");
  });

  it("normalizes error shape on failure", async () => {
    vi.mocked(getHealth).mockRejectedValueOnce(new Error("Network Error"));

    const { result } = renderHook(() => useHealthQuery(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    const error = result.current.error as {
      error?: {
        code?: string;
      };
    };

    expect(error.error?.code).toBe("network_or_unknown_error");
  });
});
