import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider } from "@/auth/AuthContext";
import { OnboardingPage } from "@/pages/Onboarding";
import * as apiClient from "@/services/apiClient";
import { ThemeProvider } from "@/theme/ThemeProvider";

vi.mock("@/services/apiClient", async () => {
  const actual = await vi.importActual<typeof apiClient>("@/services/apiClient");
  return {
    ...actual,
    me: vi.fn(),
    getQuestions: vi.fn(),
    saveAnswers: vi.fn(),
  };
});

const meMock = vi.mocked(apiClient.me);
const getQuestionsMock = vi.mocked(apiClient.getQuestions);
const saveAnswersMock = vi.mocked(apiClient.saveAnswers);

const sampleQuestions = [
  {
    id: "interested_assets",
    prompt: "What crypto assets are you interested in?",
    type: "multi" as const,
    options: [
      { id: "bitcoin", label: "Bitcoin" },
      { id: "ethereum", label: "Ethereum" },
    ],
  },
  {
    id: "investor_type",
    prompt: "What type of investor are you?",
    type: "single" as const,
    options: [
      { id: "hodler", label: "HODLer" },
      { id: "day_trader", label: "Day Trader" },
    ],
  },
  {
    id: "content_preferences",
    prompt: "What kind of content would you like to see?",
    type: "multi" as const,
    options: [
      { id: "market_news", label: "Market News" },
      { id: "fun", label: "Fun" },
    ],
  },
];

function renderOnboarding() {
  return render(
    <ThemeProvider>
      <MemoryRouter initialEntries={["/onboarding"]}>
        <AuthProvider>
          <Routes>
            <Route path="/onboarding" element={<OnboardingPage />} />
            <Route path="/dashboard" element={<div>Dashboard destination</div>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("OnboardingPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    meMock.mockResolvedValue({
      ok: true,
      data: {
        user: { id: 1, email: "a@b.com" },
        onboarding_completed: false,
      },
      error: null,
    });
  });

  it("loads questions and redirects after successful submit", async () => {
    const user = userEvent.setup();
    getQuestionsMock.mockResolvedValue({
      ok: true,
      data: { questions: sampleQuestions },
      error: null,
    });
    saveAnswersMock.mockResolvedValue({
      ok: true,
      data: {
        onboarding_completed: true,
        preferences: {
          user_id: 1,
          answers: {},
          onboarding_completed: true,
        },
      },
      error: null,
    });

    renderOnboarding();

    expect(await screen.findByText("What crypto assets are you interested in?")).toBeInTheDocument();

    await user.click(screen.getByLabelText("Bitcoin"));
    await user.click(screen.getByLabelText("HODLer"));
    await user.click(screen.getByLabelText("Market News"));
    await user.click(screen.getByRole("button", { name: "Finish onboarding" }));

    expect(await screen.findByText("Dashboard destination")).toBeInTheDocument();
  });

  it("shows server error when save fails", async () => {
    const user = userEvent.setup();
    getQuestionsMock.mockResolvedValue({
      ok: true,
      data: { questions: sampleQuestions },
      error: null,
    });
    saveAnswersMock.mockResolvedValue({
      ok: false,
      data: null,
      error: { code: "validation_error", message: "Invalid answers" },
    });

    renderOnboarding();

    expect(await screen.findByText("What type of investor are you?")).toBeInTheDocument();

    await user.click(screen.getByLabelText("Bitcoin"));
    await user.click(screen.getByLabelText("HODLer"));
    await user.click(screen.getByLabelText("Fun"));
    await user.click(screen.getByRole("button", { name: "Finish onboarding" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Invalid answers");
  });

  it("shows load error when questions fail", async () => {
    getQuestionsMock.mockResolvedValue({
      ok: false,
      data: null,
      error: { code: "unauthorized", message: "Login required" },
    });

    renderOnboarding();

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Login required");
    });
  });
});
