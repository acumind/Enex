import { test, expect } from "@playwright/test";
import {
  mockPublicApiRoutes,
  mockLeaderboardApi,
} from "./fixtures/api-routes";
import { mockLeaderboard, mockLeaderboard21 } from "./fixtures/mock-data";

test.beforeEach(async ({ page }) => {
  await mockPublicApiRoutes(page);
});

test("renders table with mock data", async ({ page }) => {
  await mockLeaderboardApi(page, mockLeaderboard);
  await page.goto("/leaderboard");

  // All 5 analyst names visible
  for (const entry of mockLeaderboard) {
    await expect(page.getByRole("link", { name: entry.predictor_name })).toBeVisible();
  }
});

test("displays accuracy, hits, and misses", async ({ page }) => {
  await mockLeaderboardApi(page, mockLeaderboard);
  await page.goto("/leaderboard");

  // Check first entry has hits/misses
  const firstRow = page.locator("tbody tr").first();
  await expect(firstRow).toContainText(String(mockLeaderboard[0].hits));
  await expect(firstRow).toContainText(String(mockLeaderboard[0].misses));
});

test("filter tabs change predictor_type API param", async ({ page }) => {
  const requests: string[] = [];
  await page.route("**/api/v1/leaderboard*", (route) => {
    requests.push(route.request().url());
    return route.fulfill({ status: 200, json: mockLeaderboard });
  });

  await page.goto("/leaderboard");
  // Wait for initial load
  await expect(page.locator("tbody tr").first()).toBeVisible();

  // Click "Brokerage" tab
  await page.getByRole("tab", { name: "Brokerage" }).click();
  await page.waitForTimeout(300); // wait for re-fetch

  const brokerageReq = requests.find((u) => u.includes("predictor_type=brokerage"));
  expect(brokerageReq).toBeTruthy();
});

test("sort dropdown changes sort_by param", async ({ page }) => {
  const requests: string[] = [];
  await page.route("**/api/v1/leaderboard*", (route) => {
    requests.push(route.request().url());
    return route.fulfill({ status: 200, json: mockLeaderboard });
  });

  await page.goto("/leaderboard");
  await expect(page.locator("tbody tr").first()).toBeVisible();

  // Open sort dropdown and pick "Streak"
  await page.getByRole("combobox").click();
  await page.getByRole("option", { name: "Streak" }).click();
  await page.waitForTimeout(300);

  const streakReq = requests.find((u) => u.includes("sort_by=streak_current"));
  expect(streakReq).toBeTruthy();
});

test("Previous disabled on page 1, Next enabled with 21 entries", async ({ page }) => {
  await mockLeaderboardApi(page, mockLeaderboard21);
  await page.goto("/leaderboard");

  await expect(page.locator("tbody tr").first()).toBeVisible();

  const prevBtn = page.getByRole("button", { name: "Previous", exact: true });
  const nextBtn = page.getByRole("button", { name: "Next", exact: true });

  await expect(prevBtn).toBeDisabled();
  await expect(nextBtn).toBeEnabled();
});

test("Next button advances to page 2", async ({ page }) => {
  const requests: string[] = [];
  await page.route("**/api/v1/leaderboard*", (route) => {
    requests.push(route.request().url());
    return route.fulfill({ status: 200, json: mockLeaderboard21 });
  });

  await page.goto("/leaderboard");
  await expect(page.locator("tbody tr").first()).toBeVisible();

  await page.getByRole("button", { name: "Next", exact: true }).click();
  await page.waitForTimeout(300);

  const page2Req = requests.find((u) => u.includes("offset=20"));
  expect(page2Req).toBeTruthy();
  await expect(page.getByText("Page 2")).toBeVisible();
});

test("empty state message", async ({ page }) => {
  await mockLeaderboardApi(page, []);
  await page.goto("/leaderboard");

  await expect(page.getByText("No analysts match the current filters.")).toBeVisible();
});

test("analyst name links to predictor page", async ({ page }) => {
  await mockLeaderboardApi(page, mockLeaderboard);
  await page.goto("/leaderboard");

  const link = page.getByRole("link", { name: mockLeaderboard[0].predictor_name });
  await expect(link).toHaveAttribute(
    "href",
    `/predictor/${mockLeaderboard[0].predictor_slug}`,
  );
});
