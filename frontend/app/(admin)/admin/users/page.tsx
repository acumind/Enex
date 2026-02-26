"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type {
  PaginatedResponse,
  ActiveSessionsResponse,
  UserDetailResponse,
} from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useState } from "react";

interface UserRow {
  id: string;
  email: string | null;
  phone: string | null;
  name: string | null;
  avatar_url: string | null;
  role: string;
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
}

const ROLES = ["user", "moderator", "admin"];

function RoleChangeDialog({
  user,
  open,
  onOpenChange,
}: {
  user: UserRow;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const queryClient = useQueryClient();
  const [role, setRole] = useState(user.role);

  const mutation = useMutation({
    mutationFn: (newRole: string) =>
      api.patch<UserRow>(`/admin/users/${user.id}/role`, { role: newRole }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      onOpenChange(false);
    },
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Change Role</DialogTitle>
        </DialogHeader>
        <p className="text-sm text-muted-foreground mb-2">
          {user.name || user.email || user.phone}
        </p>
        <div>
          <Label htmlFor="role">Role</Label>
          <Select value={role} onValueChange={setRole}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {ROLES.map((r) => (
                <SelectItem key={r} value={r}>
                  {r}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={() => mutation.mutate(role)}
            disabled={mutation.isPending || role === user.role}
          >
            {mutation.isPending ? "Saving..." : "Save"}
          </Button>
        </DialogFooter>
        {mutation.isError && (
          <p className="text-destructive text-sm">Failed to change role.</p>
        )}
      </DialogContent>
    </Dialog>
  );
}

function UserDetailDialog({
  userId,
  open,
  onOpenChange,
}: {
  userId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const queryClient = useQueryClient();

  const { data: detail } = useQuery({
    queryKey: ["admin-user-detail", userId],
    queryFn: () => api.get<UserDetailResponse>(`/admin/users/${userId}`),
    enabled: open,
  });

  const { data: sessions } = useQuery({
    queryKey: ["admin-user-sessions", userId],
    queryFn: () =>
      api.get<ActiveSessionsResponse>(`/admin/users/${userId}/sessions`),
    enabled: open,
  });

  const revokeMutation = useMutation({
    mutationFn: () =>
      api.post<UserRow>(`/admin/users/${userId}/revoke-sessions`),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["admin-user-sessions", userId],
      });
    },
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>User Detail</DialogTitle>
        </DialogHeader>
        {detail && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-2 text-sm">
              <span className="text-muted-foreground">Email:</span>
              <span>{detail.email || "-"}</span>
              <span className="text-muted-foreground">Phone:</span>
              <span>{detail.phone || "-"}</span>
              <span className="text-muted-foreground">Name:</span>
              <span>{detail.name || "-"}</span>
              <span className="text-muted-foreground">Role:</span>
              <Badge variant="secondary">{detail.role}</Badge>
              <span className="text-muted-foreground">Active:</span>
              <Badge variant={detail.is_active ? "default" : "destructive"}>
                {detail.is_active ? "Yes" : "Banned"}
              </Badge>
              <span className="text-muted-foreground">Auth Methods:</span>
              <span>{detail.auth_methods.join(", ") || "-"}</span>
              <span className="text-muted-foreground">Email Verified:</span>
              <span>{detail.is_email_verified ? "Yes" : "No"}</span>
              <span className="text-muted-foreground">Phone Verified:</span>
              <span>{detail.is_phone_verified ? "Yes" : "No"}</span>
              <span className="text-muted-foreground">Created:</span>
              <span>{new Date(detail.created_at).toLocaleString()}</span>
              <span className="text-muted-foreground">Last Login:</span>
              <span>
                {detail.last_login_at
                  ? new Date(detail.last_login_at).toLocaleString()
                  : "Never"}
              </span>
            </div>

            {sessions && (
              <>
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-sm">
                    Active Sessions: {sessions.refresh_token_count}
                  </h3>
                  {sessions.refresh_token_count > 0 && (
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => revokeMutation.mutate()}
                      disabled={revokeMutation.isPending}
                    >
                      {revokeMutation.isPending
                        ? "Revoking..."
                        : "Revoke All Sessions"}
                    </Button>
                  )}
                </div>

                {sessions.login_events.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-sm mb-2">
                      Login History
                    </h3>
                    <div className="overflow-x-auto">
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="border-b text-left">
                            <th className="pb-1 font-medium">Method</th>
                            <th className="pb-1 font-medium">IP</th>
                            <th className="pb-1 font-medium">User Agent</th>
                            <th className="pb-1 font-medium">Time</th>
                          </tr>
                        </thead>
                        <tbody>
                          {sessions.login_events.map((evt) => (
                            <tr key={evt.id} className="border-b">
                              <td className="py-1">
                                <Badge variant="outline">
                                  {evt.login_method}
                                </Badge>
                              </td>
                              <td className="py-1 font-mono">
                                {evt.ip_address || "-"}
                              </td>
                              <td className="py-1 max-w-[200px] truncate">
                                {evt.user_agent || "-"}
                              </td>
                              <td className="py-1">
                                {new Date(evt.created_at).toLocaleString()}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

export default function UserManagementPage() {
  const [cursor, setCursor] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState<string>("all");
  const [activeFilter, setActiveFilter] = useState<string>("all");
  const [roleChangeUser, setRoleChangeUser] = useState<UserRow | null>(null);
  const [detailUserId, setDetailUserId] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ["admin-users", cursor, search, roleFilter, activeFilter],
    queryFn: () => {
      const params: Record<string, string> = {};
      if (cursor) params.cursor = cursor;
      if (search) params.search = search;
      if (roleFilter !== "all") params.role = roleFilter;
      if (activeFilter !== "all") params.is_active = activeFilter;
      return api.get<PaginatedResponse<UserRow>>("/admin/users", params);
    },
  });

  const banMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      api.patch<UserRow>(`/admin/users/${id}/ban`, { ban_reason: reason }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["admin-users"] }),
  });

  const unbanMutation = useMutation({
    mutationFn: (id: string) => api.delete<UserRow>(`/admin/users/${id}/ban`),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["admin-users"] }),
  });

  const handleSearch = (value: string) => {
    setSearch(value);
    setCursor(null);
  };

  return (
    <div className="container mx-auto max-w-6xl py-8 px-4">
      <h1 className="text-2xl font-bold mb-6">User Management</h1>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <Input
          placeholder="Search by email or name..."
          value={search}
          onChange={(e) => handleSearch(e.target.value)}
          className="max-w-xs"
        />
        <Select
          value={roleFilter}
          onValueChange={(v) => {
            setRoleFilter(v);
            setCursor(null);
          }}
        >
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Role" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Roles</SelectItem>
            {ROLES.map((r) => (
              <SelectItem key={r} value={r}>
                {r}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select
          value={activeFilter}
          onValueChange={(v) => {
            setActiveFilter(v);
            setCursor(null);
          }}
        >
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="true">Active</SelectItem>
            <SelectItem value="false">Banned</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {isLoading && <p className="text-muted-foreground">Loading...</p>}
      {error && <p className="text-destructive">Failed to load users.</p>}

      {data && data.items.length === 0 && (
        <p className="text-muted-foreground">No users found.</p>
      )}

      {data && data.items.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left">
                <th className="pb-2 font-medium">Name</th>
                <th className="pb-2 font-medium">Email</th>
                <th className="pb-2 font-medium">Role</th>
                <th className="pb-2 font-medium">Active</th>
                <th className="pb-2 font-medium">Last Login</th>
                <th className="pb-2 font-medium">Created</th>
                <th className="pb-2 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((u) => (
                <tr key={u.id} className="border-b">
                  <td className="py-2">
                    <button
                      className="text-left hover:underline"
                      onClick={() => setDetailUserId(u.id)}
                    >
                      {u.name || "-"}
                    </button>
                  </td>
                  <td className="py-2 text-muted-foreground">
                    {u.email || u.phone || "-"}
                  </td>
                  <td className="py-2">
                    <Badge variant="secondary">{u.role}</Badge>
                  </td>
                  <td className="py-2">
                    <Badge
                      variant={u.is_active ? "default" : "destructive"}
                    >
                      {u.is_active ? "Active" : "Banned"}
                    </Badge>
                  </td>
                  <td className="py-2 text-muted-foreground text-xs">
                    {u.last_login_at
                      ? new Date(u.last_login_at).toLocaleDateString()
                      : "Never"}
                  </td>
                  <td className="py-2 text-muted-foreground text-xs">
                    {new Date(u.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-2">
                    <div className="flex gap-1">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setRoleChangeUser(u)}
                      >
                        Role
                      </Button>
                      {u.is_active ? (
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() =>
                            banMutation.mutate({
                              id: u.id,
                              reason: "Banned by admin",
                            })
                          }
                          disabled={banMutation.isPending}
                        >
                          Ban
                        </Button>
                      ) : (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => unbanMutation.mutate(u.id)}
                          disabled={unbanMutation.isPending}
                        >
                          Unban
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {data?.has_more && (
        <Button
          variant="outline"
          className="mt-4"
          onClick={() => setCursor(data.next_cursor)}
        >
          Load More
        </Button>
      )}

      {roleChangeUser && (
        <RoleChangeDialog
          user={roleChangeUser}
          open={!!roleChangeUser}
          onOpenChange={(open) => {
            if (!open) setRoleChangeUser(null);
          }}
        />
      )}

      {detailUserId && (
        <UserDetailDialog
          userId={detailUserId}
          open={!!detailUserId}
          onOpenChange={(open) => {
            if (!open) setDetailUserId(null);
          }}
        />
      )}
    </div>
  );
}
