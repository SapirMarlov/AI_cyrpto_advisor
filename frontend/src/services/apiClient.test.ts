import { afterEach, describe, expect, it, vi } from "vitest";

import { getHealth, login, parseEnvelope, signup } from "./apiClient";

describe("parseEnvelope", () => {
  it("parses a success envelope", () => {
    const result = parseEnvelope<{ status: string }>({
      ok: true,
      data: { status: "healthy" },
      error: null,
    });

    expect(result).toEqual({
      ok: true,
      data: { status: "healthy" },
      error: null,
    });
  });

  it("parses an error envelope", () => {
    const result = parseEnvelope<null>({
      ok: false,
      data: null,
      error: { code: "validation_error", message: "Bad input" },
    });

    expect(result).toEqual({
      ok: false,
      data: null,
      error: { code: "validation_error", message: "Bad input" },
    });
  });

  it("returns malformed_response for invalid payloads", () => {
    expect(parseEnvelope(null)).toEqual({
      ok: false,
      data: null,
      error: { code: "malformed_response", message: "Invalid API response" },
    });
  });
});

describe("apiClient request wrappers", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("getHealth returns parsed success data", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        json: async () => ({
          ok: true,
          data: { status: "healthy" },
          error: null,
        }),
      }),
    );

    const result = await getHealth();

    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.data.status).toBe("healthy");
    }
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/health"),
      expect.objectContaining({ credentials: "include" }),
    );
  });

  it("login returns parsed error envelope", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        json: async () => ({
          ok: false,
          data: null,
          error: { code: "invalid_credentials", message: "Invalid email or password" },
        }),
      }),
    );

    const result = await login("a@b.com", "bad");

    expect(result).toEqual({
      ok: false,
      data: null,
      error: {
        code: "invalid_credentials",
        message: "Invalid email or password",
      },
    });
  });

  it("signup sends JSON body with credentials", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      json: async () => ({
        ok: true,
        data: { user: { id: 1, email: "a@b.com" } },
        error: null,
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await signup("a@b.com", "secret123");

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/auth/signup"),
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        body: JSON.stringify({ email: "a@b.com", password: "secret123" }),
      }),
    );
  });

  it("returns network_error when fetch throws", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));

    const result = await getHealth();

    expect(result).toEqual({
      ok: false,
      data: null,
      error: { code: "network_error", message: "Network request failed" },
    });
  });
});
