"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { RuntimeConfigResponse } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";

const BOOLEAN_KEYS = new Set([
  "maintenance_mode",
  "evaluation_enabled",
  "registration_enabled",
]);

function isBooleanKey(key: string) {
  return BOOLEAN_KEYS.has(key);
}

export default function RuntimeConfigPage() {
  const queryClient = useQueryClient();
  const [editingConfig, setEditingConfig] =
    useState<RuntimeConfigResponse | null>(null);
  const [editValue, setEditValue] = useState("");

  const { data: configs, isLoading } = useQuery({
    queryKey: ["admin-config"],
    queryFn: () => api.get<RuntimeConfigResponse[]>("/admin/config"),
  });

  const updateMutation = useMutation({
    mutationFn: ({ key, value }: { key: string; value: string }) =>
      api.patch<RuntimeConfigResponse>(`/admin/config/${key}`, { value }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-config"] });
      setEditingConfig(null);
    },
  });

  const toggleMutation = useMutation({
    mutationFn: ({ key, value }: { key: string; value: string }) =>
      api.patch<RuntimeConfigResponse>(`/admin/config/${key}`, { value }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-config"] });
    },
  });

  function handleToggle(config: RuntimeConfigResponse) {
    const newValue = config.value === "true" ? "false" : "true";
    toggleMutation.mutate({ key: config.key, value: newValue });
  }

  function openEdit(config: RuntimeConfigResponse) {
    setEditingConfig(config);
    setEditValue(config.value);
  }

  function handleSave() {
    if (!editingConfig) return;
    updateMutation.mutate({ key: editingConfig.key, value: editValue });
  }

  return (
    <div className="container mx-auto max-w-4xl py-8 px-4">
      <h1 className="text-2xl font-bold mb-6">Runtime Configuration</h1>

      {isLoading ? (
        <p className="text-muted-foreground">Loading configuration...</p>
      ) : !configs ? (
        <p className="text-destructive">Failed to load configuration.</p>
      ) : (
        <div className="space-y-3">
          {configs.map((config) => (
            <Card key={config.key}>
              <CardContent className="py-4 px-4">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <p className="font-medium font-mono text-sm">
                      {config.key}
                    </p>
                    {config.description && (
                      <p className="text-sm text-muted-foreground mt-0.5">
                        {config.description}
                      </p>
                    )}
                    <p className="text-xs text-muted-foreground mt-1">
                      Updated: {new Date(config.updated_at).toLocaleString()}
                    </p>
                  </div>
                  <div className="ml-4">
                    {isBooleanKey(config.key) ? (
                      <Switch
                        checked={config.value === "true"}
                        onCheckedChange={() => handleToggle(config)}
                        disabled={toggleMutation.isPending}
                      />
                    ) : (
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-mono bg-muted px-2 py-1 rounded">
                          {config.value}
                        </span>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => openEdit(config)}
                        >
                          Edit
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Edit Dialog */}
      <Dialog
        open={editingConfig !== null}
        onOpenChange={(open) => !open && setEditingConfig(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              Edit: {editingConfig?.key}
            </DialogTitle>
          </DialogHeader>
          {editingConfig?.description && (
            <p className="text-sm text-muted-foreground">
              {editingConfig.description}
            </p>
          )}
          <div className="space-y-2">
            <Label htmlFor="config-value">Value</Label>
            <Input
              id="config-value"
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
            />
          </div>
          {updateMutation.isError && (
            <p className="text-destructive text-sm">Failed to update config.</p>
          )}
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setEditingConfig(null)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSave}
              disabled={updateMutation.isPending || editValue === editingConfig?.value}
            >
              {updateMutation.isPending ? "Saving..." : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
