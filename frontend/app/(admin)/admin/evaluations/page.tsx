"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { EvalDashboardResponse } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

function StatCard({
  label,
  value,
}: {
  label: string;
  value: number | string;
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {label}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-2xl font-bold">{value}</p>
      </CardContent>
    </Card>
  );
}

function OutcomeBadge({ status }: { status: string }) {
  const variant =
    status === "hit"
      ? "default"
      : status === "miss"
        ? "destructive"
        : status === "partial_hit"
          ? "secondary"
          : "outline";
  return <Badge variant={variant}>{status.replace("_", " ")}</Badge>;
}

export default function EvaluationDashboardPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["admin-eval-dashboard"],
    queryFn: () => api.get<EvalDashboardResponse>("/admin/eval-dashboard"),
  });

  return (
    <div className="container mx-auto max-w-6xl py-8 px-4">
      <h1 className="text-2xl font-bold mb-6">Evaluation Dashboard</h1>

      {isLoading ? (
        <p className="text-muted-foreground">Loading evaluation data...</p>
      ) : !data ? (
        <p className="text-destructive">Failed to load evaluation data.</p>
      ) : (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Total Evaluated" value={data.total_evaluated} />
            <StatCard label="Pending" value={data.total_pending} />
            <StatCard
              label="Accuracy"
              value={
                data.accuracy_pct !== null ? `${data.accuracy_pct}%` : "N/A"
              }
            />
            <StatCard
              label="Avg Deviation"
              value={
                data.avg_deviation_pct !== null
                  ? `${data.avg_deviation_pct}%`
                  : "N/A"
              }
            />
          </div>

          {/* Outcome Breakdown */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Outcome Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-6 flex-wrap">
                <div className="flex items-center gap-2">
                  <Badge>hit</Badge>
                  <span className="text-lg font-bold">{data.hits}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="destructive">miss</Badge>
                  <span className="text-lg font-bold">{data.misses}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="secondary">partial hit</Badge>
                  <span className="text-lg font-bold">{data.partial_hits}</span>
                </div>
              </div>
              {data.total_evaluated > 0 && (
                <div className="mt-4 h-4 bg-muted rounded overflow-hidden flex">
                  {data.hits > 0 && (
                    <div
                      className="bg-green-500 h-full"
                      style={{
                        width: `${(data.hits / data.total_evaluated) * 100}%`,
                      }}
                    />
                  )}
                  {data.partial_hits > 0 && (
                    <div
                      className="bg-yellow-500 h-full"
                      style={{
                        width: `${(data.partial_hits / data.total_evaluated) * 100}%`,
                      }}
                    />
                  )}
                  {data.misses > 0 && (
                    <div
                      className="bg-red-500 h-full"
                      style={{
                        width: `${(data.misses / data.total_evaluated) * 100}%`,
                      }}
                    />
                  )}
                </div>
              )}
              <div className="mt-4 flex gap-6 text-sm text-muted-foreground">
                <span>Today: {data.evaluations_today}</span>
                <span>This week: {data.evaluations_this_week}</span>
              </div>
            </CardContent>
          </Card>

          {/* Recent Evaluations */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Recent Evaluations</CardTitle>
            </CardHeader>
            <CardContent>
              {data.recent_evaluations.length === 0 ? (
                <p className="text-muted-foreground text-sm">
                  No evaluations yet.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-left">
                        <th className="py-2 pr-4">Stock</th>
                        <th className="py-2 pr-4">Predictor</th>
                        <th className="py-2 pr-4">Outcome</th>
                        <th className="py-2 pr-4">Deviation</th>
                        <th className="py-2">Evaluated At</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.recent_evaluations.map((ev) => (
                        <tr key={ev.prediction_id} className="border-b">
                          <td className="py-2 pr-4 font-medium">
                            {ev.stock_symbol}
                          </td>
                          <td className="py-2 pr-4">{ev.predictor_name}</td>
                          <td className="py-2 pr-4">
                            <OutcomeBadge status={ev.outcome_status} />
                          </td>
                          <td className="py-2 pr-4">
                            {ev.deviation_pct !== null
                              ? `${ev.deviation_pct}%`
                              : "—"}
                          </td>
                          <td className="py-2 text-muted-foreground">
                            {new Date(ev.evaluated_at).toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
