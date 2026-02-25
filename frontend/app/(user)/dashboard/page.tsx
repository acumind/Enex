"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Eye, Bell, UserCheck } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api-client";
import type {
  PaginatedResponse,
  WatchlistItemEnriched,
  FollowItemEnriched,
  UnreadCountResponse,
} from "@/lib/types";

export default function DashboardPage() {
  const { user, isAuthenticated } = useAuth();
  const [watchlistCount, setWatchlistCount] = useState(0);
  const [followingCount, setFollowingCount] = useState(0);
  const [unreadCount, setUnreadCount] = useState(0);
  const [recentWatchlist, setRecentWatchlist] = useState<
    WatchlistItemEnriched[]
  >([]);
  const [recentFollowing, setRecentFollowing] = useState<
    FollowItemEnriched[]
  >([]);

  useEffect(() => {
    if (!isAuthenticated) return;

    api
      .get<PaginatedResponse<WatchlistItemEnriched>>("/watchlist", {
        limit: "5",
      })
      .then((data) => {
        setRecentWatchlist(data.items);
        // Approximate count from items returned (could be more)
        setWatchlistCount(data.items.length + (data.has_more ? 1 : 0));
      })
      .catch(() => {});

    api
      .get<PaginatedResponse<FollowItemEnriched>>("/following", { limit: "5" })
      .then((data) => {
        setRecentFollowing(data.items);
        setFollowingCount(data.items.length + (data.has_more ? 1 : 0));
      })
      .catch(() => {});

    api
      .get<UnreadCountResponse>("/notifications/unread-count")
      .then((data) => setUnreadCount(data.count))
      .catch(() => {});
  }, [isAuthenticated]);

  return (
    <main className="mx-auto max-w-6xl px-4 py-8">
      <h1 className="mb-2 text-3xl font-bold">
        Welcome{user?.name ? `, ${user.name}` : ""}
      </h1>
      <p className="mb-8 text-muted-foreground">
        Your Enex dashboard — track predictions, follow analysts, and stay
        informed.
      </p>

      {/* Summary Cards */}
      <div className="mb-8 grid gap-4 sm:grid-cols-3">
        <Link href="/watchlist">
          <Card className="transition-colors hover:bg-muted/30">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Watchlist
              </CardTitle>
              <Eye className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold tabular-nums">
                {watchlistCount}
              </p>
              <p className="text-xs text-muted-foreground">stocks tracked</p>
            </CardContent>
          </Card>
        </Link>
        <Link href="/following">
          <Card className="transition-colors hover:bg-muted/30">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Following
              </CardTitle>
              <UserCheck className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold tabular-nums">
                {followingCount}
              </p>
              <p className="text-xs text-muted-foreground">
                predictors followed
              </p>
            </CardContent>
          </Card>
        </Link>
        <Link href="/notifications">
          <Card className="transition-colors hover:bg-muted/30">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Notifications
              </CardTitle>
              <Bell className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold tabular-nums">{unreadCount}</p>
              <p className="text-xs text-muted-foreground">unread</p>
            </CardContent>
          </Card>
        </Link>
      </div>

      {/* Quick Links */}
      <div className="mb-8 grid gap-4 sm:grid-cols-2">
        {/* Recent Watchlist */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recent Watchlist</CardTitle>
          </CardHeader>
          <CardContent>
            {recentWatchlist.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No stocks in your watchlist yet.
              </p>
            ) : (
              <ul className="space-y-2">
                {recentWatchlist.map((item) => (
                  <li key={item.stock_id}>
                    <Link
                      href={`/stock/${item.stock_symbol}`}
                      className="flex items-center justify-between text-sm hover:text-primary"
                    >
                      <span>
                        <span className="font-mono">{item.stock_symbol}</span>{" "}
                        <span className="text-muted-foreground">
                          {item.stock_name}
                        </span>
                      </span>
                      {item.stock_current_price && (
                        <span className="tabular-nums text-muted-foreground">
                          ₹
                          {parseFloat(item.stock_current_price).toLocaleString(
                            "en-IN",
                          )}
                        </span>
                      )}
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        {/* Recent Following */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recently Followed</CardTitle>
          </CardHeader>
          <CardContent>
            {recentFollowing.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                Not following any predictors yet.
              </p>
            ) : (
              <ul className="space-y-2">
                {recentFollowing.map((item) => (
                  <li key={item.predictor_id}>
                    <Link
                      href={`/predictor/${item.predictor_slug}`}
                      className="text-sm hover:text-primary"
                    >
                      {item.predictor_name}
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="flex flex-wrap gap-3">
        <Link
          href="/submit"
          className="rounded-md border px-4 py-2 text-sm transition-colors hover:bg-muted/50"
        >
          Submit a Prediction
        </Link>
        <Link
          href="/suggest"
          className="rounded-md border px-4 py-2 text-sm transition-colors hover:bg-muted/50"
        >
          Suggest a Prediction
        </Link>
        <Link
          href="/leaderboard"
          className="rounded-md border px-4 py-2 text-sm transition-colors hover:bg-muted/50"
        >
          View Leaderboard
        </Link>
      </div>
    </main>
  );
}
