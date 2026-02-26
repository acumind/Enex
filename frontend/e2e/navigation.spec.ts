import { test, expect } from "@playwright/test";
import {
  mockPublicApiRoutes,
  mockAuthenticatedState,
  mockAnnouncementApi,
} from "./fixtures/api-routes";

test.beforeEach(async ({ page }) => {
  await mockPublicApiRoutes(page);
});

// ---------------------------------------------------------------------------
// Navbar
// ---------------------------------------------------------------------------

test.describe("Navbar", () => {
  test("logo links to home", async ({ page }) => {
    await page.goto("/about");
    const logo = page.getByRole("link", { name: "Enex" });
    await expect(logo).toBeVisible();
    await expect(logo).toHaveAttribute("href", "/");
  });

  test("has Leaderboard link", async ({ page }) => {
    await page.goto("/");
    const link = page.getByRole("navigation").getByRole("link", { name: "Leaderboard" });
    await expect(link).toBeVisible();
    await expect(link).toHaveAttribute("href", "/leaderboard");
  });

  test("has About link", async ({ page }) => {
    await page.goto("/");
    const link = page.getByRole("navigation").getByRole("link", { name: "About" });
    await expect(link).toBeVisible();
    await expect(link).toHaveAttribute("href", "/about");
  });

  test("shows Login button when unauthenticated", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("link", { name: "Login" })).toBeVisible();
  });

  test("shows user name and Logout when authenticated", async ({ page }) => {
    // Override the default unauthenticated mocks
    await mockAuthenticatedState(page);
    await mockAnnouncementApi(page);
    await page.goto("/");
    await expect(page.getByText("Test User")).toBeVisible();
    await expect(page.getByRole("button", { name: "Logout" })).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Footer
// ---------------------------------------------------------------------------

test.describe("Footer", () => {
  test("has all 5 navigation links", async ({ page }) => {
    await page.goto("/");
    const footer = page.locator("footer");
    await expect(footer.getByRole("link", { name: "Leaderboard" })).toBeVisible();
    await expect(footer.getByRole("link", { name: "About" })).toBeVisible();
    await expect(footer.getByRole("link", { name: "Terms" })).toBeVisible();
    await expect(footer.getByRole("link", { name: "Privacy" })).toBeVisible();
    await expect(footer.getByRole("link", { name: "Contact" })).toBeVisible();
  });

  test("displays copyright with current year", async ({ page }) => {
    await page.goto("/");
    const year = new Date().getFullYear().toString();
    await expect(page.locator("footer")).toContainText(year);
    await expect(page.locator("footer")).toContainText("Enex");
  });

  test("displays disclaimer text", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("footer")).toContainText("Not financial advice");
  });

  test("footer links navigate correctly", async ({ page }) => {
    await page.goto("/");
    await page.locator("footer").getByRole("link", { name: "About" }).click();
    await expect(page).toHaveURL(/\/about/);
  });
});
