import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock next/server before importing middleware
vi.mock("next/server", () => {
  const next = vi.fn(() => ({ type: "next" }));
  const redirect = vi.fn((url: URL) => ({ type: "redirect", url: url.toString() }));

  return {
    NextResponse: { next, redirect },
  };
});

import { middleware } from "./middleware";
import { NextResponse } from "next/server";

function createRequest(pathname: string, hasCookie = false) {
  return {
    nextUrl: {
      pathname,
    },
    url: `http://localhost:3000${pathname}`,
    cookies: {
      get: vi.fn((name: string) =>
        name === "refresh_token" && hasCookie
          ? { value: "test-token" }
          : undefined,
      ),
    },
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } as any;
}

describe("middleware", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("passes through non-protected paths", () => {
    const result = middleware(createRequest("/"));
    expect(NextResponse.next).toHaveBeenCalled();
    expect(result).toEqual({ type: "next" });
  });

  it("passes through public pages like /about", () => {
    middleware(createRequest("/about"));
    expect(NextResponse.next).toHaveBeenCalled();
    expect(NextResponse.redirect).not.toHaveBeenCalled();
  });

  it("redirects protected paths when no cookie present", () => {
    middleware(createRequest("/dashboard"));
    expect(NextResponse.redirect).toHaveBeenCalledWith(
      expect.objectContaining({
        pathname: "/login",
      }),
    );
  });

  it("includes callbackUrl in redirect", () => {
    middleware(createRequest("/dashboard"));
    const redirectUrl = (NextResponse.redirect as ReturnType<typeof vi.fn>).mock
      .calls[0][0] as URL;
    expect(redirectUrl.searchParams.get("callbackUrl")).toBe("/dashboard");
  });

  it("passes through protected paths when cookie is present", () => {
    const result = middleware(createRequest("/dashboard", true));
    expect(NextResponse.next).toHaveBeenCalled();
    expect(result).toEqual({ type: "next" });
  });

  it("redirects nested protected paths (e.g. /admin/users)", () => {
    middleware(createRequest("/admin/users"));
    expect(NextResponse.redirect).toHaveBeenCalled();
  });

  it("passes through nested protected paths with cookie", () => {
    middleware(createRequest("/admin/users", true));
    expect(NextResponse.next).toHaveBeenCalled();
  });

  it.each(["/submit", "/suggest", "/profile", "/watchlist", "/following", "/notifications"])(
    "redirects %s without cookie",
    (path) => {
      vi.clearAllMocks();
      middleware(createRequest(path));
      expect(NextResponse.redirect).toHaveBeenCalled();
    },
  );
});
