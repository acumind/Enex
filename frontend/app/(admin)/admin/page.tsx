"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { api } from "@/lib/api-client";
import type {
  AdminStatsResponse,
  AuditLogResponse,
  JobStatusResponse,
  PaginatedResponse,
} from "@/lib/types";
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

function JobStatusBadge({ status }: { status: string }) {
  const variant =
    status === "SUCCESS"
      ? "default"
      : status === "FAILURE"
        ? "destructive"
        : status === "PENDING" || status === "STARTED"
          ? "secondary"
          : "outline";
  return <Badge variant={variant}>{status}</Badge>;
}

export default function AdminPage() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["admin-stats"],
    queryFn: () => api.get<AdminStatsResponse>("/admin/stats"),
  });

  const { data: auditData } = useQuery({
    queryKey: ["admin-audit-recent"],
    queryFn: () =>
      api.get<PaginatedResponse<AuditLogResponse>>("/admin/audit-log", {
        limit: "10",
      }),
  });

  const { data: jobs } = useQuery({
    queryKey: ["admin-jobs-recent"],
    queryFn: () =>
      api.get<JobStatusResponse[]>("/admin/jobs/recent", { limit: "10" }),
  });

  return (
    <div className="container mx-auto max-w-6xl py-8 px-4">
      <h1 className="text-2xl font-bold mb-6">Admin Dashboard</h1>

      {/* Stats Grid */}
      {statsLoading ? (
        <p className="text-muted-foreground mb-6">Loading stats...</p>
      ) : stats ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <StatCard
            label="Pending Predictions"
            value={stats.pending_predictions}
          />
          <StatCard
            label="Pending Suggestions"
            value={stats.pending_suggestions}
          />
          <StatCard label="Total Users" value={stats.total_users} />
          <StatCard
            label="Predictions This Week"
            value={stats.predictions_this_week}
          />
        </div>
      ) : null}

      {/* Quick Actions */}
      <h2 className="text-lg font-semibold mb-3">Quick Actions</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <Link href="/admin/review-queue">
          <Card className="hover:bg-muted/50 transition-colors cursor-pointer">
            <CardContent className="pt-6 text-center">
              <p className="font-medium">Review Queue</p>
              <p className="text-sm text-muted-foreground">
                Approve or reject predictions
              </p>
            </CardContent>
          </Card>
        </Link>
        <Link href="/admin/suggestions">
          <Card className="hover:bg-muted/50 transition-colors cursor-pointer">
            <CardContent className="pt-6 text-center">
              <p className="font-medium">Suggestions</p>
              <p className="text-sm text-muted-foreground">
                Promote or dismiss
              </p>
            </CardContent>
          </Card>
        </Link>
        <Link href="/admin/bulk-import">
          <Card className="hover:bg-muted/50 transition-colors cursor-pointer">
            <CardContent className="pt-6 text-center">
              <p className="font-medium">Bulk Import</p>
              <p className="text-sm text-muted-foreground">
                Extract from URLs
              </p>
            </CardContent>
          </Card>
        </Link>
        <Link href="/admin/stocks">
          <Card className="hover:bg-muted/50 transition-colors cursor-pointer">
            <CardContent className="pt-6 text-center">
              <p className="font-medium">Stock Management</p>
              <p className="text-sm text-muted-foreground">
                Create and edit stocks
              </p>
            </CardContent>
          </Card>
        </Link>
      </div>

      {/* Two-column layout for Recent Activity and Jobs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Activity */}
        <div>
          <h2 className="text-lg font-semibold mb-3">Recent Activity</h2>
          {auditData && auditData.items.length > 0 ? (
            <div className="space-y-2">
              {auditData.items.map((entry) => (
                <Card key={entry.id}>
                  <CardContent className="py-3 px-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="font-medium text-sm">
                          {entry.action}
                        </span>
                        <span className="text-muted-foreground text-sm ml-2">
                          on {entry.entity_type}
                        </span>
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {entry.actor_name || "Unknown"}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {new Date(entry.created_at).toLocaleString()}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground text-sm">
              No recent activity.
            </p>
          )}
        </div>

        {/* Recent Jobs */}
        <div>
          <h2 className="text-lg font-semibold mb-3">Recent Jobs</h2>
          {jobs && jobs.length > 0 ? (
            <div className="space-y-2">
              {jobs.map((job) => (
                <Card key={job.task_id}>
                  <CardContent className="py-3 px-4">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-sm">
                        {job.task_name}
                      </span>
                      <JobStatusBadge status={job.status} />
                    </div>
                    {job.date_done && (
                      <p className="text-xs text-muted-foreground mt-1">
                        Completed: {new Date(job.date_done).toLocaleString()}
                      </p>
                    )}
                    {job.traceback && (
                      <p className="text-xs text-destructive mt-1 truncate">
                        {job.traceback.split("\n").pop()}
                      </p>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground text-sm">No recent jobs.</p>
          )}
        </div>
      </div>
    </div>
  );
}
