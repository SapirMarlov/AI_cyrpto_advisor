import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider } from "@/auth/AuthContext";
import { DashboardPage } from "@/pages/Dashboard";
import * as apiClient from "@/services/apiClient";
import { ThemeProvider } from "@/theme/ThemeProvider";

vi.mock("@/services/apiClient", async () => {
  const actual = await vi.importActual<typeof apiClient>("@/services/apiClient");
  return {
    ...actual,
    me: vi.fn(),
    getDailyDashboard: vi.fn(),
    vote: vi.fn(),
    logout: vi.fn(),
  };
});

const meMock = vi.mocked(apiClient.me);
const getDailyDashboardMock = vi.mocked(apiClient.getDailyDashboard);
const voteMock = vi.mocked(apiClient.vote);

function renderDashboard() {
  return render(
    <ThemeProvider>
      <MemoryRouter>
        <AuthProvider>
          <DashboardPage />
        </AuthProvider>
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("DashboardPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    meMock.mockResolvedValue({
      ok: true,
      data: {
        user: { id: 1, email: "a@b.com" },
        onboarding_completed: true,
      },
      error: null,
    });
  });

  it("renders mixed section success without hiding working panels", async () => {
    getDailyDashboardMock.mockResolvedValue({
      ok: true,
      data: {
        generated_at: "2026-07-10T12:00:00Z",
        sections: {
          news: {
            data: {
              items: [
                {
                  title: "Bitcoin climbs",
                  url: "https://example.com/btc",
                  source: "TestWire",
                  published_at: "2026-07-10",
                },
              ],
            },
            error: null,
            stale: false,
          },
          prices: {
            data: {
              prices: {
                bitcoin: {
                  usd: 65000,
                  change_24h: 1.5,
                  sparkline_7d: [64000, 65000],
                },
              },
            },
            error: null,
            stale: false,
          },
          insight: {
            data: null,
            error: { code: "provider_error", message: "Insight unavailable" },
            stale: false,
          },
          meme: {
            data: {
              title: "To the moon",
              image_url: "https://example.com/meme.png",
              permalink: "https://reddit.com/r/cryptomemes/1",
            },
            error: null,
            stale: false,
          },
        },
      },
      error: null,
    });

    renderDashboard();

    expect(await screen.findByText("Bitcoin climbs")).toBeInTheDocument();
    expect(screen.getByText("bitcoin")).toBeInTheDocument();
    expect(screen.getByText("Insight unavailable")).toBeInTheDocument();
    expect(screen.getByAltText("To the moon")).toBeInTheDocument();
  });
});

describe("VoteButtons via dashboard news", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    meMock.mockResolvedValue({
      ok: true,
      data: {
        user: { id: 1, email: "a@b.com" },
        onboarding_completed: true,
      },
      error: null,
    });
    getDailyDashboardMock.mockResolvedValue({
      ok: true,
      data: {
        generated_at: "2026-07-10T12:00:00Z",
        sections: {
          news: {
            data: {
              items: [
                {
                  title: "Ethereum update",
                  url: "https://example.com/eth",
                  source: "TestWire",
                  published_at: null,
                },
              ],
            },
            error: null,
            stale: false,
          },
          prices: { data: { prices: {} }, error: null, stale: false },
          insight: {
            data: { insight_text: "Stay calm", generated_by: "template" },
            error: null,
            stale: false,
          },
          meme: {
            data: {
              title: "Meme",
              image_url: "https://example.com/m.png",
              permalink: "https://reddit.com/r/x/1",
            },
            error: null,
            stale: false,
          },
        },
      },
      error: null,
    });
  });

  it("submits an up vote for a news item", async () => {
    const user = userEvent.setup();
    voteMock.mockResolvedValue({
      ok: true,
      data: {
        id: 1,
        user_id: 1,
        item_id: "https://example.com/eth",
        item_type: "news",
        vote_type: "up",
        created_at: "2026-07-10",
        updated_at: "2026-07-10",
      },
      error: null,
    });

    renderDashboard();
    expect(await screen.findByText("Ethereum update")).toBeInTheDocument();

    const upButtons = screen.getAllByRole("button", { name: "Thumbs up" });
    await user.click(upButtons[0]);

    await waitFor(() => {
      expect(voteMock).toHaveBeenCalledWith(
        "https://example.com/eth",
        "news",
        "up",
      );
    });
  });

  it("shows vote error and keeps panel visible", async () => {
    const user = userEvent.setup();
    voteMock.mockResolvedValue({
      ok: false,
      data: null,
      error: { code: "validation_error", message: "Vote failed" },
    });

    renderDashboard();
    expect(await screen.findByText("Ethereum update")).toBeInTheDocument();

    const upButtons = screen.getAllByRole("button", { name: "Thumbs up" });
    await user.click(upButtons[0]);

    expect(await screen.findByText("Vote failed")).toBeInTheDocument();
    expect(screen.getByText("Ethereum update")).toBeInTheDocument();
  });
});
