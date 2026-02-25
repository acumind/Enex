import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "About — Enex",
  description:
    "Learn how Enex tracks analyst predictions for Indian equity markets and scores them for accuracy.",
};

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="mb-8 text-3xl font-bold">About Enex</h1>

      <div className="space-y-8 text-sm leading-relaxed text-foreground/90">
        <section>
          <h2 className="mb-3 text-xl font-semibold">What is Enex?</h2>
          <p>
            Enex is an Analyst Prediction Tracker for the Indian equity market.
            We collect stock price target predictions made by analysts,
            brokerage firms, research houses, and media personalities, then
            track them against actual market outcomes to rank predictors by
            accuracy.
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold">How It Works</h2>
          <ol className="ml-4 list-decimal space-y-2">
            <li>
              <strong>Prediction Ingestion</strong> — Predictions are submitted
              by users, suggested via a lightweight form, or bulk-imported by
              admins. AI-assisted extraction can parse predictions from article
              URLs.
            </li>
            <li>
              <strong>Review &amp; Approval</strong> — Every prediction goes
              through a moderator review queue before it becomes part of the
              public record.
            </li>
            <li>
              <strong>Daily Price Fetching</strong> — Closing prices are fetched
              daily for all tracked stocks.
            </li>
            <li>
              <strong>Automated Evaluation</strong> — On or after the target
              date (or 12 months from prediction date if none was given), the
              system evaluates each prediction against actual prices.
            </li>
            <li>
              <strong>Scorecard Generation</strong> — Per-predictor scorecards
              are computed: accuracy rate, hit/miss counts, streak, sector
              breakdown, and average deviation.
            </li>
          </ol>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold">Scoring Methodology</h2>
          <p>
            Each prediction is classified as one of three outcomes based on the
            highest (for bullish) or lowest (for bearish) price reached during
            the prediction window:
          </p>
          <ul className="ml-4 mt-2 list-disc space-y-1">
            <li>
              <strong>Hit</strong> — The target price was reached or exceeded.
            </li>
            <li>
              <strong>Partial Hit</strong> — The price came within 5% of the
              target but did not fully reach it.
            </li>
            <li>
              <strong>Miss</strong> — The price did not come within 5% of the
              target.
            </li>
          </ul>
          <p className="mt-2">
            Accuracy is computed as:{" "}
            <code className="rounded bg-muted px-1 py-0.5">
              (hits + partial_hits &times; 0.5) / total_evaluated &times; 100
            </code>
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold">Evaluation Timing</h2>
          <p>
            If a prediction specifies a target date, that date is used. If no
            target date is provided, the default evaluation window is 12 months
            from the prediction date. Evaluations run daily at 23:30 IST.
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold">Data Sources</h2>
          <p>
            Predictions are sourced from public interviews, news articles,
            research reports, social media posts, podcasts, and blogs. Each
            prediction links back to its original source. We use the Wayback
            Machine to archive source URLs where possible.
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold">Disclaimer</h2>
          <p className="text-muted-foreground">
            Enex is not a financial advisory service. All information is
            provided for informational and educational purposes only. Past
            prediction accuracy does not guarantee future results. Always do
            your own research before making investment decisions.
          </p>
        </section>
      </div>
    </div>
  );
}
