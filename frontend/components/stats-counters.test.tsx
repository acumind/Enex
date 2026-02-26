import { describe, it, expect } from "vitest";
import { render, screen } from "@/test/test-utils";
import { StatsCounters } from "./stats-counters";
import type { PlatformStatsResponse } from "@/lib/types";

const stats: PlatformStatsResponse = {
  total_predictions: 1234,
  total_predictors: 56,
  total_stocks: 789,
  avg_accuracy_pct: "65.3",
  total_evaluated: 900,
};

describe("StatsCounters", () => {
  it("renders all 4 stat cards", () => {
    render(<StatsCounters stats={stats} />);
    expect(screen.getByText("Total Predictions")).toBeInTheDocument();
    expect(screen.getByText("Total Analysts")).toBeInTheDocument();
    expect(screen.getByText("Stocks Tracked")).toBeInTheDocument();
    expect(screen.getByText("Avg Accuracy")).toBeInTheDocument();
  });

  it("formats numbers with toLocaleString", () => {
    render(<StatsCounters stats={stats} />);
    expect(screen.getByText("1,234")).toBeInTheDocument();
  });

  it("formats accuracy percentage", () => {
    render(<StatsCounters stats={stats} />);
    expect(screen.getByText("65.3%")).toBeInTheDocument();
  });

  it("shows N/A when avg_accuracy_pct is null", () => {
    render(
      <StatsCounters stats={{ ...stats, avg_accuracy_pct: null }} />,
    );
    expect(screen.getByText("N/A")).toBeInTheDocument();
  });
});
