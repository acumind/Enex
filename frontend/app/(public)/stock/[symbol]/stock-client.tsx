"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { OutcomeBadge } from "@/components/outcome-badge";
import { WatchlistButton } from "@/components/watchlist-button";
import { api } from "@/lib/api-client";
import type {
  PaginatedResponse,
  PredictionResponse,
  StockResponse,
} from "@/lib/types";

interface Props {
  stock: StockResponse;
  symbol: string;
}

export function StockClient({ stock, symbol }: Props) {
  const [predictions, setPredictions] = useState<PredictionResponse[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchPredictions = useCallback(
    async (nextCursor?: string) => {
      setLoading(true);
      try {
        const params: Record<string, string> = { limit: "20" };
        if (nextCursor) params.cursor = nextCursor;
        const data = await api.get<PaginatedResponse<PredictionResponse>>(
          `/stocks/${symbol}/predictions`,
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
    [symbol]
  );

  useEffect(() => {
    fetchPredictions();
  }, [fetchPredictions]);

  // Simple consensus from predictions
  const bullish = predictions.filter(
    (p) => parseFloat(p.upside_pct) > 0
  ).length;
  const bearish = predictions.filter(
    (p) => parseFloat(p.upside_pct) < 0
  ).length;

  return (
    <div className="space-y-8">
      {/* Stock Info Header */}
      <div>
        <div className="flex items-center gap-3">
          <h1 className="text-3xl font-bold">{stock.name}</h1>
          <Badge variant="outline" className="font-mono">
            {stock.symbol}
          </Badge>
          <WatchlistButton stockId={stock.id} />
        </div>
        <div className="mt-2 flex flex-wrap gap-3 text-sm text-muted-foreground">
          <span>{stock.exchange}</span>
          {stock.sector && <span>{stock.sector}</span>}
          {stock.industry && <span>{stock.industry}</span>}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Current Price
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold tabular-nums">
              {stock.current_price
                ? `₹${parseFloat(stock.current_price).toLocaleString("en-IN")}`
                : "N/A"}
            </p>
            {stock.price_updated_at && (
              <p className="text-xs text-muted-foreground">
                Updated: {new Date(stock.price_updated_at).toLocaleDateString()}
              </p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Market Cap
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold tabular-nums">
              {stock.market_cap
                ? `₹${(stock.market_cap / 10000000).toFixed(0)} Cr`
                : "N/A"}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Consensus
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4 text-sm">
              <span className="text-green-700 dark:text-green-400">
                {bullish} Bullish
              </span>
              <span className="text-red-700 dark:text-red-400">
                {bearish} Bearish
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Prediction List */}
      <div>
        <h2 className="mb-4 text-xl font-semibold">Predictions</h2>
        {loading && predictions.length === 0 ? (
          <p className="text-muted-foreground">Loading predictions...</p>
        ) : predictions.length === 0 ? (
          <p className="text-muted-foreground">
            No predictions tracked for this stock yet.
          </p>
        ) : (
          <div className="space-y-2">
            <div className="overflow-x-auto rounded-lg border">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50 text-left">
                    <th className="px-4 py-3 font-medium">Date</th>
                    <th className="px-4 py-3 font-medium">Predictor</th>
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
                        {p.predictor_slug ? (
                          <Link
                            href={`/predictor/${p.predictor_slug}`}
                            className="text-primary underline-offset-4 hover:underline"
                          >
                            {p.predictor_name || p.predictor_id.slice(0, 8)}
                          </Link>
                        ) : (
                          p.predictor_id.slice(0, 8)
                        )}
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums">
                        ₹
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
