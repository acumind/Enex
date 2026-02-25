import Link from "next/link";
import { Button } from "@/components/ui/button";
import { AccuracyBadge } from "@/components/accuracy-badge";
import { PredictionCard } from "@/components/prediction-card";
import { StatsCounters } from "@/components/stats-counters";
import type {
  LeaderboardEntry,
  PaginatedResponse,
  PlatformStatsResponse,
  PredictionResponse,
} from "@/lib/types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function fetchJSON<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      next: { revalidate: 60 },
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export default async function HomePage() {
  const [predictions, leaderboard, stats] = await Promise.all([
    fetchJSON<PaginatedResponse<PredictionResponse>>(
      "/predictions/recent?limit=6"
    ),
    fetchJSON<LeaderboardEntry[]>("/leaderboard?limit=5"),
    fetchJSON<PlatformStatsResponse>("/stats"),
  ]);

  return (
    <div className="mx-auto max-w-6xl px-4 py-12">
      {/* Hero */}
      <section className="mb-16 text-center">
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
          Who Really Gets the Market Right?
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-lg text-muted-foreground">
          We track stock price predictions from analysts, brokerages, and media
          houses across Indian markets &mdash; then score them against real
          outcomes. Transparent, data-driven accountability.
        </p>
        <div className="mt-6 flex items-center justify-center gap-3">
          <Button asChild size="lg">
            <Link href="/leaderboard">View Leaderboard</Link>
          </Button>
          <Button asChild size="lg" variant="outline">
            <Link href="/predictions">Browse Predictions</Link>
          </Button>
        </div>
      </section>

      {/* Stats Counters */}
      {stats && (
        <section className="mb-16">
          <StatsCounters stats={stats} />
        </section>
      )}

      {/* Recent Predictions */}
      {predictions && predictions.items.length > 0 && (
        <section className="mb-16">
          <h2 className="mb-6 text-2xl font-semibold">Recent Predictions</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {predictions.items.map((p) => (
              <PredictionCard key={p.id} prediction={p} />
            ))}
          </div>
        </section>
      )}

      {/* How It Works */}
      <section className="mb-16">
        <h2 className="mb-8 text-center text-2xl font-semibold">
          How It Works
        </h2>
        <div className="grid gap-8 sm:grid-cols-3">
          <div className="text-center">
            <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground font-bold">
              1
            </div>
            <h3 className="mb-1 font-semibold">Predictions Are Logged</h3>
            <p className="text-sm text-muted-foreground">
              When an analyst or media house publishes a stock price target, we
              capture it with a source link and timestamp.
            </p>
          </div>
          <div className="text-center">
            <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground font-bold">
              2
            </div>
            <h3 className="mb-1 font-semibold">Markets Do Their Thing</h3>
            <p className="text-sm text-muted-foreground">
              We wait for the target date or evaluation window to pass, then
              compare the predicted price against actual market data.
            </p>
          </div>
          <div className="text-center">
            <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground font-bold">
              3
            </div>
            <h3 className="mb-1 font-semibold">Accuracy Is Scored</h3>
            <p className="text-sm text-muted-foreground">
              Each prediction is marked as a hit, miss, or partial hit.
              Analysts are ranked on a public leaderboard by accuracy.
            </p>
          </div>
        </div>
      </section>

      {/* Top 5 Leaderboard Preview */}
      {leaderboard && leaderboard.length > 0 && (
        <section>
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-2xl font-semibold">Top Analysts</h2>
            <Link
              href="/leaderboard"
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              View all &rarr;
            </Link>
          </div>
          <div className="overflow-x-auto rounded-lg border">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50 text-left">
                  <th className="px-4 py-3 font-medium">#</th>
                  <th className="px-4 py-3 font-medium">Analyst</th>
                  <th className="px-4 py-3 font-medium">Type</th>
                  <th className="px-4 py-3 text-right font-medium">
                    Accuracy
                  </th>
                  <th className="px-4 py-3 text-right font-medium">
                    Predictions
                  </th>
                  <th className="px-4 py-3 text-right font-medium">Streak</th>
                </tr>
              </thead>
              <tbody>
                {leaderboard.map((entry, i) => (
                  <tr key={entry.predictor_id} className="border-b last:border-0">
                    <td className="px-4 py-3 text-muted-foreground">
                      {i + 1}
                    </td>
                    <td className="px-4 py-3">
                      <Link
                        href={`/predictor/${entry.predictor_slug}`}
                        className="font-medium hover:underline"
                      >
                        {entry.predictor_name}
                      </Link>
                    </td>
                    <td className="px-4 py-3 capitalize text-muted-foreground">
                      {entry.predictor_type.replace("_", " ")}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <AccuracyBadge value={entry.accuracy_pct} />
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      {entry.total_predictions}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      {entry.streak_current}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
