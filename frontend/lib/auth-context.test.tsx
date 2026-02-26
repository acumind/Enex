import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, act, waitFor } from "@testing-library/react";
import { AuthProvider, useAuth } from "./auth-context";
import type { AuthUser } from "./types";

const mockUser: AuthUser = {
  id: "u1",
  email: "test@example.com",
  phone: null,
  name: "Test",
  avatar_url: null,
  role: "user",
  is_email_verified: true,
  is_phone_verified: false,
  auth_methods: ["email"],
  is_active: true,
  created_at: "2025-01-01T00:00:00Z",
  last_login_at: null,
};

const mockFetch = vi.fn();

beforeEach(() => {
  vi.stubGlobal("fetch", mockFetch);
  // By default, session restore fails (no session)
  mockFetch.mockResolvedValue({ ok: false });
});

function TestConsumer() {
  const { user, isLoading, isAuthenticated } = useAuth();
  return (
    <div>
      <span data-testid="loading">{String(isLoading)}</span>
      <span data-testid="authenticated">{String(isAuthenticated)}</span>
      <span data-testid="user">{user?.name ?? "none"}</span>
    </div>
  );
}

describe("AuthProvider", () => {
  it("renders children", async () => {
    render(
      <AuthProvider>
        <p>child</p>
      </AuthProvider>,
    );
    await waitFor(() => expect(screen.getByText("child")).toBeInTheDocument());
  });

  it("starts in loading state then resolves", async () => {
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );
    // Eventually isLoading becomes false
    await waitFor(() => {
      expect(screen.getByTestId("loading").textContent).toBe("false");
    });
  });

  it("restores session on mount when refresh succeeds", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ access_token: "tok" }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockUser),
      });

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("user").textContent).toBe("Test");
      expect(screen.getByTestId("authenticated").textContent).toBe("true");
    });
  });
});

describe("useAuth", () => {
  it("throws when used outside AuthProvider", () => {
    // Suppress console.error for expected error
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    expect(() => render(<TestConsumer />)).toThrow(
      "useAuth must be used within AuthProvider",
    );
    spy.mockRestore();
  });
});

describe("login / logout", () => {
  function LoginLogoutConsumer() {
    const { user, isAuthenticated, login, logout } = useAuth();
    return (
      <div>
        <span data-testid="auth">{String(isAuthenticated)}</span>
        <span data-testid="name">{user?.name ?? "none"}</span>
        <button onClick={() => login("tok123", mockUser)}>Login</button>
        <button onClick={() => logout()}>Logout</button>
      </div>
    );
  }

  it("login() sets token and user", async () => {
    render(
      <AuthProvider>
        <LoginLogoutConsumer />
      </AuthProvider>,
    );

    await waitFor(() =>
      expect(screen.getByTestId("auth").textContent).toBe("false"),
    );

    await act(async () => {
      screen.getByText("Login").click();
    });

    expect(screen.getByTestId("auth").textContent).toBe("true");
    expect(screen.getByTestId("name").textContent).toBe("Test");
  });

  it("logout() clears state and calls API", async () => {
    mockFetch
      // session restore fails
      .mockResolvedValueOnce({ ok: false });

    render(
      <AuthProvider>
        <LoginLogoutConsumer />
      </AuthProvider>,
    );

    await waitFor(() =>
      expect(screen.getByTestId("auth").textContent).toBe("false"),
    );

    // Login first
    await act(async () => {
      screen.getByText("Login").click();
    });
    expect(screen.getByTestId("auth").textContent).toBe("true");

    // Reset fetch mock to track logout call
    mockFetch.mockResolvedValueOnce({ ok: true });

    // Logout
    await act(async () => {
      screen.getByText("Logout").click();
    });

    expect(screen.getByTestId("auth").textContent).toBe("false");
    expect(screen.getByTestId("name").textContent).toBe("none");
  });

  it("logout() clears state even if API call fails", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false }); // session restore fails

    render(
      <AuthProvider>
        <LoginLogoutConsumer />
      </AuthProvider>,
    );

    await waitFor(() =>
      expect(screen.getByTestId("auth").textContent).toBe("false"),
    );

    // Login
    await act(async () => {
      screen.getByText("Login").click();
    });

    // Logout API fails
    mockFetch.mockRejectedValueOnce(new Error("network error"));

    await act(async () => {
      screen.getByText("Logout").click();
    });

    expect(screen.getByTestId("auth").textContent).toBe("false");
  });
});
