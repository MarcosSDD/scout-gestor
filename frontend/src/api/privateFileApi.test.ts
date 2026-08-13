import { AxiosError } from "axios";
import { describe, expect, it, vi } from "vitest";
import { httpClient } from "./httpClient";
import { downloadPrivateFile } from "./privateFileApi";

describe("downloadPrivateFile", () => {
  it("convierte un envelope JSON dentro de Blob en ApiError", async () => {
    vi.spyOn(httpClient, "get").mockRejectedValue(
      new AxiosError("falló", undefined, undefined, undefined, {
        status: 403,
        data: new Blob([
          JSON.stringify({
            success: false,
            error: {
              code: "permission_denied",
              message: "Sin permiso",
              details: {},
            },
          }),
        ]),
      } as never),
    );
    await expect(downloadPrivateFile("/privado/")).rejects.toMatchObject({
      error: { code: "permission_denied", status: 403 },
    });
  });
});
