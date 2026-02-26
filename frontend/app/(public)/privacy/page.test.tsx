import { describe, it, expect } from "vitest";
import { render, screen } from "@/test/test-utils";
import PrivacyPage, { metadata } from "./page";

describe("PrivacyPage", () => {
  it("renders the page heading", () => {
    render(<PrivacyPage />);
    expect(
      screen.getByRole("heading", { level: 1, name: "Privacy Policy" }),
    ).toBeInTheDocument();
  });

  it("renders the DPDPA section", () => {
    render(<PrivacyPage />);
    expect(
      screen.getByRole("heading", { name: "8. Your Rights (DPDPA 2023)" }),
    ).toBeInTheDocument();
  });

  it("renders all section headings", () => {
    render(<PrivacyPage />);
    const sections = [
      "1. Overview",
      "2. Data We Collect",
      "3. How We Use Your Data",
      "4. AI & Data Processing",
      "5. Third-Party Services",
      "6. Cookies & Local Storage",
      "7. Data Retention",
      "8. Your Rights (DPDPA 2023)",
      "9. Data Security",
      "10. Children",
      "11. Changes to This Policy",
      "12. Contact",
    ];
    for (const heading of sections) {
      expect(screen.getByRole("heading", { name: heading })).toBeInTheDocument();
    }
  });

  it("exports metadata with title", () => {
    expect(metadata.title).toBe("Privacy Policy — Enex");
  });

  it("exports metadata with description", () => {
    expect(metadata.description).toContain("DPDPA");
  });
});
