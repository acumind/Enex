import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, userEvent } from "@/test/test-utils";
import { Navbar } from "./navbar";
import { createMockAuthValue, mockAuthUser } from "@/test/test-utils";

// Mock child components to isolate Navbar logic
vi.mock("@/components/notification-bell", () => ({
  NotificationBell: () => <div data-testid="notification-bell" />,
}));
vi.mock("@/components/theme-toggle", () => ({
  ThemeToggle: () => <div data-testid="theme-toggle" />,
}));
vi.mock("@/components/search-bar", () => ({
  SearchBar: () => <div data-testid="search-bar" />,
}));

const mockLogout = vi.fn().mockResolvedValue(undefined);
let authValue = createMockAuthValue();

vi.mock("@/lib/auth-context", () => ({
  useAuth: () => authValue,
}));

describe("Navbar", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    authValue = createMockAuthValue();
  });

  it("renders logo link to /", () => {
    render(<Navbar />);
    const logo = screen.getByRole("link", { name: "Enex" });
    expect(logo).toHaveAttribute("href", "/");
  });

  it("renders Leaderboard nav link", () => {
    render(<Navbar />);
    expect(screen.getByRole("link", { name: "Leaderboard" })).toHaveAttribute(
      "href",
      "/leaderboard",
    );
  });

  it("renders About nav link", () => {
    render(<Navbar />);
    expect(screen.getByRole("link", { name: "About" })).toHaveAttribute(
      "href",
      "/about",
    );
  });

  it("shows Login button when unauthenticated", () => {
    render(<Navbar />);
    const login = screen.getByRole("link", { name: "Login" });
    expect(login).toHaveAttribute("href", "/login");
  });

  it("shows user name and Logout button when authenticated", () => {
    authValue = createMockAuthValue({
      user: mockAuthUser,
      isAuthenticated: true,
      logout: mockLogout,
    });
    render(<Navbar />);
    expect(screen.getByText("Test User")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Logout" })).toBeInTheDocument();
  });

  it("falls back to email when name is null", () => {
    authValue = createMockAuthValue({
      user: { ...mockAuthUser, name: null },
      isAuthenticated: true,
    });
    render(<Navbar />);
    expect(screen.getByText("test@example.com")).toBeInTheDocument();
  });

  it("falls back to 'User' when both name and email are null", () => {
    authValue = createMockAuthValue({
      user: { ...mockAuthUser, name: null, email: null },
      isAuthenticated: true,
    });
    render(<Navbar />);
    expect(screen.getByText("User")).toBeInTheDocument();
  });

  it("calls logout() when Logout button is clicked", async () => {
    authValue = createMockAuthValue({
      user: mockAuthUser,
      isAuthenticated: true,
      logout: mockLogout,
    });
    const user = userEvent.setup();
    render(<Navbar />);
    await user.click(screen.getByRole("button", { name: "Logout" }));
    expect(mockLogout).toHaveBeenCalledTimes(1);
  });
});
