import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { PricesPanel } from "@/components/dashboard/PricesPanel";

describe("PricesPanel", () => {
  it("toggles from list view to chart view", async () => {
    const user = userEvent.setup();
    render(
      <PricesPanel
        section={{
          data: {
            prices: {
              bitcoin: {
                usd: 65000,
                change_24h: 1.5,
                sparkline_7d: [64000, 64500, 65000, 65200],
              },
              ethereum: {
                usd: 3200,
                change_24h: -0.4,
                sparkline_7d: [3210, 3190, 3200],
              },
            },
          },
          error: null,
          stale: false,
        }}
      />,
    );

    expect(screen.getByText("bitcoin")).toBeInTheDocument();
    expect(screen.getByText("$65,000.00")).toBeInTheDocument();

    await user.click(screen.getByRole("radio", { name: "Chart view" }));

    expect(screen.getByText("7-day price")).toBeInTheDocument();
    expect(screen.getByLabelText("Select coin")).toBeInTheDocument();
    expect(screen.queryByText("$65,000.00")).toBeInTheDocument();
  });

  it("keeps list view when chart data is missing but still allows chart mode", async () => {
    const user = userEvent.setup();
    render(
      <PricesPanel
        section={{
          data: {
            prices: {
              solana: { usd: 140, change_24h: 2.1, sparkline_7d: null },
            },
          },
          error: null,
          stale: false,
        }}
      />,
    );

    await user.click(screen.getByRole("radio", { name: "Chart view" }));
    expect(
      screen.getByText("Chart data is unavailable for this coin right now."),
    ).toBeInTheDocument();
  });
});
