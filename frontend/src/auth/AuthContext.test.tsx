import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider, useAuth } from "@/auth/AuthContext";
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
const loginMock = vi.mocked(apiClient.login);

function AuthProbe() {
  const { status, user, login } = useAuth();

  return (
    <div>
      <p>status:{status}</p>
      <p>user:{user?.email ?? "none"}</p>
      <button
        type="button"
        onClick={() => {
          void login("a@b.com", "secret123");
        }}
      >
        Do login
      </button>
    </div>
  );
}

describe("AuthContext", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("loads unauthenticated state when me fails", async () => {
    meMock.mockResolvedValue({
      ok: false,
      data: null,
      error: { code: "unauthorized", message: "Login required" },
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <AuthProbe />
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("status:unauthenticated")).toBeInTheDocument();
    });
  });

  it("login refreshes session from me", async () => {
    const user = userEvent.setup();
    meMock
      .mockResolvedValueOnce({
        ok: false,
        data: null,
        error: { code: "unauthorized", message: "Login required" },
      })
      .mockResolvedValueOnce({
        ok: true,
        data: {
          user: { id: 1, email: "a@b.com" },
          onboarding_completed: false,
        },
        error: null,
      });
    loginMock.mockResolvedValue({
      ok: true,
      data: { user: { id: 1, email: "a@b.com" } },
      error: null,
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <AuthProbe />
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("status:unauthenticated")).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Do login" }));

    await waitFor(() => {
      expect(screen.getByText("status:authenticated")).toBeInTheDocument();
      expect(screen.getByText("user:a@b.com")).toBeInTheDocument();
    });
  });
});
