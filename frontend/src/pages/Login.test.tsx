import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider } from "@/auth/AuthContext";
import { LoginPage } from "@/pages/Login";
import * as apiClient from "@/services/apiClient";
import { ThemeProvider } from "@/theme/ThemeProvider";

vi.mock("@/services/apiClient", async () => {
  const actual = await vi.importActual<typeof apiClient>("@/services/apiClient");
  return {
    ...actual,
    me: vi.fn(),
    login: vi.fn(),
    signup: vi.fn(),
    logout: vi.fn(),
  };
});

const meMock = vi.mocked(apiClient.me);
const loginMock = vi.mocked(apiClient.login);

function renderLogin() {
  return render(
    <ThemeProvider>
      <MemoryRouter initialEntries={["/login"]}>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/onboarding" element={<div>Onboarding destination</div>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("LoginPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    meMock.mockResolvedValue({
      ok: false,
      data: null,
      error: { code: "unauthorized", message: "Login required" },
    });
  });

  it("shows server error on failed login", async () => {
    const user = userEvent.setup();
    loginMock.mockResolvedValue({
      ok: false,
      data: null,
      error: { code: "invalid_credentials", message: "Invalid email or password" },
    });

    renderLogin();

    await waitFor(() => {
      expect(screen.getByLabelText("Email")).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText("Email"), "a@b.com");
    await user.type(screen.getByLabelText("Password"), "secret123");
    await user.click(screen.getByRole("button", { name: "Log in" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Invalid email or password",
    );
  });

  it("navigates after successful login", async () => {
    const user = userEvent.setup();
    loginMock.mockResolvedValue({
      ok: true,
      data: { user: { id: 1, email: "a@b.com" } },
      error: null,
    });
    meMock
      .mockResolvedValueOnce({
        ok: false,
        data: null,
        error: { code: "unauthorized", message: "Login required" },
      })
      .mockResolvedValue({
        ok: true,
        data: {
          user: { id: 1, email: "a@b.com" },
          onboarding_completed: false,
        },
        error: null,
      });

    renderLogin();

    await waitFor(() => {
      expect(screen.getByLabelText("Email")).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText("Email"), "a@b.com");
    await user.type(screen.getByLabelText("Password"), "secret123");
    await user.click(screen.getByRole("button", { name: "Log in" }));

    expect(await screen.findByText("Onboarding destination")).toBeInTheDocument();
  });
});
