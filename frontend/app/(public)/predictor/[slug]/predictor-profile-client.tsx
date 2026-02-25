"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { OutcomeBadge } from "@/components/outcome-badge";
import { AccuracyBadge } from "@/components/accuracy-badge";
import { FollowButton } from "@/components/follow-button";
import { api } from "@/lib/api-client";
import type {
  PaginatedResponse,
  PredictionResponse,
  PredictorResponse,
  ScorecardResponse,
} from "@/lib/types";

interface Props {
  predictor: PredictorResponse;
  scorecard: ScorecardResponse | null;
  slug: string;
}

export function PredictorProfileClient({
  predictor,
  scorecard,
  slug,
}: Props) {
  const [predictions, setPredictions] = useState<PredictionResponse[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [members, setMembers] = useState<PredictorResponse[]>([]);

  const fetchPredictions = useCallback(
    async (nextCursor?: string) => {
      setLoading(true);
      try {
        const params: Record<string, string> = { limit: "20" };
        if (nextCursor) params.cursor = nextCursor;
        const data = await api.get<PaginatedResponse<PredictionResponse>>(
          `/predictors/${slug}/predictions`,
          params
        );
        setPredictions((prev) =>
          nextCursor ? [...prev, ...data.items] : data.items
        );
        setCursor(data.next_cursor);
        setHasMore(data.has_more);
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    },
    [slug]
  );

  useEffect(() => {
    fetchPredictions();
  }, [fetchPredictions]);

  // Load members for firm-type predictors
  useEffect(() => {
    const orgTypes = ["brokerage", "research_firm", "media_house"];
    if (!orgTypes.includes(predictor.type)) return;
    api
      .get<PredictorResponse[]>(`/predictors/${slug}/members`)
      .then(setMembers)
      .catch(() => {});
  }, [predictor.type, slug]);

  const sectorData = scorecard
    ? Object.entries(scorecard.sector_accuracy).map(([sector, acc]) => ({
        sector,
        accuracy: acc,
      }))
    : [];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-3">
          <h1 className="text-3xl font-bold">{predictor.name}</h1>
          {predictor.is_verified && (
            <Badge variant="secondary">Verified</Badge>
          )}
          <FollowButton predictorId={predictor.id} />
        </div>
        <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
          <Badge variant="outline" className="capitalize">
            {predictor.type.replace("_", " ")}
          </Badge>
          {predictor.designation && <span>{predictor.designation}</span>}
        </div>
        {predictor.bio && (
          <p className="mt-2 max-w-3xl text-muted-foreground">
            {predictor.bio}
          </p>
        )}
      </div>

      {/* Scorecard */}
      {scorecard && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Accuracy
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl">
                <AccuracyBadge value={scorecard.accuracy_pct} />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Record
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-3 text-sm">
                <span className="text-green-700 dark:text-green-400">
                  {scorecard.hits} hits
                </span>
                <span className="text-yellow-700 dark:text-yellow-400">
                  {scorecard.partial_hits} partial
                </span>
                <span className="text-red-700 dark:text-red-400">
                  {scorecard.misses} misses
                </span>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                {scorecard.total_predictions} total predictions
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Current Streak
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold tabular-nums">
                {scorecard.streak_current}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Avg Deviation
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-semibold tabular-nums">
                {scorecard.avg_deviation_pct
                  ? `${parseFloat(scorecard.avg_deviation_pct).toFixed(1)}%`
                  : "N/A"}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Sector accuracy chart */}
      {sectorData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Sector Accuracy</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={sectorData}>
                <XAxis
                  dataKey="sector"
                  tick={{ fontSize: 12 }}
                  interval={0}
                  angle={-30}
                  textAnchor="end"
                  height={80}
                />
                <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} />
                <Tooltip
                  formatter={(value) => [`${Number(value).toFixed(1)}%`, "Accuracy"]}
                />
                <Bar
                  dataKey="accuracy"
                  fill="hsl(var(--chart-1))"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Members (for firms) */}
      {members.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Team Members</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {members.map((m) => (
                <Link
                  key={m.id}
                  href={`/predictor/${m.slug}`}
                  className="rounded-md border p-3 text-sm hover:bg-muted/50"
                >
                  <p className="font-medium">{m.name}</p>
                  {m.designation && (
                    <p className="text-xs text-muted-foreground">
                      {m.designation}
                    </p>
                  )}
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Prediction History */}
      <div>
        <h2 className="mb-4 text-xl font-semibold">Prediction History</h2>
        {loading && predictions.length === 0 ? (
          <p className="text-muted-foreground">Loading predictions...</p>
        ) : predictions.length === 0 ? (
          <p className="text-muted-foreground">No predictions yet.</p>
        ) : (
          <div className="space-y-2">
            <div className="overflow-x-auto rounded-lg border">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50 text-left">
                    <th className="px-4 py-3 font-medium">Date</th>
                    <th className="px-4 py-3 font-medium">Stock</th>
                    <th className="px-4 py-3 text-right font-medium">
                      Target
                    </th>
                    <th className="px-4 py-3 text-right font-medium">
                      Upside
                    </th>
                    <th className="px-4 py-3 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {predictions.map((p) => (
                    <tr
                      key={p.id}
                      className="border-b last:border-0 hover:bg-muted/30"
                    >
                      <td className="px-4 py-3 text-muted-foreground">
                        {p.prediction_date}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        {p.stock_symbol ? (
                          <Link
                            href={`/stock/${p.stock_symbol}`}
                            className="font-mono text-primary underline-offset-4 hover:underline"
                          >
                            {p.stock_symbol}
                          </Link>
                        ) : (
                          <span className="font-mono text-xs">
                            {p.stock_id.slice(0, 8)}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums">
                        {parseFloat(p.target_price).toLocaleString("en-IN")}
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums">
                        {parseFloat(p.upside_pct) >= 0 ? "+" : ""}
                        {parseFloat(p.upside_pct).toFixed(1)}%
                      </td>
                      <td className="px-4 py-3">
                        <OutcomeBadge status={p.status === "approved" ? "pending" : p.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {hasMore && (
              <div className="flex justify-center pt-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => cursor && fetchPredictions(cursor)}
                  disabled={loading}
                >
                  {loading ? "Loading..." : "Load more"}
                </Button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
