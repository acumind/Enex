"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api-client";
import type { PaginatedResponse, WatchlistItemEnriched } from "@/lib/types";

export default function WatchlistPage() {
  const { isAuthenticated } = useAuth();
  const [items, setItems] = useState<WatchlistItemEnriched[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchItems = useCallback(async (nextCursor?: string) => {
    setLoading(true);
    try {
      const params: Record<string, string> = { limit: "20" };
      if (nextCursor) params.cursor = nextCursor;
      const data = await api.get<PaginatedResponse<WatchlistItemEnriched>>(
        "/watchlist",
        params,
      );
      setItems((prev) => (nextCursor ? [...prev, ...data.items] : data.items));
      setCursor(data.next_cursor);
      setHasMore(data.has_more);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) fetchItems();
  }, [isAuthenticated, fetchItems]);

  const removeItem = useCallback(
    async (stockId: string) => {
      try {
        await api.delete(`/watchlist/${stockId}`);
        setItems((prev) => prev.filter((i) => i.stock_id !== stockId));
      } catch {
        // ignore
      }
    },
    [],
  );

  return (
    <main className="mx-auto max-w-4xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold">My Watchlist</h1>
      {loading && items.length === 0 ? (
        <p className="text-muted-foreground">Loading...</p>
      ) : items.length === 0 ? (
        <p className="text-muted-foreground">
          No stocks in your watchlist yet. Visit a stock page to add one.
        </p>
      ) : (
        <div className="space-y-2">
          <div className="overflow-x-auto rounded-lg border">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50 text-left">
                  <th className="px-4 py-3 font-medium">Symbol</th>
                  <th className="px-4 py-3 font-medium">Name</th>
                  <th className="px-4 py-3 font-medium">Sector</th>
                  <th className="px-4 py-3 text-right font-medium">Price</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr
                    key={item.stock_id}
                    className="border-b last:border-0 hover:bg-muted/30"
                  >
                    <td className="px-4 py-3">
                      <Link
                        href={`/stock/${item.stock_symbol}`}
                        className="font-mono text-primary underline-offset-4 hover:underline"
                      >
                        {item.stock_symbol}
                      </Link>
                    </td>
                    <td className="px-4 py-3">{item.stock_name}</td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {item.stock_sector || "—"}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      {item.stock_current_price
                        ? `₹${parseFloat(item.stock_current_price).toLocaleString("en-IN")}`
                        : "N/A"}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeItem(item.stock_id)}
                      >
                        <Trash2 className="h-4 w-4 text-muted-foreground" />
                      </Button>
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
                onClick={() => cursor && fetchItems(cursor)}
                disabled={loading}
              >
                {loading ? "Loading..." : "Load more"}
              </Button>
            </div>
          )}
        </div>
      )}
    </main>
  );
}
