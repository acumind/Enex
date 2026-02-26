import type { Page } from "@playwright/test";
import type {
  AnnouncementResponse,
  LeaderboardEntry,
  SearchResponse,
} from "../../lib/types";
import { mockAuthUser } from "./mock-data";

/**
 * Mock the common API routes that fire on every page load (announcement, auth refresh,
 * notifications). Defaults to unauthenticated state.
 */
export async function mockPublicApiRoutes(page: Page) {
  await page.route("**/api/v1/announcement", (route) =>
    route.fulfill({ status: 404, body: "" }),
  );
  await page.route("**/api/v1/auth/refresh", (route) =>
    route.fulfill({ status: 401, json: { detail: "Not authenticated" } }),
  );
  await page.route("**/api/v1/notifications/unread-count", (route) =>
    route.fulfill({ status: 401, json: { detail: "Not authenticated" } }),
  );
}

export async function mockLeaderboardApi(
  page: Page,
  data: LeaderboardEntry[] = [],
) {
  await page.route("**/api/v1/leaderboard*", (route) =>
    route.fulfill({ status: 200, json: data }),
  );
}

export async function mockSearchApi(
  page: Page,
  response: SearchResponse = { predictors: [], stocks: [] },
) {
  await page.route("**/api/v1/search*", (route) =>
    route.fulfill({ status: 200, json: response }),
  );
}

export async function mockAnnouncementApi(
  page: Page,
  data: AnnouncementResponse | null = null,
) {
  await page.route("**/api/v1/announcement", (route) => {
    if (data) {
      return route.fulfill({ status: 200, json: data });
    }
    return route.fulfill({ status: 404, body: "" });
  });
}

/**
 * Set up routes so the AuthProvider considers the user authenticated:
 * - auth/refresh returns a valid access_token
 * - auth/me returns the mock user
 * - notifications/unread-count returns 0
 */
export async function mockAuthenticatedState(page: Page) {
  await page.route("**/api/v1/auth/refresh", (route) =>
    route.fulfill({
      status: 200,
      json: { access_token: "mock-jwt", token_type: "bearer" },
    }),
  );
  await page.route("**/api/v1/auth/me", (route) =>
    route.fulfill({ status: 200, json: mockAuthUser }),
  );
  await page.route("**/api/v1/notifications/unread-count", (route) =>
    route.fulfill({ status: 200, json: { count: 0 } }),
  );
}

/**
 * Mock the OTP send + verify flow for login tests.
 */
export async function mockOtpFlow(page: Page) {
  await page.route("**/api/v1/auth/otp/send", (route) =>
    route.fulfill({
      status: 200,
      json: {
        message: "OTP sent",
        identifier: "test@enex.in",
        expires_in_seconds: 300,
      },
    }),
  );
  await page.route("**/api/v1/auth/otp/verify", (route) =>
    route.fulfill({
      status: 200,
      json: {
        access_token: "mock-jwt",
        token_type: "bearer",
        user: mockAuthUser,
      },
    }),
  );
}

/**
 * Mock OTP send to return 429 rate limit.
 */
export async function mockOtpRateLimited(page: Page) {
  await page.route("**/api/v1/auth/otp/send", (route) =>
    route.fulfill({
      status: 429,
      json: { detail: "Too many OTP requests. Try again later." },
    }),
  );
}
