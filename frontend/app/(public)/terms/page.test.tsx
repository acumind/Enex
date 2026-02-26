import { describe, it, expect } from "vitest";
import { render, screen } from "@/test/test-utils";
import TermsPage, { metadata } from "./page";

describe("TermsPage", () => {
  it("renders the page heading", () => {
    render(<TermsPage />);
    expect(
      screen.getByRole("heading", { level: 1, name: "Terms of Service" }),
    ).toBeInTheDocument();
  });

  it("renders all 11 section headings", () => {
    render(<TermsPage />);
    const sections = [
      "1. Acceptance of Terms",
      "2. What Enex Is",
      "3. No Investment Advice",
      "4. User Accounts",
      "5. Acceptable Use",
      "6. Content & Submissions",
      "7. Predictor Rights",
      "8. Intellectual Property",
      "9. Limitation of Liability",
      "10. Modifications",
      "11. Governing Law",
    ];
    for (const heading of sections) {
      expect(screen.getByRole("heading", { name: heading })).toBeInTheDocument();
    }
  });

  it("exports metadata with title", () => {
    expect(metadata.title).toBe("Terms of Service — Enex");
  });

  it("exports metadata with description", () => {
    expect(metadata.description).toBeDefined();
  });
});
