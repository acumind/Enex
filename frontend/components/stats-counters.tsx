import { BarChart3, Target, TrendingUp, Users } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import type { PlatformStatsResponse } from "@/lib/types";

const items = [
  { key: "total_predictions", label: "Total Predictions", icon: Target },
  { key: "total_predictors", label: "Total Analysts", icon: Users },
  { key: "total_stocks", label: "Stocks Tracked", icon: TrendingUp },
  { key: "avg_accuracy_pct", label: "Avg Accuracy", icon: BarChart3 },
] as const;

export function StatsCounters({ stats }: { stats: PlatformStatsResponse }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {items.map(({ key, label, icon: Icon }) => {
        const raw = stats[key];
        const display =
          key === "avg_accuracy_pct"
            ? raw != null
              ? `${Number(raw).toFixed(1)}%`
              : "N/A"
            : raw?.toLocaleString() ?? "0";

        return (
          <Card key={key} className="py-4">
            <CardContent className="flex items-center gap-4">
              <div className="rounded-lg bg-primary/10 p-2.5">
                <Icon className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-bold tabular-nums">{display}</p>
                <p className="text-sm text-muted-foreground">{label}</p>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
