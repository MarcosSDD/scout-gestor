import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, Link, RouterProvider } from "react-router-dom";
import { useDirtyNavigationGuard } from "./useDirtyNavigationGuard";

function DirtyPage() {
  const dialog = useDirtyNavigationGuard(true);
  return (
    <>
      <h1>Formulario</h1>
      <Link to="/destino">Salir</Link>
      {dialog}
    </>
  );
}

describe("useDirtyNavigationGuard", () => {
  beforeEach(() => {
    HTMLDialogElement.prototype.showModal = function showModal() {
      this.setAttribute("open", "");
    };
    HTMLDialogElement.prototype.close = function close(value = "") {
      this.returnValue = value;
      this.removeAttribute("open");
      this.dispatchEvent(new Event("close"));
    };
  });

  it("blocks navigation, restores the form on cancel and proceeds on discard", async () => {
    const user = userEvent.setup();
    const router = createMemoryRouter(
      [
        { path: "/", element: <DirtyPage /> },
        { path: "/destino", element: <h1>Destino</h1> },
      ],
      { initialEntries: ["/"] },
    );
    render(<RouterProvider router={router} />);
    await user.click(screen.getByRole("link", { name: "Salir" }));
    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("open");
    expect(
      screen.getByRole("button", { name: "Seguir editando" }),
    ).toHaveFocus();
    expect(dialog).toHaveClass("unsaved-changes-dialog");
    expect(screen.getByRole("button", { name: "Seguir editando" })).toHaveClass(
      "unsaved-changes-dialog__button--secondary",
    );
    expect(
      screen.getByRole("button", { name: "Descartar cambios" }),
    ).toHaveClass("unsaved-changes-dialog__button--destructive");
    await user.click(screen.getByRole("button", { name: "Seguir editando" }));
    expect(
      screen.getByRole("heading", { name: "Formulario" }),
    ).toBeInTheDocument();
    await user.click(screen.getByRole("link", { name: "Salir" }));
    await user.click(screen.getByRole("button", { name: "Descartar cambios" }));
    expect(
      await screen.findByRole("heading", { name: "Destino" }),
    ).toBeInTheDocument();
  });
});
