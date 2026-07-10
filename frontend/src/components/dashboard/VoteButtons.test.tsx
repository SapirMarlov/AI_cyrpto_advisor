import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { VoteButtons } from "@/components/dashboard/VoteButtons";
import * as apiClient from "@/services/apiClient";

vi.mock("@/services/apiClient", async () => {
  const actual = await vi.importActual<typeof apiClient>("@/services/apiClient");
  return {
    ...actual,
    vote: vi.fn(),
  };
});

const voteMock = vi.mocked(apiClient.vote);

describe("VoteButtons", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("calls vote on thumbs up", async () => {
    const user = userEvent.setup();
    voteMock.mockResolvedValue({
      ok: true,
      data: {
        id: 1,
        user_id: 1,
        item_id: "news-1",
        item_type: "news",
        vote_type: "up",
        created_at: "t",
        updated_at: "t",
      },
      error: null,
    });

    render(<VoteButtons itemId="news-1" itemType="news" />);
    await user.click(screen.getByRole("button", { name: "Thumbs up" }));

    await waitFor(() => {
      expect(voteMock).toHaveBeenCalledWith("news-1", "news", "up");
    });
  });

  it("reverts and shows error when vote fails", async () => {
    const user = userEvent.setup();
    voteMock.mockResolvedValue({
      ok: false,
      data: null,
      error: { code: "validation_error", message: "Could not save vote" },
    });

    render(<VoteButtons itemId="news-1" itemType="news" />);
    await user.click(screen.getByRole("button", { name: "Thumbs down" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Could not save vote");
  });
});
