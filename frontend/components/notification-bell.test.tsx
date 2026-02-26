import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, userEvent, waitFor } from "@/test/test-utils";
import { NotificationBell } from "./notification-bell";
import { createMockAuthValue } from "@/test/test-utils";

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
    download: vi.fn(),
  },
}));

vi.mock("@/lib/api-client", () => ({
  api: mockApi,
}));

let authValue = createMockAuthValue();
vi.mock("@/lib/auth-context", () => ({
  useAuth: () => authValue,
}));

const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
  usePathname: () => "/",
  useSearchParams: () => new URLSearchParams(),
}));

describe("NotificationBell", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    authValue = createMockAuthValue();
  });

  it("returns null when unauthenticated", () => {
    const { container } = render(<NotificationBell />);
    expect(container.innerHTML).toBe("");
  });

  it("renders bell button when authenticated", async () => {
    authValue = createMockAuthValue({ isAuthenticated: true });
    mockApi.get.mockResolvedValue({ count: 0 });

    render(<NotificationBell />);
    const buttons = screen.getAllByRole("button");
    expect(buttons.length).toBeGreaterThanOrEqual(1);
  });

  it("shows unread badge when count > 0", async () => {
    authValue = createMockAuthValue({ isAuthenticated: true });
    mockApi.get.mockResolvedValue({ count: 5 });

    render(<NotificationBell />);
    await waitFor(() => {
      expect(screen.getByText("5")).toBeInTheDocument();
    });
  });

  it("shows 99+ for counts above 99", async () => {
    authValue = createMockAuthValue({ isAuthenticated: true });
    mockApi.get.mockResolvedValue({ count: 150 });

    render(<NotificationBell />);
    await waitFor(() => {
      expect(screen.getByText("99+")).toBeInTheDocument();
    });
  });

  it("opens dropdown with notifications on click", async () => {
    authValue = createMockAuthValue({ isAuthenticated: true });
    mockApi.get
      .mockResolvedValueOnce({ count: 1 })
      .mockResolvedValueOnce({
        items: [
          {
            id: "n1",
            user_id: "u1",
            type: "prediction_outcome",
            title: "Prediction Hit!",
            message: "Your prediction was correct",
            data: {},
            is_read: false,
            created_at: "2025-06-01T00:00:00Z",
          },
        ],
      });

    const user = userEvent.setup();
    render(<NotificationBell />);

    await waitFor(() => expect(screen.getByText("1")).toBeInTheDocument());

    await user.click(screen.getAllByRole("button")[0]);

    await waitFor(() => {
      expect(screen.getByText("Prediction Hit!")).toBeInTheDocument();
      expect(screen.getByText("Your prediction was correct")).toBeInTheDocument();
    });
  });

  it("renders 'Notifications' header in dropdown", async () => {
    authValue = createMockAuthValue({ isAuthenticated: true });
    mockApi.get
      .mockResolvedValueOnce({ count: 0 })
      .mockResolvedValueOnce({ items: [] });

    const user = userEvent.setup();
    render(<NotificationBell />);

    await user.click(screen.getAllByRole("button")[0]);

    await waitFor(() => {
      expect(screen.getByText("Notifications")).toBeInTheDocument();
    });
  });
});
