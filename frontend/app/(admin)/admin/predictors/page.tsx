"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { PaginatedResponse, PredictorResponse } from "@/lib/types";
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
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useState } from "react";

const PREDICTOR_TYPES = [
  "individual",
  "brokerage",
  "research_firm",
  "media_house",
  "influencer",
];

function EditPredictorDialog({
  predictor,
  open,
  onOpenChange,
}: {
  predictor: PredictorResponse;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({
    name: predictor.name,
    type: predictor.type,
    bio: predictor.bio || "",
    website: predictor.website || "",
    is_verified: predictor.is_verified,
  });

  const mutation = useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.patch<PredictorResponse>(
        `/admin/predictors/${predictor.id}`,
        data,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-predictors"] });
      onOpenChange(false);
    },
  });

  const handleSave = () => {
    const body: Record<string, unknown> = {};
    if (form.name !== predictor.name) body.name = form.name;
    if (form.bio !== (predictor.bio || "")) body.bio = form.bio || null;
    if (form.website !== (predictor.website || ""))
      body.website = form.website || null;
    if (form.is_verified !== predictor.is_verified)
      body.is_verified = form.is_verified;

    if (Object.keys(body).length === 0) {
      onOpenChange(false);
      return;
    }
    mutation.mutate(body);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Edit Predictor</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div>
            <Label htmlFor="name">Name</Label>
            <Input
              id="name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
          </div>
          <div>
            <Label htmlFor="type">Type</Label>
            <Select
              value={form.type}
              onValueChange={(v) => setForm({ ...form, type: v })}
              disabled
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {PREDICTOR_TYPES.map((t) => (
                  <SelectItem key={t} value={t}>
                    {t.replace(/_/g, " ")}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label htmlFor="bio">Bio / Description</Label>
            <Textarea
              id="bio"
              value={form.bio}
              onChange={(e) => setForm({ ...form, bio: e.target.value })}
              rows={3}
            />
          </div>
          <div>
            <Label htmlFor="website">Website</Label>
            <Input
              id="website"
              value={form.website}
              onChange={(e) => setForm({ ...form, website: e.target.value })}
            />
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_verified"
              checked={form.is_verified}
              onChange={(e) =>
                setForm({ ...form, is_verified: e.target.checked })
              }
              className="h-4 w-4"
            />
            <Label htmlFor="is_verified">Verified</Label>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={mutation.isPending}>
            {mutation.isPending ? "Saving..." : "Save Changes"}
          </Button>
        </DialogFooter>
        {mutation.isError && (
          <p className="text-destructive text-sm mt-2">
            Failed to update predictor.
          </p>
        )}
      </DialogContent>
    </Dialog>
  );
}

export default function PredictorManagementPage() {
  const [cursor, setCursor] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [editingPredictor, setEditingPredictor] =
    useState<PredictorResponse | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["admin-predictors", cursor, search, typeFilter],
    queryFn: () => {
      const params: Record<string, string> = {};
      if (cursor) params.cursor = cursor;
      if (search) params.search = search;
      if (typeFilter !== "all") params.type = typeFilter;
      return api.get<PaginatedResponse<PredictorResponse>>(
        "/admin/predictors",
        params,
      );
    },
  });

  const handleSearch = (value: string) => {
    setSearch(value);
    setCursor(null);
  };

  return (
    <div className="container mx-auto max-w-6xl py-8 px-4">
      <h1 className="text-2xl font-bold mb-6">Predictor Management</h1>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <Input
          placeholder="Search by name..."
          value={search}
          onChange={(e) => handleSearch(e.target.value)}
          className="max-w-xs"
        />
        <Select
          value={typeFilter}
          onValueChange={(v) => {
            setTypeFilter(v);
            setCursor(null);
          }}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            {PREDICTOR_TYPES.map((t) => (
              <SelectItem key={t} value={t}>
                {t.replace(/_/g, " ")}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {isLoading && <p className="text-muted-foreground">Loading...</p>}
      {error && <p className="text-destructive">Failed to load predictors.</p>}

      {data && data.items.length === 0 && (
        <p className="text-muted-foreground">No predictors found.</p>
      )}

      {data && data.items.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left">
                <th className="pb-2 font-medium">Name</th>
                <th className="pb-2 font-medium">Type</th>
                <th className="pb-2 font-medium">Slug</th>
                <th className="pb-2 font-medium">Verified</th>
                <th className="pb-2 font-medium">Created</th>
                <th className="pb-2 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((p) => (
                <tr key={p.id} className="border-b">
                  <td className="py-2">{p.name}</td>
                  <td className="py-2">
                    <Badge variant="secondary">
                      {p.type.replace(/_/g, " ")}
                    </Badge>
                  </td>
                  <td className="py-2 text-muted-foreground font-mono text-xs">
                    {p.slug}
                  </td>
                  <td className="py-2">
                    <Badge variant={p.is_verified ? "default" : "outline"}>
                      {p.is_verified ? "Verified" : "No"}
                    </Badge>
                  </td>
                  <td className="py-2 text-muted-foreground text-xs">
                    {new Date(p.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setEditingPredictor(p)}
                    >
                      Edit
                    </Button>
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

      {editingPredictor && (
        <EditPredictorDialog
          predictor={editingPredictor}
          open={!!editingPredictor}
          onOpenChange={(open) => {
            if (!open) setEditingPredictor(null);
          }}
        />
      )}
    </div>
  );
}
