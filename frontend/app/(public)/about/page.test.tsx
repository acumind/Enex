import { describe, it, expect } from "vitest";
import { render, screen } from "@/test/test-utils";
import AboutPage, { metadata } from "./page";

describe("AboutPage", () => {
  it("renders the page heading", () => {
    render(<AboutPage />);
    expect(
      screen.getByRole("heading", { level: 1, name: "About Enex" }),
    ).toBeInTheDocument();
  });

  it("renders all section headings", () => {
    render(<AboutPage />);
    const sections = [
      "What is Enex?",
      "How It Works",
      "Scoring Methodology",
      "Evaluation Timing",
      "Data Sources",
      "Disclaimer",
    ];
    for (const heading of sections) {
      expect(screen.getByRole("heading", { name: heading })).toBeInTheDocument();
    }
  });

  it("exports metadata with title", () => {
    expect(metadata.title).toBe("About — Enex");
  });

  it("exports metadata with description", () => {
    expect(metadata.description).toBeDefined();
  });
});
