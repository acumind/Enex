"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api-client";
import type { NotificationResponse, PaginatedResponse } from "@/lib/types";

export default function NotificationsPage() {
  const { isAuthenticated } = useAuth();
  const router = useRouter();
  const [items, setItems] = useState<NotificationResponse[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchItems = useCallback(async (nextCursor?: string) => {
    setLoading(true);
    try {
      const params: Record<string, string> = { limit: "20" };
      if (nextCursor) params.cursor = nextCursor;
      const data = await api.get<PaginatedResponse<NotificationResponse>>(
        "/notifications",
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

  const markAllRead = useCallback(async () => {
    await api.post("/notifications/read-all").catch(() => {});
    setItems((prev) => prev.map((n) => ({ ...n, is_read: true })));
  }, []);

  const handleClick = useCallback(
    async (n: NotificationResponse) => {
      if (!n.is_read) {
        await api.post(`/notifications/${n.id}/read`).catch(() => {});
        setItems((prev) =>
          prev.map((item) =>
            item.id === n.id ? { ...item, is_read: true } : item,
          ),
        );
      }
      if (n.data.stock_symbol) {
        router.push(`/stock/${n.data.stock_symbol}`);
      } else if (n.data.predictor_slug) {
        router.push(`/predictor/${n.data.predictor_slug}`);
      }
    },
    [router],
  );

  return (
    <main className="mx-auto max-w-4xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Notifications</h1>
        <Button variant="outline" size="sm" onClick={markAllRead}>
          Mark all as read
        </Button>
      </div>
      {loading && items.length === 0 ? (
        <p className="text-muted-foreground">Loading...</p>
      ) : items.length === 0 ? (
        <p className="text-muted-foreground">No notifications yet.</p>
      ) : (
        <div className="space-y-2">
          {items.map((n) => (
            <button
              key={n.id}
              onClick={() => handleClick(n)}
              className={`block w-full rounded-lg border p-4 text-left transition-colors hover:bg-muted/50 ${
                !n.is_read ? "border-primary/20 bg-muted/20" : ""
              }`}
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-medium">{n.title}</p>
                  {n.message && (
                    <p className="mt-1 text-sm text-muted-foreground">
                      {n.message}
                    </p>
                  )}
                </div>
                {!n.is_read && (
                  <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-primary" />
                )}
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                {new Date(n.created_at).toLocaleString()}
              </p>
            </button>
          ))}
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
