import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, userEvent, waitFor } from "@/test/test-utils";
import { FollowButton } from "./follow-button";
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

describe("FollowButton", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    authValue = createMockAuthValue();
  });

  it("returns null when unauthenticated", () => {
    const { container } = render(<FollowButton predictorId="p1" />);
    expect(container.innerHTML).toBe("");
  });

  it("renders Follow button when authenticated and not following", () => {
    authValue = createMockAuthValue({ isAuthenticated: true });
    mockApi.get.mockResolvedValue({ following: false });

    render(<FollowButton predictorId="p1" />);
    expect(screen.getByRole("button", { name: /follow/i })).toBeInTheDocument();
  });

  it("renders Following button when already following", async () => {
    authValue = createMockAuthValue({ isAuthenticated: true });
    mockApi.get.mockResolvedValue({ following: true });

    render(<FollowButton predictorId="p1" />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /following/i })).toBeInTheDocument();
    });
  });

  it("toggles to Following on click", async () => {
    authValue = createMockAuthValue({ isAuthenticated: true });
    mockApi.get.mockResolvedValue({ following: false });
    mockApi.post.mockResolvedValue({});

    const user = userEvent.setup();
    render(<FollowButton predictorId="p1" />);
    await user.click(screen.getByRole("button", { name: /follow/i }));
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /following/i })).toBeInTheDocument();
    });
  });

  it("handles 409 conflict by setting following to true", async () => {
    authValue = createMockAuthValue({ isAuthenticated: true });
    mockApi.get.mockResolvedValue({ following: false });
    mockApi.post.mockRejectedValue(new MockApiClientError("Conflict", 409));

    const user = userEvent.setup();
    render(<FollowButton predictorId="p1" />);
    await user.click(screen.getByRole("button", { name: /follow/i }));
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /following/i })).toBeInTheDocument();
    });
  });

  it("disables button while loading", async () => {
    authValue = createMockAuthValue({ isAuthenticated: true });
    mockApi.get.mockResolvedValue({ following: false });
    mockApi.post.mockImplementation(() => new Promise(() => {}));

    const user = userEvent.setup();
    render(<FollowButton predictorId="p1" />);
    await user.click(screen.getByRole("button", { name: /follow/i }));
    expect(screen.getByRole("button")).toBeDisabled();
  });
});
