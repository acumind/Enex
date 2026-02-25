"use client";

import { useCallback, useEffect, useState } from "react";
import { Eye, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth-context";
import { api, ApiClientError } from "@/lib/api-client";
import type { WatchlistCheckResponse } from "@/lib/types";

interface Props {
  stockId: string;
}

export function WatchlistButton({ stockId }: Props) {
  const { isAuthenticated } = useAuth();
  const [watching, setWatching] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) return;
    api
      .get<WatchlistCheckResponse>(`/watchlist/check/${stockId}`)
      .then((data) => setWatching(data.watching))
      .catch(() => {});
  }, [isAuthenticated, stockId]);

  const toggle = useCallback(async () => {
    setLoading(true);
    try {
      if (watching) {
        await api.delete(`/watchlist/${stockId}`);
        setWatching(false);
      } else {
        await api.post("/watchlist", { stock_id: stockId });
        setWatching(true);
      }
    } catch (err) {
      if (err instanceof ApiClientError && err.status === 409) {
        setWatching(true);
      }
    } finally {
      setLoading(false);
    }
  }, [watching, stockId]);

  if (!isAuthenticated) return null;

  return (
    <Button
      variant={watching ? "secondary" : "outline"}
      size="sm"
      onClick={toggle}
      disabled={loading}
    >
      {watching ? (
        <>
          <Eye className="mr-1.5 h-4 w-4" />
          Watching
        </>
      ) : (
        <>
          <EyeOff className="mr-1.5 h-4 w-4" />
          Watch
        </>
      )}
    </Button>
  );
}
