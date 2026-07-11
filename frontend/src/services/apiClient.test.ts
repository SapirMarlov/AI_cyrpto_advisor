import { afterEach, describe, expect, it, vi } from "vitest";

import {
  buildApiUrl,
  getHealth,
  login,
  parseEnvelope,
  resolveApiBaseUrl,
  signup,
} from "./apiClient";

describe("resolveApiBaseUrl / buildApiUrl", () => {
  it("defaults undefined to local Flask origin", () => {
    expect(resolveApiBaseUrl(undefined)).toBe("http://127.0.0.1:5000");
  });

  it("keeps empty string for same-origin production calls", () => {
    expect(resolveApiBaseUrl("")).toBe("");
    expect(buildApiUrl("/api/health", "")).toBe("/api/health");
  });

  it("strips a trailing slash from the base", () => {
    expect(resolveApiBaseUrl("http://127.0.0.1:5000/")).toBe(
      "http://127.0.0.1:5000",
    );
    expect(buildApiUrl("/api/health", "http://127.0.0.1:5000")).toBe(
      "http://127.0.0.1:5000/api/health",
    );
  });
});

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

    await signup("a@b.com", "secret123", "Ada");

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/auth/signup"),
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        body: JSON.stringify({ email: "a@b.com", password: "secret123", name: "Ada" }),
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
