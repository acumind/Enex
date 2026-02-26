import { describe, it, expect } from "vitest";
import { render, screen } from "@/test/test-utils";
import ContactPage, { metadata } from "./page";

describe("ContactPage", () => {
  it("renders the page heading", () => {
    render(<ContactPage />);
    expect(
      screen.getByRole("heading", { level: 1, name: "Contact" }),
    ).toBeInTheDocument();
  });

  it("renders email links to hello@enex.in", () => {
    render(<ContactPage />);
    const emailLinks = screen.getAllByRole("link", { name: "hello@enex.in" });
    expect(emailLinks.length).toBeGreaterThanOrEqual(1);
    expect(emailLinks[0]).toHaveAttribute("href", "mailto:hello@enex.in");
  });

  it("renders email link to privacy@enex.in", () => {
    render(<ContactPage />);
    const link = screen.getByRole("link", { name: "privacy@enex.in" });
    expect(link).toHaveAttribute("href", "mailto:privacy@enex.in");
  });

  it("renders GitHub link", () => {
    render(<ContactPage />);
    const link = screen.getByRole("link", { name: "GitHub repository" });
    expect(link).toHaveAttribute(
      "href",
      "https://github.com/acumind/Enex/issues",
    );
  });

  it("exports metadata with title", () => {
    expect(metadata.title).toBe("Contact — Enex");
  });

  it("exports metadata with description", () => {
    expect(metadata.description).toBeDefined();
  });
});
