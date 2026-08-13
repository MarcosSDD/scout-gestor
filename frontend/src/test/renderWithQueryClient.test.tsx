import { screen } from "@testing-library/react";

import { renderWithQueryClient } from "./renderWithQueryClient";

describe("renderWithQueryClient", () => {
  it("renders children with query client wrapper", () => {
    renderWithQueryClient(<div>Wrapped content</div>);

    expect(screen.getByText("Wrapped content")).toBeInTheDocument();
  });
});
