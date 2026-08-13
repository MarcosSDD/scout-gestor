import { fireEvent, screen, waitFor } from "@testing-library/react";

import { getGrupoDashboard } from "../../api/dashboardApi";
import type { GrupoDashboardResponse } from "../../api/dashboardApi";
import { getGrupos } from "../../api/gruposApi";
import type { GruposResponse } from "../../api/gruposApi";
import { renderWithQueryClient } from "../../test/renderWithQueryClient";
import { DashboardPage } from "./DashboardPage";

vi.mock("../../api/gruposApi", () => ({
  getGrupos: vi.fn(),
}));

vi.mock("../../api/dashboardApi", () => ({
  getGrupoDashboard: vi.fn(),
}));

const gruposEnvelope: GruposResponse = {
  success: true,
  message: "OK",
  data: [
    {
      id: 7,
      nombre_oficial: "Grupo We Lemu",
      zona: 1,
      zona_nombre: "Zona Centro",
      distrito: 2,
      distrito_nombre: "Distrito Norte",
      tipo_grupo: "PLURICONFESIONAL",
      estado_vigencia: "ACTIVO",
      comuna: "Santiago",
      logo: "",
      minimo_miembros_calculado: 0,
      total_beneficiarios_activos: 10,
      total_adultos_activos: 4,
    },
  ],
};

const dashboardEnvelope: GrupoDashboardResponse = {
  success: true,
  message: "Dashboard del grupo",
  data: {
    grupo: {
      id: 7,
      nombre_oficial: "Grupo We Lemu",
      estado_vigencia: "ACTIVO",
    },
    kpis: {
      total_miembros: 14,
      total_beneficiarios_activos: 10,
      total_adultos_activos: 4,
      adultos_con_formacion: 2,
      porcentaje_adultos_con_formacion: 50,
      beneficiarios_con_apoderado_activo: 8,
      porcentaje_beneficiarios_con_apoderado_activo: 80,
    },
    alertas: {
      cumpleanos_semana: [
        {
          persona_id: 10,
          tipo: "BENEFICIARIO" as const,
          rut: "11.111.111-1",
          nombres: "Sofi",
          apellidos: "Perez",
          fecha_nacimiento: "2012-07-15",
          cumpleanos: "2026-07-15",
          edad_cumple: 14,
          dias_restantes: 2,
          unidad: { id: 3, nombre: "Tropa" },
        },
      ],
    },
  },
};

describe("DashboardPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("loads first accessible group automatically and renders KPIs", async () => {
    vi.mocked(getGrupos).mockResolvedValueOnce(gruposEnvelope);
    vi.mocked(getGrupoDashboard).mockResolvedValueOnce(dashboardEnvelope);

    renderWithQueryClient(<DashboardPage />);

    expect(screen.getByRole("status")).toHaveTextContent(
      "Cargando grupos accesibles",
    );

    await waitFor(() => expect(getGrupoDashboard).toHaveBeenCalledWith(7));
    expect(
      await screen.findByRole("heading", { name: "Grupo We Lemu" }),
    ).toBeInTheDocument();
    expect(screen.getByText("14")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
    expect(screen.getByText("Sofi Perez")).toBeInTheDocument();
    expect(screen.getByText(/cumple 14 anos/i)).toBeInTheDocument();
  });

  it("shows selector and loads selected group when multiple groups are available", async () => {
    vi.mocked(getGrupos).mockResolvedValueOnce({
      ...gruposEnvelope,
      data: [
        ...gruposEnvelope.data,
        { ...gruposEnvelope.data[0], id: 8, nombre_oficial: "Grupo Pehuen" },
      ],
    });
    vi.mocked(getGrupoDashboard)
      .mockResolvedValueOnce(dashboardEnvelope)
      .mockResolvedValueOnce({
        ...dashboardEnvelope,
        data: {
          ...dashboardEnvelope.data,
          grupo: {
            id: 8,
            nombre_oficial: "Grupo Pehuen",
            estado_vigencia: "ACTIVO",
          },
        },
      });

    renderWithQueryClient(<DashboardPage />);

    const select = await screen.findByLabelText("Grupo");
    fireEvent.change(select, { target: { value: "8" } });

    await waitFor(() => expect(getGrupoDashboard).toHaveBeenCalledWith(8));
    expect(
      await screen.findByRole("heading", { name: "Grupo Pehuen" }),
    ).toBeInTheDocument();
  });

  it("shows empty state when no accessible groups exist", async () => {
    vi.mocked(getGrupos).mockResolvedValueOnce({
      success: true,
      message: "OK",
      data: [],
    });

    renderWithQueryClient(<DashboardPage />);

    expect(
      await screen.findByRole("heading", { name: "Sin grupos accesibles" }),
    ).toBeInTheDocument();
    expect(getGrupoDashboard).not.toHaveBeenCalled();
  });

  it("handles backend permission errors from dashboard endpoint", async () => {
    vi.mocked(getGrupos).mockResolvedValueOnce(gruposEnvelope);
    vi.mocked(getGrupoDashboard).mockRejectedValueOnce({
      isAxiosError: true,
      response: {
        data: {
          success: false,
          error: {
            code: "permission_denied",
            message: "No tiene permisos",
            details: null,
          },
        },
      },
    });

    renderWithQueryClient(<DashboardPage />);

    expect(
      await screen.findByRole("heading", { name: "Acceso denegado" }),
    ).toBeInTheDocument();
  });
});
