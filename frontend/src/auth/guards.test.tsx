import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider } from "@/auth/AuthContext";
import {
  GuestOnly,
  RequireAuth,
  RequireDashboard,
  RequireOnboarding,
} from "@/auth/guards";
import * as apiClient from "@/services/apiClient";

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

function renderGuards(initialPath: string) {
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={[initialPath]}>
        <Routes>
          <Route element={<GuestOnly />}>
            <Route path="/login" element={<div>Login page</div>} />
          </Route>
          <Route element={<RequireOnboarding />}>
            <Route path="/onboarding" element={<div>Onboarding page</div>} />
          </Route>
          <Route element={<RequireDashboard />}>
            <Route path="/dashboard" element={<div>Dashboard page</div>} />
          </Route>
          <Route element={<RequireAuth />}>
            <Route path="/authed" element={<div>Authed page</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  );
}

describe("route guards", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("blocks unauthenticated users from dashboard", async () => {
    meMock.mockResolvedValue({
      ok: false,
      data: null,
      error: { code: "unauthorized", message: "Login required" },
    });

    renderGuards("/dashboard");

    await waitFor(() => {
      expect(screen.getByText("Login page")).toBeInTheDocument();
    });
  });

  it("sends authenticated incomplete users to onboarding from guest routes", async () => {
    meMock.mockResolvedValue({
      ok: true,
      data: {
        user: { id: 1, email: "a@b.com" },
        onboarding_completed: false,
      },
      error: null,
    });

    renderGuards("/login");

    await waitFor(() => {
      expect(screen.getByText("Onboarding page")).toBeInTheDocument();
    });
  });

  it("sends completed users to dashboard from onboarding", async () => {
    meMock.mockResolvedValue({
      ok: true,
      data: {
        user: { id: 1, email: "a@b.com" },
        onboarding_completed: true,
      },
      error: null,
    });

    renderGuards("/onboarding");

    await waitFor(() => {
      expect(screen.getByText("Dashboard page")).toBeInTheDocument();
    });
  });
});
