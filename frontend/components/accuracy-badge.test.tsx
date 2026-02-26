import { describe, it, expect } from "vitest";
import { render, screen } from "@/test/test-utils";
import { AccuracyBadge } from "./accuracy-badge";

describe("AccuracyBadge", () => {
  it("renders 'N/A' when value is null", () => {
    render(<AccuracyBadge value={null} />);
    expect(screen.getByText("N/A")).toBeInTheDocument();
  });

  it("formats value with one decimal (85.3 → '85.3%')", () => {
    render(<AccuracyBadge value="85.3" />);
    expect(screen.getByText("85.3%")).toBeInTheDocument();
  });

  it("applies green color for ≥70", () => {
    const { container } = render(<AccuracyBadge value="75.0" />);
    const span = container.querySelector("span");
    expect(span?.className).toContain("text-green-700");
  });

  it("applies yellow color for ≥40 and <70", () => {
    const { container } = render(<AccuracyBadge value="55.0" />);
    const span = container.querySelector("span");
    expect(span?.className).toContain("text-yellow-700");
  });

  it("applies red color for <40", () => {
    const { container } = render(<AccuracyBadge value="25.0" />);
    const span = container.querySelector("span");
    expect(span?.className).toContain("text-red-700");
  });

  it("handles boundary at exactly 70", () => {
    const { container } = render(<AccuracyBadge value="70" />);
    const span = container.querySelector("span");
    expect(span?.className).toContain("text-green-700");
  });

  it("handles boundary at exactly 40", () => {
    const { container } = render(<AccuracyBadge value="40" />);
    const span = container.querySelector("span");
    expect(span?.className).toContain("text-yellow-700");
  });
});
