import { test, expect } from "@playwright/test";
import { mockPublicApiRoutes } from "./fixtures/api-routes";

test.beforeEach(async ({ page }) => {
  await mockPublicApiRoutes(page);
});

test("renders hero heading", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Who Really Gets the Market Right?" }),
  ).toBeVisible();
});

test("renders CTA buttons", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("link", { name: "View Leaderboard" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Browse Predictions" })).toBeVisible();
});

test("renders How It Works section with 3 steps", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "How It Works" })).toBeVisible();
  await expect(page.getByText("Predictions Are Logged")).toBeVisible();
  await expect(page.getByText("Markets Do Their Thing")).toBeVisible();
  await expect(page.getByText("Accuracy Is Scored")).toBeVisible();
});

test("View Leaderboard navigates to /leaderboard", async ({ page }) => {
  // Also mock leaderboard API since we'll navigate there
  await page.route("**/api/v1/leaderboard*", (route) =>
    route.fulfill({ status: 200, json: [] }),
  );
  await page.goto("/");
  await page.getByRole("link", { name: "View Leaderboard" }).click();
  await expect(page).toHaveURL(/\/leaderboard/);
});
