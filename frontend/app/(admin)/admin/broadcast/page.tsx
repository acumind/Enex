"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { BroadcastResponse } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

export default function BroadcastPage() {
  const [title, setTitle] = useState("");
  const [message, setMessage] = useState("");
  const [type, setType] = useState("system");
  const [roleFilter, setRoleFilter] = useState("all");
  const [lastResult, setLastResult] = useState<BroadcastResponse | null>(null);

  const broadcastMutation = useMutation({
    mutationFn: () =>
      api.post<BroadcastResponse>("/admin/notifications/broadcast", {
        title,
        message,
        type,
        role_filter: roleFilter === "all" ? null : roleFilter,
      }),
    onSuccess: (data) => {
      setLastResult(data);
      setTitle("");
      setMessage("");
      setType("system");
      setRoleFilter("all");
    },
  });

  const canSubmit =
    title.trim().length > 0 &&
    message.trim().length > 0 &&
    !broadcastMutation.isPending;

  return (
    <div className="container mx-auto max-w-2xl py-8 px-4">
      <h1 className="text-2xl font-bold mb-6">Notification Broadcast</h1>

      {lastResult && (
        <Card className="mb-6 border-green-200 bg-green-50 dark:bg-green-950/20">
          <CardContent className="py-4">
            <p className="text-sm font-medium text-green-800 dark:text-green-200">
              {lastResult.message}
            </p>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Send Notification</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="title">Title</Label>
            <Input
              id="title"
              placeholder="Notification title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              maxLength={200}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="message">Message</Label>
            <Textarea
              id="message"
              placeholder="Notification message..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              maxLength={2000}
              rows={4}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Type</Label>
              <Select value={type} onValueChange={setType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="system">System</SelectItem>
                  <SelectItem value="info">Info</SelectItem>
                  <SelectItem value="warning">Warning</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Recipients</Label>
              <Select value={roleFilter} onValueChange={setRoleFilter}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Users</SelectItem>
                  <SelectItem value="user">Users Only</SelectItem>
                  <SelectItem value="moderator">Moderators</SelectItem>
                  <SelectItem value="admin">Admins</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {broadcastMutation.isError && (
            <p className="text-destructive text-sm">
              Failed to send notification.
            </p>
          )}

          <Button
            onClick={() => broadcastMutation.mutate()}
            disabled={!canSubmit}
            className="w-full"
          >
            {broadcastMutation.isPending ? "Sending..." : "Send Broadcast"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
