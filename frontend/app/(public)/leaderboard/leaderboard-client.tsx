"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { AccuracyBadge } from "@/components/accuracy-badge";
import { api } from "@/lib/api-client";
import type { LeaderboardEntry } from "@/lib/types";

const PREDICTOR_TYPES = [
  { value: "all", label: "All" },
  { value: "individual", label: "Individual" },
  { value: "brokerage", label: "Brokerage" },
  { value: "research_firm", label: "Research Firm" },
  { value: "media_house", label: "Media" },
  { value: "influencer", label: "Influencer" },
] as const;

const SORT_OPTIONS = [
  { value: "accuracy", label: "Accuracy" },
  { value: "total_predictions", label: "Total Predictions" },
  { value: "streak_current", label: "Streak" },
] as const;

const PAGE_SIZE = 20;

export function LeaderboardClient() {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [type, setType] = useState("all");
  const [sortBy, setSortBy] = useState("accuracy");
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {
        limit: String(PAGE_SIZE + 1),
        offset: String(offset),
        sort_by: sortBy,
      };
      if (type !== "all") params.predictor_type = type;

      const data = await api.get<LeaderboardEntry[]>("/leaderboard", params);
      setHasMore(data.length > PAGE_SIZE);
      setEntries(data.slice(0, PAGE_SIZE));
    } catch {
      setEntries([]);
    } finally {
      setLoading(false);
    }
  }, [type, sortBy, offset]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleTypeChange = (value: string) => {
    setType(value);
    setOffset(0);
  };

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <Tabs value={type} onValueChange={handleTypeChange}>
          <TabsList className="flex-wrap">
            {PREDICTOR_TYPES.map((t) => (
              <TabsTrigger key={t.value} value={t.value}>
                {t.label}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>

        <Select value={sortBy} onValueChange={(v) => { setSortBy(v); setOffset(0); }}>
          <SelectTrigger>
            <SelectValue placeholder="Sort by" />
          </SelectTrigger>
          <SelectContent>
            {SORT_OPTIONS.map((s) => (
              <SelectItem key={s.value} value={s.value}>
                {s.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/50 text-left">
              <th className="px-4 py-3 font-medium">#</th>
              <th className="px-4 py-3 font-medium">Analyst</th>
              <th className="px-4 py-3 font-medium">Type</th>
              <th className="px-4 py-3 text-right font-medium">Accuracy</th>
              <th className="px-4 py-3 text-right font-medium">Hits</th>
              <th className="px-4 py-3 text-right font-medium">Misses</th>
              <th className="px-4 py-3 text-right font-medium">Partial</th>
              <th className="px-4 py-3 text-right font-medium">Total</th>
              <th className="px-4 py-3 text-right font-medium">Streak</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={9} className="px-4 py-8 text-center text-muted-foreground">
                  Loading...
                </td>
              </tr>
            ) : entries.length === 0 ? (
              <tr>
                <td colSpan={9} className="px-4 py-8 text-center text-muted-foreground">
                  No analysts match the current filters.
                </td>
              </tr>
            ) : (
              entries.map((entry, i) => (
                <tr key={entry.predictor_id} className="border-b last:border-0 hover:bg-muted/30">
                  <td className="px-4 py-3 text-muted-foreground">
                    {offset + i + 1}
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
                  <td className="px-4 py-3 text-right tabular-nums text-green-700 dark:text-green-400">
                    {entry.hits}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums text-red-700 dark:text-red-400">
                    {entry.misses}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums text-yellow-700 dark:text-yellow-400">
                    {entry.partial_hits}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums">
                    {entry.total_predictions}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums">
                    {entry.streak_current}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <Button
          variant="outline"
          size="sm"
          disabled={offset === 0}
          onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
        >
          Previous
        </Button>
        <span className="text-sm text-muted-foreground">
          Page {Math.floor(offset / PAGE_SIZE) + 1}
        </span>
        <Button
          variant="outline"
          size="sm"
          disabled={!hasMore}
          onClick={() => setOffset(offset + PAGE_SIZE)}
        >
          Next
        </Button>
      </div>
    </div>
  );
}
