import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, userEvent, waitFor } from "@/test/test-utils";
import { WatchlistButton } from "./watchlist-button";
import { createMockAuthValue } from "@/test/test-utils";

const { mockApi, MockApiClientError } = vi.hoisted(() => {
  class MockApiClientError extends Error {
    constructor(
      message: string,
      public status: number,
    ) {
      super(message);
      this.name = "ApiClientError";
    }
  }
  return {
    mockApi: {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      patch: vi.fn(),
      delete: vi.fn(),
      download: vi.fn(),
    },
    MockApiClientError,
  };
});

vi.mock("@/lib/api-client", () => ({
  api: mockApi,
  ApiClientError: MockApiClientError,
}));

let authValue = createMockAuthValue();
vi.mock("@/lib/auth-context", () => ({
  useAuth: () => authValue,
}));

describe("WatchlistButton", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    authValue = createMockAuthValue();
  });

  it("returns null when unauthenticated", () => {
    const { container } = render(<WatchlistButton stockId="s1" />);
    expect(container.innerHTML).toBe("");
  });

  it("renders Watch button when authenticated and not watching", () => {
    authValue = createMockAuthValue({ isAuthenticated: true });
    mockApi.get.mockResolvedValue({ watching: false });

    render(<WatchlistButton stockId="s1" />);
    expect(screen.getByRole("button", { name: /watch$/i })).toBeInTheDocument();
  });

  it("renders Watching button when already watching", async () => {
    authValue = createMockAuthValue({ isAuthenticated: true });
    mockApi.get.mockResolvedValue({ watching: true });

    render(<WatchlistButton stockId="s1" />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /watching/i })).toBeInTheDocument();
    });
  });

  it("toggles to Watching on click", async () => {
    authValue = createMockAuthValue({ isAuthenticated: true });
    mockApi.get.mockResolvedValue({ watching: false });
    mockApi.post.mockResolvedValue({});

    const user = userEvent.setup();
    render(<WatchlistButton stockId="s1" />);
    await user.click(screen.getByRole("button", { name: /watch$/i }));
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /watching/i })).toBeInTheDocument();
    });
  });

  it("handles 409 conflict by setting watching to true", async () => {
    authValue = createMockAuthValue({ isAuthenticated: true });
    mockApi.get.mockResolvedValue({ watching: false });
    mockApi.post.mockRejectedValue(new MockApiClientError("Conflict", 409));

    const user = userEvent.setup();
    render(<WatchlistButton stockId="s1" />);
    await user.click(screen.getByRole("button", { name: /watch$/i }));
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /watching/i })).toBeInTheDocument();
    });
  });

  it("disables button while loading", async () => {
    authValue = createMockAuthValue({ isAuthenticated: true });
    mockApi.get.mockResolvedValue({ watching: false });
    mockApi.post.mockImplementation(() => new Promise(() => {}));

    const user = userEvent.setup();
    render(<WatchlistButton stockId="s1" />);
    await user.click(screen.getByRole("button", { name: /watch$/i }));
    expect(screen.getByRole("button")).toBeDisabled();
  });
});
