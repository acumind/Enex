import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { api, ApiClientError, setTokenGetter, setTokenRefresher } from "./api-client";

describe("ApiClient", () => {
  const mockFetch = vi.fn();

  beforeEach(() => {
    vi.stubGlobal("fetch", mockFetch);
    setTokenGetter(() => null);
    setTokenRefresher(async () => null);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  function mockResponse(body: unknown, status = 200) {
    return {
      ok: status >= 200 && status < 300,
      status,
      json: vi.fn().mockResolvedValue(body),
      blob: vi.fn().mockResolvedValue(new Blob()),
    };
  }

  it("GET sends request with correct path", async () => {
    mockFetch.mockResolvedValueOnce(mockResponse({ data: 1 }));
    const result = await api.get("/test");
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/v1/test",
      expect.objectContaining({ credentials: "include" }),
    );
    expect(result).toEqual({ data: 1 });
  });

  it("GET appends query params", async () => {
    mockFetch.mockResolvedValueOnce(mockResponse({}));
    await api.get("/test", { q: "hello", limit: "5" });
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/v1/test?q=hello&limit=5",
      expect.anything(),
    );
  });

  it("POST sends JSON body", async () => {
    mockFetch.mockResolvedValueOnce(mockResponse({ ok: true }));
    await api.post("/test", { key: "value" });
    const [, opts] = mockFetch.mock.calls[0];
    expect(opts.method).toBe("POST");
    expect(opts.body).toBe('{"key":"value"}');
  });

  it("PUT sends JSON body", async () => {
    mockFetch.mockResolvedValueOnce(mockResponse({ ok: true }));
    await api.put("/test", { name: "updated" });
    const [, opts] = mockFetch.mock.calls[0];
    expect(opts.method).toBe("PUT");
  });

  it("PATCH sends JSON body", async () => {
    mockFetch.mockResolvedValueOnce(mockResponse({ ok: true }));
    await api.patch("/test", { field: "val" });
    const [, opts] = mockFetch.mock.calls[0];
    expect(opts.method).toBe("PATCH");
  });

  it("DELETE sends request", async () => {
    mockFetch.mockResolvedValueOnce(mockResponse({ ok: true }));
    await api.delete("/test/1");
    const [url, opts] = mockFetch.mock.calls[0];
    expect(url).toBe("/api/v1/test/1");
    expect(opts.method).toBe("DELETE");
  });

  it("injects Authorization header when token is available", async () => {
    setTokenGetter(() => "my-token");
    mockFetch.mockResolvedValueOnce(mockResponse({}));
    await api.get("/protected");
    const [, opts] = mockFetch.mock.calls[0];
    expect(opts.headers.Authorization).toBe("Bearer my-token");
  });

  it("includes credentials: include on all requests", async () => {
    mockFetch.mockResolvedValueOnce(mockResponse({}));
    await api.get("/test");
    const [, opts] = mockFetch.mock.calls[0];
    expect(opts.credentials).toBe("include");
  });

  it("retries once on 401 with token refresh", async () => {
    setTokenGetter(() => "old-token");
    setTokenRefresher(async () => "new-token");

    mockFetch
      .mockResolvedValueOnce(mockResponse({ detail: "Unauthorized" }, 401))
      .mockResolvedValueOnce(mockResponse({ data: "success" }));

    const result = await api.get("/protected");
    expect(result).toEqual({ data: "success" });
    expect(mockFetch).toHaveBeenCalledTimes(2);
  });

  it("does not retry more than once on 401", async () => {
    setTokenGetter(() => "old-token");
    setTokenRefresher(async () => "new-token");

    mockFetch
      .mockResolvedValueOnce(mockResponse({ detail: "Unauthorized" }, 401))
      .mockResolvedValueOnce(mockResponse({ detail: "Still Unauthorized" }, 401));

    await expect(api.get("/protected")).rejects.toThrow(ApiClientError);
    expect(mockFetch).toHaveBeenCalledTimes(2);
  });

  it("throws ApiClientError on non-OK responses", async () => {
    mockFetch.mockResolvedValueOnce(
      mockResponse({ detail: "Not Found" }, 404),
    );
    await expect(api.get("/missing")).rejects.toThrow(ApiClientError);
    await expect(api.get("/missing")).rejects.toThrow();
  });

  it("ApiClientError includes status code", async () => {
    mockFetch.mockResolvedValueOnce(
      mockResponse({ detail: "Bad Request" }, 400),
    );
    try {
      await api.get("/bad");
    } catch (err) {
      expect(err).toBeInstanceOf(ApiClientError);
      expect((err as ApiClientError).status).toBe(400);
      expect((err as ApiClientError).message).toBe("Bad Request");
    }
  });
});
