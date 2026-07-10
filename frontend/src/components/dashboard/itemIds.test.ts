import { describe, expect, it } from "vitest";

import {
  insightItemId,
  memeItemId,
  newsItemId,
} from "@/components/dashboard/itemIds";

describe("itemIds", () => {
  it("derives stable ids", () => {
    expect(newsItemId(" https://example.com/a ")).toBe("https://example.com/a");
    expect(memeItemId("https://reddit.com/r/x/1", "https://img")).toBe(
      "https://reddit.com/r/x/1",
    );
    expect(memeItemId(undefined, "https://img")).toBe("https://img");
    expect(insightItemId("2026-07-10T12:00:00Z")).toBe("insight-2026-07-10");
  });
});
