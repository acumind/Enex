"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { SystemHealthResponse, AdminAlertsResponse } from "@/lib/types";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

function AlertBanner({ alerts }: { alerts: AdminAlertsResponse }) {
  if (alerts.alerts.length === 0) return null;
  return (
    <div className="space-y-2 mb-6">
      {alerts.alerts.map((alert, i) => (
        <Alert
          key={i}
          variant={alert.level === "critical" ? "destructive" : "default"}
        >
          <AlertDescription className="flex items-center gap-2">
            <Badge
              variant={
                alert.level === "critical" ? "destructive" : "secondary"
              }
            >
              {alert.level}
            </Badge>
            <span>{alert.message}</span>
          </AlertDescription>
        </Alert>
      ))}
    </div>
  );
}

function PoolBar({
  label,
  value,
  total,
  color,
}: {
  label: string;
  value: number;
  total: number;
  color: string;
}) {
  const pct = total > 0 ? Math.round((value / total) * 100) : 0;
  return (
    <div className="flex items-center gap-3">
      <span className="text-sm text-muted-foreground w-28">{label}</span>
      <div className="flex-1 h-4 bg-muted rounded overflow-hidden">
        <div
          className={`h-full ${color} rounded`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-sm font-medium w-16 text-right">
        {value}/{total}
      </span>
    </div>
  );
}

export default function SystemHealthPage() {
  const { data: health, isLoading } = useQuery({
    queryKey: ["admin-health"],
    queryFn: () => api.get<SystemHealthResponse>("/admin/health"),
    refetchInterval: 30000,
  });

  const { data: alerts } = useQuery({
    queryKey: ["admin-alerts"],
    queryFn: () => api.get<AdminAlertsResponse>("/admin/alerts"),
    refetchInterval: 30000,
  });

  return (
    <div className="container mx-auto max-w-4xl py-8 px-4">
      <h1 className="text-2xl font-bold mb-6">System Health</h1>

      {alerts && <AlertBanner alerts={alerts} />}

      {isLoading ? (
        <p className="text-muted-foreground">Loading health data...</p>
      ) : !health ? (
        <p className="text-destructive">Failed to load health data.</p>
      ) : (
        <div className="space-y-6">
          {/* Database Pool */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Database Pool</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <PoolBar
                label="Checked Out"
                value={health.db_pool_checked_out}
                total={health.db_pool_size}
                color="bg-blue-500"
              />
              <PoolBar
                label="Checked In"
                value={health.db_pool_checked_in}
                total={health.db_pool_size}
                color="bg-green-500"
              />
              <PoolBar
                label="Overflow"
                value={health.db_pool_overflow}
                total={health.db_pool_size}
                color="bg-yellow-500"
              />
              <p className="text-sm text-muted-foreground">
                Pool size: {health.db_pool_size}
              </p>
            </CardContent>
          </Card>

          {/* Redis */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Redis</CardTitle>
            </CardHeader>
            <CardContent>
              {health.redis_latency_ms !== null ? (
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Latency</p>
                    <p className="text-xl font-bold">
                      {health.redis_latency_ms}ms
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Memory</p>
                    <p className="text-xl font-bold">
                      {health.redis_memory ?? "N/A"}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">
                      Connected Clients
                    </p>
                    <p className="text-xl font-bold">
                      {health.redis_connected_clients ?? "N/A"}
                    </p>
                  </div>
                </div>
              ) : (
                <p className="text-destructive">Redis unreachable</p>
              )}
            </CardContent>
          </Card>

          {/* Celery */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Celery Workers</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Workers</p>
                  <p className="text-xl font-bold">{health.celery_workers}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Active Tasks</p>
                  <p className="text-xl font-bold">
                    {health.celery_active_tasks}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">
                    Reserved Tasks
                  </p>
                  <p className="text-xl font-bold">
                    {health.celery_reserved_tasks}
                  </p>
                </div>
              </div>
              {health.celery_workers === 0 && (
                <p className="text-destructive text-sm mt-2">
                  No workers are currently online.
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
