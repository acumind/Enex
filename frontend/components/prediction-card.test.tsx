import { describe, it, expect } from "vitest";
import { render, screen } from "@/test/test-utils";
import { PredictionCard } from "./prediction-card";
import type { PredictionResponse } from "@/lib/types";

const basePrediction: PredictionResponse = {
  id: "pred-1",
  predictor_id: "pred-id-1",
  stock_id: "stock-id-1",
  target_price: "1500.50",
  price_at_prediction: "1200.00",
  prediction_date: "2025-06-01",
  target_date: "2025-12-01",
  default_eval_date: "2026-06-01",
  source_url: "https://example.com/article",
  source_type: "news_article",
  source_archive_url: null,
  raw_quote: null,
  submitted_by: null,
  extraction_method: "manual",
  ai_confidence: null,
  status: "evaluated",
  reviewed_by: null,
  reviewed_at: null,
  created_at: "2025-06-01T00:00:00Z",
  updated_at: "2025-06-01T00:00:00Z",
  upside_pct: "25.0",
};

describe("PredictionCard", () => {
  it("formats target price in en-IN locale", () => {
    render(<PredictionCard prediction={basePrediction} />);
    // en-IN formats 1500.5 as "1,500.5"
    expect(screen.getByText("1,500.5")).toBeInTheDocument();
  });

  it("shows positive upside with + sign", () => {
    render(<PredictionCard prediction={basePrediction} />);
    expect(screen.getByText("+25.0%")).toBeInTheDocument();
  });

  it("shows negative upside without + sign", () => {
    render(
      <PredictionCard
        prediction={{ ...basePrediction, upside_pct: "-10.5" }}
      />,
    );
    expect(screen.getByText("-10.5%")).toBeInTheDocument();
  });

  it("renders predictor link when provided", () => {
    render(
      <PredictionCard
        prediction={basePrediction}
        predictorName="Motilal Oswal"
        predictorSlug="motilal-oswal"
      />,
    );
    const link = screen.getByRole("link", { name: "Motilal Oswal" });
    expect(link).toHaveAttribute("href", "/predictor/motilal-oswal");
  });

  it("renders stock link when provided", () => {
    render(
      <PredictionCard prediction={basePrediction} stockSymbol="RELIANCE" />,
    );
    const link = screen.getByRole("link", { name: "RELIANCE" });
    expect(link).toHaveAttribute("href", "/stock/RELIANCE");
  });

  it("displays prediction date", () => {
    render(<PredictionCard prediction={basePrediction} />);
    expect(screen.getByText("2025-06-01")).toBeInTheDocument();
  });

  it("displays target date when present", () => {
    render(<PredictionCard prediction={basePrediction} />);
    expect(screen.getByText("Target: 2025-12-01")).toBeInTheDocument();
  });

  it("maps 'approved' status to 'pending' for OutcomeBadge", () => {
    render(
      <PredictionCard
        prediction={{ ...basePrediction, status: "approved" }}
      />,
    );
    expect(screen.getByText("Pending")).toBeInTheDocument();
  });
});
