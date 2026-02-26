import { test, expect } from "@playwright/test";
import { mockPublicApiRoutes, mockAnnouncementApi } from "./fixtures/api-routes";
import { mockAnnouncement } from "./fixtures/mock-data";

/** Set up unauthenticated routes + announcement mock. */
async function setupWithAnnouncement(page: import("@playwright/test").Page) {
  await page.route("**/api/v1/auth/refresh", (route) =>
    route.fulfill({ status: 401, json: { detail: "Not authenticated" } }),
  );
  await page.route("**/api/v1/notifications/unread-count", (route) =>
    route.fulfill({ status: 401, json: { detail: "Not authenticated" } }),
  );
  await mockAnnouncementApi(page, mockAnnouncement);
}

test("shows banner text when API returns announcement", async ({ page }) => {
  await setupWithAnnouncement(page);
  await page.goto("/");
  // Clear any stale dismissed state
  await page.evaluate(() => localStorage.clear());
  await page.reload();
  await expect(page.getByText(mockAnnouncement.text)).toBeVisible();
});

test("dismiss hides banner", async ({ page }) => {
  await setupWithAnnouncement(page);
  await page.goto("/");
  await page.evaluate(() => localStorage.clear());
  await page.reload();
  await expect(page.getByText(mockAnnouncement.text)).toBeVisible();

  // Click dismiss button
  await page.getByRole("button", { name: "Dismiss" }).click();
  await expect(page.getByText(mockAnnouncement.text)).not.toBeVisible();
});

test("dismissed banner stays hidden on reload", async ({ page }) => {
  await setupWithAnnouncement(page);
  await page.goto("/");
  await page.evaluate(() => localStorage.clear());
  await page.reload();
  await expect(page.getByText(mockAnnouncement.text)).toBeVisible();

  // Dismiss
  await page.getByRole("button", { name: "Dismiss" }).click();
  await expect(page.getByText(mockAnnouncement.text)).not.toBeVisible();

  // Reload — banner should stay hidden (localStorage persists the dismissed key)
  await page.reload();
  await page.waitForLoadState("networkidle");
  await expect(page.getByText(mockAnnouncement.text)).not.toBeVisible();
});

test("no banner when API returns 404", async ({ page }) => {
  await mockPublicApiRoutes(page); // announcement returns 404 by default
  await page.goto("/");

  // Banner text should not be present
  await expect(page.getByText(mockAnnouncement.text)).not.toBeVisible();
});
