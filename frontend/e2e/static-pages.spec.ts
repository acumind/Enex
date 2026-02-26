import { test, expect } from "@playwright/test";
import { mockPublicApiRoutes } from "./fixtures/api-routes";

test.beforeEach(async ({ page }) => {
  await mockPublicApiRoutes(page);
});

// ---------------------------------------------------------------------------
// About page
// ---------------------------------------------------------------------------

test.describe("About page", () => {
  test("renders heading", async ({ page }) => {
    await page.goto("/about");
    await expect(page.getByRole("heading", { name: "About Enex", level: 1 })).toBeVisible();
  });

  test("has correct page title", async ({ page }) => {
    await page.goto("/about");
    await expect(page).toHaveTitle(/About/);
  });

  test("renders all 6 section headings", async ({ page }) => {
    await page.goto("/about");
    const sections = [
      "What is Enex?",
      "How It Works",
      "Scoring Methodology",
      "Evaluation Timing",
      "Data Sources",
      "Disclaimer",
    ];
    for (const heading of sections) {
      await expect(page.getByRole("heading", { name: heading })).toBeVisible();
    }
  });
});

// ---------------------------------------------------------------------------
// Terms page
// ---------------------------------------------------------------------------

test.describe("Terms page", () => {
  test("renders heading", async ({ page }) => {
    await page.goto("/terms");
    await expect(page.getByRole("heading", { name: "Terms of Service", level: 1 })).toBeVisible();
  });

  test("renders all 11 section headings", async ({ page }) => {
    await page.goto("/terms");
    const sections = [
      "Acceptance of Terms",
      "What Enex Is",
      "No Investment Advice",
      "User Accounts",
      "Acceptable Use",
      "Content & Submissions",
      "Predictor Rights",
      "Intellectual Property",
      "Limitation of Liability",
      "Modifications",
      "Governing Law",
    ];
    for (const heading of sections) {
      await expect(page.getByRole("heading", { name: heading })).toBeVisible();
    }
  });

  test("shows last updated text", async ({ page }) => {
    await page.goto("/terms");
    await expect(page.getByText("Last updated")).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Privacy page
// ---------------------------------------------------------------------------

test.describe("Privacy page", () => {
  test("renders heading", async ({ page }) => {
    await page.goto("/privacy");
    await expect(page.getByRole("heading", { name: "Privacy Policy", level: 1 })).toBeVisible();
  });

  test("renders all 12 section headings", async ({ page }) => {
    await page.goto("/privacy");
    const sections = [
      "Overview",
      "Data We Collect",
      "How We Use Your Data",
      "AI & Data Processing",
      "Third-Party Services",
      "Cookies & Local Storage",
      "Data Retention",
      "Your Rights (DPDPA 2023)",
      "Data Security",
      "Children",
      "Changes to This Policy",
      "Contact",
    ];
    for (const heading of sections) {
      await expect(page.getByRole("heading", { name: heading })).toBeVisible();
    }
  });

  test("links to Anthropic privacy policy", async ({ page }) => {
    await page.goto("/privacy");
    const link = page.getByRole("link", { name: /anthropic/i });
    await expect(link).toBeVisible();
    await expect(link).toHaveAttribute("href", "https://www.anthropic.com/privacy");
  });
});

// ---------------------------------------------------------------------------
// Contact page
// ---------------------------------------------------------------------------

test.describe("Contact page", () => {
  test("renders heading", async ({ page }) => {
    await page.goto("/contact");
    await expect(page.getByRole("heading", { name: "Contact", level: 1 })).toBeVisible();
  });

  test("has hello@enex.in mailto link", async ({ page }) => {
    await page.goto("/contact");
    const link = page.getByRole("link", { name: /hello@enex\.in/ });
    await expect(link.first()).toBeVisible();
    await expect(link.first()).toHaveAttribute("href", "mailto:hello@enex.in");
  });

  test("has privacy@enex.in mailto link", async ({ page }) => {
    await page.goto("/contact");
    const link = page.getByRole("link", { name: /privacy@enex\.in/ });
    await expect(link).toBeVisible();
    await expect(link).toHaveAttribute("href", "mailto:privacy@enex.in");
  });

  test("has GitHub issues link", async ({ page }) => {
    await page.goto("/contact");
    const link = page.getByRole("link", { name: /github/i });
    await expect(link).toBeVisible();
    await expect(link).toHaveAttribute("href", /github\.com\/acumind\/Enex\/issues/);
  });
});
