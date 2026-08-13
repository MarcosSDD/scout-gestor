import { fireEvent, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import type { ReactNode } from "react";

import { downloadPrivatePhoto } from "../../api/privateFileApi";
import {
  getAdulto,
  getApoderado,
  getBeneficiario,
  getPersonas,
} from "../../api/personasApi";
import { getRamas } from "../../api/catalogosApi";
import { renderWithQueryClient } from "../../test/renderWithQueryClient";
import { AuthContext } from "../auth/AuthContext";
import {
  AdultoDetailPage,
  ApoderadoDetailPage,
  BeneficiarioDetailPage,
  OwnPersonaPage,
} from "./PersonaDetailPages";
import { AdultosPage, BeneficiariosPage, PersonasPage } from "./PersonasPages";

vi.mock("../../api/personasApi", () => ({
  getPersonas: vi.fn(),
  getAdultos: vi.fn(),
  getBeneficiarios: vi.fn(),
  getApoderados: vi.fn(),
  getAdulto: vi.fn(),
  getBeneficiario: vi.fn(),
  getApoderado: vi.fn(),
  getPersona: vi.fn(),
}));
vi.mock("../../api/catalogosApi", () => ({ getRamas: vi.fn() }));
vi.mock("../unidades/useStructuralQueries", () => ({
  useUnidadOptionsQuery: vi.fn(),
}));
vi.mock("../../api/privateFileApi", () => ({
  downloadPrivatePhoto: vi.fn(),
  revokePrivateFile: vi.fn(),
}));

const permissions = {
  can_edit: true,
  can_download_photo: true,
  can_download_certificate: true,
  can_manage_progression: true,
  can_edit_committee: true,
};
const persona = {
  id: 42,
  nombres: "Ana María",
  apellidos: "Rojas Soto",
  estado: "ACTIVO",
  rut: "11.111.111-1",
  fecha_nacimiento: "1990-02-03",
  sexo: "F",
  direccion: "Calle Scout 10",
  telefono: "+56912345678",
  email: "ana@example.test",
  foto_disponible: true,
};

function detailRoute(route: string, initialEntry: string, page: ReactNode) {
  return (
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path={route} element={page} />
      </Routes>
    </MemoryRouter>
  );
}

describe("PersonasPage", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renders minimal PII and persists filters through the URL query", async () => {
    vi.mocked(getPersonas).mockResolvedValue({
      success: true,
      message: "OK",
      meta: { count: 1, next: null, previous: null },
      data: [{ id: 1, nombre_completo: "Ana Rojas", estado: "ACTIVO" }],
    });
    renderWithQueryClient(
      <MemoryRouter>
        <PersonasPage />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Ana Rojas")).toBeInTheDocument();
    expect(screen.queryByText("11.111.111-1")).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Buscar"), {
      target: { value: "Ana" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Aplicar filtros" }));
    expect(getPersonas).toHaveBeenLastCalledWith({ search: "Ana" });
  });

  it("uses the role display label and sends GUIADORA when filtering guiadoras", async () => {
    const { getAdultos } = await import("../../api/personasApi");
    vi.mocked(getAdultos).mockResolvedValue({
      success: true,
      message: "OK",
      meta: { count: 2, next: null, previous: null },
      data: [
        {
          id: 1,
          persona: 1,
          persona_nombre: "María Scout",
          persona_estado: "ACTIVO",
          rol_principal: "GUIADORA",
          rol_principal_display: "Guiadora de unidad",
          certificado_vigencia_hasta: "2030-01-01",
          certificado_vigente: true,
        },
        {
          id: 2,
          persona: 2,
          persona_nombre: "Elena Legacy",
          persona_estado: "ACTIVO",
          rol_principal: "GUIA",
          certificado_vigencia_hasta: "2030-01-01",
          certificado_vigente: true,
        },
      ],
    });
    renderWithQueryClient(
      <MemoryRouter>
        <AdultosPage />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Guiadora de unidad")).toBeInTheDocument();
    expect(screen.getAllByText("Guiadora")).toHaveLength(2);
    fireEvent.change(screen.getByLabelText("Rol"), {
      target: { value: "GUIADORA" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Aplicar filtros" }));
    expect(getAdultos).toHaveBeenLastCalledWith({ rol_principal: "GUIADORA" });
  });

  it("filters beneficiaries by branch and unit names, preserving initial URL filters until applied", async () => {
    const { useUnidadOptionsQuery } = await import(
      "../unidades/useStructuralQueries"
    );
    const { getBeneficiarios } = await import("../../api/personasApi");
    vi.mocked(getRamas).mockResolvedValue({
      success: true,
      message: "OK",
      data: [
        {
          id: 2,
          nombre: "Tropa",
          edad_minima: 11,
          edad_maxima: 15,
          activa: true,
        },
      ],
    });
    vi.mocked(useUnidadOptionsQuery).mockReturnValue({
      data: {
        data: [
          {
            id: 8,
            nombre: "Pumas",
            grupo_nombre: "Grupo Norte",
            estado: "INACTIVA",
          },
        ],
      },
      isLoading: false,
      isError: false,
    } as never);
    vi.mocked(getBeneficiarios).mockResolvedValue({
      success: true,
      message: "OK",
      data: [],
      meta: { count: 0, next: null, previous: null },
    });
    renderWithQueryClient(
      <MemoryRouter
        initialEntries={["/app/personas/beneficiarios/?rama_id=2&unidad_id=8"]}
      >
        <BeneficiariosPage />
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole("option", { name: "Tropa" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Rama")).toHaveValue("2");
    expect(screen.getByLabelText("Unidad")).toHaveValue("8");
    expect(
      screen.getByRole("option", { name: "Pumas · Grupo Norte · Inactiva" }),
    ).toBeInTheDocument();
    expect(getBeneficiarios).toHaveBeenLastCalledWith(
      expect.objectContaining({ rama_id: 2, unidad_id: 8 }),
    );

    fireEvent.change(screen.getByLabelText("Rama"), { target: { value: "" } });
    expect(screen.getByLabelText("Unidad")).toHaveValue("");
    expect(screen.getByLabelText("Unidad")).toBeDisabled();
    expect(getBeneficiarios).toHaveBeenLastCalledWith(
      expect.objectContaining({ rama_id: 2, unidad_id: 8 }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Aplicar filtros" }));
    await waitFor(() =>
      expect(getBeneficiarios).toHaveBeenLastCalledWith(
        expect.not.objectContaining({
          rama_id: expect.anything(),
          unidad_id: expect.anything(),
        }),
      ),
    );
  });

  it("shows loading, unavailable, and empty unit option labels", async () => {
    const { useUnidadOptionsQuery } = await import(
      "../unidades/useStructuralQueries"
    );
    const { getBeneficiarios } = await import("../../api/personasApi");
    vi.mocked(getRamas).mockResolvedValue({
      success: true,
      message: "OK",
      data: [
        {
          id: 2,
          nombre: "Tropa",
          edad_minima: 11,
          edad_maxima: 15,
          activa: true,
        },
      ],
    });
    vi.mocked(getBeneficiarios).mockResolvedValue({
      success: true,
      message: "OK",
      data: [],
      meta: { count: 0, next: null, previous: null },
    });
    vi.mocked(useUnidadOptionsQuery).mockReturnValue({
      isLoading: true,
      isError: false,
    } as never);
    const view = renderWithQueryClient(
      <MemoryRouter initialEntries={["/app/personas/beneficiarios/?rama_id=2"]}>
        <BeneficiariosPage />
      </MemoryRouter>,
    );
    expect(
      await screen.findByRole("option", { name: "Cargando unidad…" }),
    ).toBeInTheDocument();
    view.unmount();

    vi.mocked(useUnidadOptionsQuery).mockReturnValue({
      isLoading: false,
      isError: true,
    } as never);
    const errorView = renderWithQueryClient(
      <MemoryRouter initialEntries={["/app/personas/beneficiarios/?rama_id=2"]}>
        <BeneficiariosPage />
      </MemoryRouter>,
    );
    expect(
      await screen.findByRole("option", {
        name: "No fue posible cargar unidades.",
      }),
    ).toBeInTheDocument();
    errorView.unmount();

    vi.mocked(useUnidadOptionsQuery).mockReturnValue({
      data: { data: [] },
      isLoading: false,
      isError: false,
    } as never);
    renderWithQueryClient(
      <MemoryRouter initialEntries={["/app/personas/beneficiarios/?rama_id=2"]}>
        <BeneficiariosPage />
      </MemoryRouter>,
    );
    expect(
      await screen.findByRole("option", {
        name: "No hay unidades disponibles.",
      }),
    ).toBeInTheDocument();
  });

  it("renders an adult detail from the nested persona contract and downloads its photo by persona ID", async () => {
    vi.mocked(getAdulto).mockResolvedValue({
      success: true,
      message: "OK",
      data: {
        id: 7,
        persona,
        rol_principal: "GUIA",
        certificado_vigencia_hasta: "2030-01-01",
        certificado_vigente: true,
        certificado_disponible: true,
      },
      meta: { permissions },
    });
    vi.mocked(downloadPrivatePhoto).mockResolvedValue({
      url: "blob:adulto",
      filename: "adulto.jpg",
    });
    renderWithQueryClient(
      detailRoute(
        "/app/personas/adultos/:adultoId",
        "/app/personas/adultos/7",
        <AdultoDetailPage />,
      ),
    );

    expect(
      await screen.findByRole("heading", { name: "Ana María Rojas Soto" }),
    ).toBeInTheDocument();
    expect(screen.getByText("11.111.111-1")).toBeInTheDocument();
    expect(screen.getByText("ana@example.test")).toBeInTheDocument();
    expect(
      await screen.findByAltText("Foto de perfil autorizada"),
    ).toHaveAttribute("src", "blob:adulto");
    expect(downloadPrivatePhoto).toHaveBeenCalledWith(42);
  });

  it("renders a beneficiary detail from the nested persona contract and downloads its photo by persona ID", async () => {
    vi.mocked(getBeneficiario).mockResolvedValue({
      success: true,
      message: "OK",
      data: {
        id: 8,
        persona,
        rama_actual: 2,
        rama_nombre: "Tropa",
        unidad: 9,
        unidad_nombre: "Pumas",
        grupo_nombre: "Grupo Norte",
        fecha_ingreso: "2020-03-01",
        registros_progresion_recientes: [],
      },
      meta: { permissions },
    });
    vi.mocked(downloadPrivatePhoto).mockResolvedValue({
      url: "blob:beneficiario",
      filename: "beneficiario.jpg",
    });
    renderWithQueryClient(
      detailRoute(
        "/app/personas/beneficiarios/:beneficiarioId",
        "/app/personas/beneficiarios/8",
        <BeneficiarioDetailPage />,
      ),
    );

    expect(
      await screen.findByRole("heading", { name: "Ana María Rojas Soto" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Calle Scout 10")).toBeInTheDocument();
    expect(screen.getByText("Tropa")).toBeInTheDocument();
    await screen.findByAltText("Foto de perfil autorizada");
    expect(downloadPrivatePhoto).toHaveBeenCalledWith(42);
  });

  it("renders a guardian detail from the nested persona contract and downloads its photo by persona ID", async () => {
    vi.mocked(getApoderado).mockResolvedValue({
      success: true,
      message: "OK",
      data: { id: 9, persona, es_miembro_comite: true, rol_comite: "TESORERO" },
      meta: { permissions },
    });
    vi.mocked(downloadPrivatePhoto).mockResolvedValue({
      url: "blob:apoderado",
      filename: "apoderado.jpg",
    });
    renderWithQueryClient(
      detailRoute(
        "/app/personas/apoderados/:apoderadoId",
        "/app/personas/apoderados/9",
        <ApoderadoDetailPage />,
      ),
    );

    expect(
      await screen.findByRole("heading", { name: "Ana María Rojas Soto" }),
    ).toBeInTheDocument();
    expect(screen.getByText("+56912345678")).toBeInTheDocument();
    expect(screen.getByText("TESORERO")).toBeInTheDocument();
    await screen.findByAltText("Foto de perfil autorizada");
    expect(downloadPrivatePhoto).toHaveBeenCalledWith(42);
  });

  it("shows an account state instead of a missing-person error when the user has no persona", () => {
    const value = {
      status: "authenticated" as const,
      user: {
        id: 1,
        username: "sin-persona",
        email: "",
        first_name: "",
        last_name: "",
        is_staff: false,
        is_superuser: false,
        persona_id: null,
        responsable_grupo_ids: [],
        unidad_roles: [],
        is_apoderado: false,
      },
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
    };
    renderWithQueryClient(
      <AuthContext value={value}>
        <MemoryRouter>
          <OwnPersonaPage />
        </MemoryRouter>
      </AuthContext>,
    );

    expect(
      screen.getByRole("heading", { name: "Mi perfil" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Tu cuenta no tiene una persona asociada."),
    ).toBeInTheDocument();
    expect(screen.queryByText("Ficha no encontrada")).not.toBeInTheDocument();
  });

  it("announces an unavailable private photo when the authorized download fails", async () => {
    vi.mocked(getAdulto).mockResolvedValue({
      success: true,
      message: "OK",
      data: { id: 7, persona, rol_principal: "GUIA" },
      meta: { permissions },
    });
    vi.mocked(downloadPrivatePhoto).mockRejectedValue(new Error("unavailable"));
    renderWithQueryClient(
      detailRoute(
        "/app/personas/adultos/:adultoId",
        "/app/personas/adultos/7",
        <AdultoDetailPage />,
      ),
    );

    const message = await screen.findByText(
      "La foto no está disponible ahora.",
    );
    expect(message).toHaveAttribute("role", "status");
    expect(message).toHaveAttribute("aria-live", "polite");
    expect(downloadPrivatePhoto).toHaveBeenCalledWith(42);
  });
});
