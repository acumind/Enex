import { vi } from "vitest";

/**
 * Mock api client for tests.
 *
 * Usage in test files:
 * ```ts
 * vi.mock("@/lib/api-client", () => ({
 *   api: mockApi,
 *   ApiClientError: MockApiClientError,
 * }));
 * ```
 */
export const mockApi = {
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  patch: vi.fn(),
  delete: vi.fn(),
  download: vi.fn(),
};

export class MockApiClientError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiClientError";
  }
}

/** Reset all mocks between tests. */
export function resetApiMocks() {
  Object.values(mockApi).forEach((fn) => fn.mockReset());
}
