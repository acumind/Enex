import { test, expect } from "@playwright/test";
import { mockPublicApiRoutes } from "./fixtures/api-routes";
import { setAuthCookie } from "./fixtures/auth";

const PROTECTED_PATHS = [
  "/dashboard",
  "/submit",
  "/suggest",
  "/profile",
  "/watchlist",
  "/following",
  "/notifications",
];

test.beforeEach(async ({ page }) => {
  await mockPublicApiRoutes(page);
});

// ---------------------------------------------------------------------------
// Unauthenticated redirects
// ---------------------------------------------------------------------------

for (const path of PROTECTED_PATHS) {
  test(`${path} redirects to /login without auth cookie`, async ({ page }) => {
    const response = await page.goto(path);
    // Next.js middleware issues a 307 redirect → browser follows it
    await expect(page).toHaveURL(/\/login/);
    // callbackUrl should be present
    const url = new URL(page.url());
    expect(url.searchParams.get("callbackUrl")).toBe(path);
    // Verify we didn't get redirected to the original path
    expect(response?.url()).toContain("/login");
  });
}

// ---------------------------------------------------------------------------
// Authenticated access
// ---------------------------------------------------------------------------

test("/dashboard loads without redirect when auth cookie present", async ({
  page,
  context,
}) => {
  await setAuthCookie(context);
  // Mock the auth refresh + me endpoints so the page renders
  await page.route("**/api/v1/auth/refresh", (route) =>
    route.fulfill({
      status: 200,
      json: { access_token: "mock-jwt", token_type: "bearer" },
    }),
  );
  await page.route("**/api/v1/auth/me", (route) =>
    route.fulfill({
      status: 200,
      json: {
        id: "u1",
        email: "test@enex.in",
        phone: null,
        name: "Test User",
        avatar_url: null,
        role: "user",
        is_email_verified: true,
        is_phone_verified: false,
        auth_methods: ["email"],
        is_active: true,
        created_at: "2025-01-01T00:00:00Z",
        last_login_at: null,
      },
    }),
  );
  await page.route("**/api/v1/notifications/unread-count", (route) =>
    route.fulfill({ status: 200, json: { count: 0 } }),
  );
  // Catch any other API calls the dashboard might make
  await page.route("**/api/v1/admin/**", (route) =>
    route.fulfill({ status: 403, json: { detail: "Forbidden" } }),
  );

  await page.goto("/dashboard");
  await expect(page).toHaveURL(/\/dashboard/);
});

// ---------------------------------------------------------------------------
// Public paths never redirect
// ---------------------------------------------------------------------------

const PUBLIC_PATHS = ["/", "/about", "/leaderboard"];

for (const path of PUBLIC_PATHS) {
  test(`${path} loads without redirect`, async ({ page }) => {
    // Mock leaderboard for /leaderboard route
    await page.route("**/api/v1/leaderboard*", (route) =>
      route.fulfill({ status: 200, json: [] }),
    );
    await page.goto(path);
    await expect(page).toHaveURL(new RegExp(`${path === "/" ? "/$" : path}`));
  });
}
