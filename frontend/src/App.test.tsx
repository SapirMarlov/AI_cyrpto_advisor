import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";
import { AuthProvider } from "./auth/AuthContext";
import * as apiClient from "./services/apiClient";
import { ThemeProvider } from "./theme/ThemeProvider";

vi.mock("./services/apiClient", async () => {
  const actual = await vi.importActual<typeof apiClient>("./services/apiClient");
  return {
    ...actual,
    me: vi.fn(),
  };
});

const meMock = vi.mocked(apiClient.me);

function renderApp(initialPath = "/login") {
  return render(
    <ThemeProvider>
      <MemoryRouter initialEntries={[initialPath]}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("App shell", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    meMock.mockResolvedValue({
      ok: false,
      data: null,
      error: { code: "unauthorized", message: "Login required" },
    });
  });

  it("renders application heading on login route", async () => {
    renderApp("/login");
    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "AI Crypto Advisor" }),
      ).toBeInTheDocument();
    });
  });
});
