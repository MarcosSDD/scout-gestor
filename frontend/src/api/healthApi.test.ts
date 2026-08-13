import { httpClient } from "./httpClient";
import { getHealth } from "./healthApi";

vi.mock("./httpClient", () => ({
  httpClient: {
    get: vi.fn(),
  },
}));

describe("getHealth", () => {
  it("calls /health/ and returns typed envelope", async () => {
    const envelope = {
      success: true,
      message: "API healthy",
      data: {
        status: "ok" as const,
        version: "v1",
      },
    };

    vi.mocked(httpClient.get).mockResolvedValueOnce({ data: envelope });

    const result = await getHealth();

    expect(httpClient.get).toHaveBeenCalledWith("/health/");
    expect(result).toEqual(envelope);
  });

  it("propagates request errors", async () => {
    const networkError = new Error("Network Error");
    vi.mocked(httpClient.get).mockRejectedValueOnce(networkError);

    await expect(getHealth()).rejects.toThrow("Network Error");
  });
});
