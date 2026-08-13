import { screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import { CircularActionLink } from "./CircularActionLink";
import { renderWithQueryClient } from "../../test/renderWithQueryClient";

describe("CircularActionLink", () => {
  it("renders an accessible circular link with a tooltip", () => {
    renderWithQueryClient(
      <MemoryRouter>
        <CircularActionLink to="/app/unidades/nueva" label="Nueva unidad" />
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: "Nueva unidad" })).toHaveAttribute(
      "href",
      "/app/unidades/nueva",
    );
    const link = screen.getByRole("link", { name: "Nueva unidad" });
    const tooltip = screen.getByRole("tooltip");
    expect(tooltip).toHaveTextContent("Nueva unidad");
    expect(link).toHaveAttribute("aria-describedby", tooltip.id);
    expect(screen.getByText("+")).toHaveAttribute("aria-hidden", "true");
  });
});
