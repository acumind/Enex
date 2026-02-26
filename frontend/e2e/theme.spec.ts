import { test, expect } from "@playwright/test";
import { mockPublicApiRoutes } from "./fixtures/api-routes";

test.beforeEach(async ({ page }) => {
  await mockPublicApiRoutes(page);
});

test("theme toggle button exists with correct aria-label", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("button", { name: "Toggle theme" }),
  ).toBeVisible();
});

test("clicking toggle adds dark class on html element", async ({ page }) => {
  await page.goto("/");

  // Initial state: no dark class (default is light in test environment)
  const html = page.locator("html");

  // Click theme toggle
  await page.getByRole("button", { name: "Toggle theme" }).click();

  // Should now have dark class
  await expect(html).toHaveClass(/dark/);
});
