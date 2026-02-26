import { test, expect } from "@playwright/test";
import {
  mockPublicApiRoutes,
  mockOtpFlow,
  mockOtpRateLimited,
} from "./fixtures/api-routes";

test.beforeEach(async ({ page }) => {
  await mockPublicApiRoutes(page);
});

test("renders Welcome card", async ({ page }) => {
  await page.goto("/login");
  await expect(page.getByText("Welcome to Enex").first()).toBeVisible();
  await expect(page.getByText("Sign in to track analyst predictions").first()).toBeVisible();
});

test("has 3 tabs: Phone (default), Email, Google", async ({ page }) => {
  await page.goto("/login");
  await expect(page.getByRole("tab", { name: "Phone" })).toBeVisible();
  await expect(page.getByRole("tab", { name: "Email" })).toBeVisible();
  await expect(page.getByRole("tab", { name: "Google" })).toBeVisible();

  // Phone tab is selected by default
  await expect(page.getByRole("tab", { name: "Phone" })).toHaveAttribute(
    "data-state",
    "active",
  );
});

test("Email tab shows email input", async ({ page }) => {
  await page.goto("/login");
  await page.getByRole("tab", { name: "Email" }).click();
  await expect(page.getByLabel("Email Address")).toBeVisible();
  await expect(page.getByPlaceholder("you@example.com")).toBeVisible();
});

test("Google tab shows Continue with Google button", async ({ page }) => {
  await page.goto("/login");
  await page.getByRole("tab", { name: "Google" }).click();
  await expect(page.getByRole("button", { name: /Continue with Google/ })).toBeVisible();
});

test("Send button disabled when input is empty", async ({ page }) => {
  await page.goto("/login");
  await page.getByRole("tab", { name: "Email" }).click();
  const sendBtn = page.getByRole("button", { name: "Send Verification Code" });
  await expect(sendBtn).toBeDisabled();
});

test("OTP send transitions to verify step", async ({ page }) => {
  await mockOtpFlow(page);
  await page.goto("/login");
  await page.getByRole("tab", { name: "Email" }).click();

  await page.getByPlaceholder("you@example.com").fill("test@enex.in");
  await page.getByRole("button", { name: "Send Verification Code" }).click();

  // Verify step
  await expect(page.getByText("Code sent to")).toBeVisible();
  await expect(page.getByText("test@enex.in")).toBeVisible();
  await expect(page.getByLabel("Verification Code")).toBeVisible();
});

test("Verify button disabled until 6 digits entered", async ({ page }) => {
  await mockOtpFlow(page);
  await page.goto("/login");
  await page.getByRole("tab", { name: "Email" }).click();

  await page.getByPlaceholder("you@example.com").fill("test@enex.in");
  await page.getByRole("button", { name: "Send Verification Code" }).click();
  await expect(page.getByLabel("Verification Code")).toBeVisible();

  const verifyBtn = page.getByRole("button", { name: "Verify & Sign In" });
  await expect(verifyBtn).toBeDisabled();

  // Enter 5 digits — still disabled
  await page.getByLabel("Verification Code").fill("12345");
  await expect(verifyBtn).toBeDisabled();

  // Enter 6 digits — enabled
  await page.getByLabel("Verification Code").fill("123456");
  await expect(verifyBtn).toBeEnabled();
});

test("Change email returns to input step", async ({ page }) => {
  await mockOtpFlow(page);
  await page.goto("/login");
  await page.getByRole("tab", { name: "Email" }).click();

  await page.getByPlaceholder("you@example.com").fill("test@enex.in");
  await page.getByRole("button", { name: "Send Verification Code" }).click();
  await expect(page.getByLabel("Verification Code")).toBeVisible();

  await page.getByText("Change email").click();
  await expect(page.getByLabel("Email Address")).toBeVisible();
});

test("Resend countdown visible after sending OTP", async ({ page }) => {
  await mockOtpFlow(page);
  await page.goto("/login");
  await page.getByRole("tab", { name: "Email" }).click();

  await page.getByPlaceholder("you@example.com").fill("test@enex.in");
  await page.getByRole("button", { name: "Send Verification Code" }).click();
  await expect(page.getByLabel("Verification Code")).toBeVisible();

  await expect(page.getByText(/Resend in \d+s/)).toBeVisible();
});

test("displays error on 429 rate limit", async ({ page }) => {
  await mockOtpRateLimited(page);
  await page.goto("/login");
  await page.getByRole("tab", { name: "Email" }).click();

  await page.getByPlaceholder("you@example.com").fill("test@enex.in");
  await page.getByRole("button", { name: "Send Verification Code" }).click();

  await expect(page.getByText("Too many OTP requests")).toBeVisible();
});
