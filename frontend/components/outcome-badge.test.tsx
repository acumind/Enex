import { describe, it, expect } from "vitest";
import { render, screen } from "@/test/test-utils";
import { OutcomeBadge } from "./outcome-badge";

describe("OutcomeBadge", () => {
  it("renders 'Hit' for status=hit", () => {
    render(<OutcomeBadge status="hit" />);
    expect(screen.getByText("Hit")).toBeInTheDocument();
  });

  it("renders 'Partial' for status=partial_hit", () => {
    render(<OutcomeBadge status="partial_hit" />);
    expect(screen.getByText("Partial")).toBeInTheDocument();
  });

  it("renders 'Miss' for status=miss", () => {
    render(<OutcomeBadge status="miss" />);
    expect(screen.getByText("Miss")).toBeInTheDocument();
  });

  it("renders 'Pending' for status=pending", () => {
    render(<OutcomeBadge status="pending" />);
    expect(screen.getByText("Pending")).toBeInTheDocument();
  });

  it("renders 'Expired' for status=expired", () => {
    render(<OutcomeBadge status="expired" />);
    expect(screen.getByText("Expired")).toBeInTheDocument();
  });

  it("falls back to 'Pending' for unknown status", () => {
    render(<OutcomeBadge status="unknown_thing" />);
    expect(screen.getByText("Pending")).toBeInTheDocument();
  });
});
