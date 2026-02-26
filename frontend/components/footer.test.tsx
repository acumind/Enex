import { describe, it, expect } from "vitest";
import { render, screen } from "@/test/test-utils";
import { Footer } from "./footer";

describe("Footer", () => {
  it("renders Leaderboard link", () => {
    render(<Footer />);
    const link = screen.getByRole("link", { name: "Leaderboard" });
    expect(link).toHaveAttribute("href", "/leaderboard");
  });

  it("renders About link", () => {
    render(<Footer />);
    const link = screen.getByRole("link", { name: "About" });
    expect(link).toHaveAttribute("href", "/about");
  });

  it("renders Terms link", () => {
    render(<Footer />);
    const link = screen.getByRole("link", { name: "Terms" });
    expect(link).toHaveAttribute("href", "/terms");
  });

  it("renders Privacy link", () => {
    render(<Footer />);
    const link = screen.getByRole("link", { name: "Privacy" });
    expect(link).toHaveAttribute("href", "/privacy");
  });

  it("renders Contact link", () => {
    render(<Footer />);
    const link = screen.getByRole("link", { name: "Contact" });
    expect(link).toHaveAttribute("href", "/contact");
  });

  it("renders disclaimer text", () => {
    render(<Footer />);
    expect(
      screen.getByText(/not financial advice/i),
    ).toBeInTheDocument();
  });

  it("renders copyright with current year", () => {
    render(<Footer />);
    const year = new Date().getFullYear();
    expect(screen.getByText(`© ${year} Enex`)).toBeInTheDocument();
  });
});
