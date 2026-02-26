import { render, type RenderOptions } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactElement, ReactNode } from "react";
import type { AuthUser } from "@/lib/types";

/** Create a fresh QueryClient for each test (no retries, instant GC). */
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });
}

/** Wrap component in QueryClientProvider. */
function AllProviders({ children }: { children: ReactNode }) {
  const queryClient = createTestQueryClient();
  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

/** Custom render that wraps in test providers. */
function customRender(
  ui: ReactElement,
  options?: Omit<RenderOptions, "wrapper">,
) {
  return render(ui, { wrapper: AllProviders, ...options });
}

// --- Auth mock helpers ---

export function createMockAuthValue(overrides: Partial<{
  user: AuthUser | null;
  accessToken: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (token: string, user: AuthUser) => void;
  logout: () => Promise<void>;
  refreshAccessToken: () => Promise<string | null>;
}> = {}) {
  return {
    user: null,
    accessToken: null,
    isLoading: false,
    isAuthenticated: false,
    login: vi.fn(),
    logout: vi.fn().mockResolvedValue(undefined),
    refreshAccessToken: vi.fn().mockResolvedValue(null),
    ...overrides,
  };
}

export const mockAuthUser: AuthUser = {
  id: "user-1",
  email: "test@example.com",
  phone: null,
  name: "Test User",
  avatar_url: null,
  role: "user",
  is_email_verified: true,
  is_phone_verified: false,
  auth_methods: ["email"],
  is_active: true,
  created_at: "2025-01-01T00:00:00Z",
  last_login_at: "2025-06-01T12:00:00Z",
};

export const mockAdminUser: AuthUser = {
  id: "admin-1",
  email: "admin@enex.in",
  phone: null,
  name: "Admin User",
  avatar_url: null,
  role: "admin",
  is_email_verified: true,
  is_phone_verified: false,
  auth_methods: ["email"],
  is_active: true,
  created_at: "2025-01-01T00:00:00Z",
  last_login_at: "2025-06-01T12:00:00Z",
};

// Re-export everything from RTL + userEvent
export * from "@testing-library/react";
export { default as userEvent } from "@testing-library/user-event";

// Override render with our custom version
export { customRender as render };
