"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type {
  PaginatedResponse,
  PredictionResponse,
  PredictionUpdate,
} from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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

const SOURCE_TYPES = [
  "tv_interview",
  "news_article",
  "research_report",
  "social_media",
  "podcast",
  "blog",
  "other",
];

function EditPredictionDialog({
  prediction,
  open,
  onOpenChange,
}: {
  prediction: PredictionResponse;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({
    target_price: prediction.target_price,
    price_at_prediction: prediction.price_at_prediction,
    prediction_date: prediction.prediction_date,
    target_date: prediction.target_date || "",
    source_url: prediction.source_url,
    source_type: prediction.source_type,
    raw_quote: prediction.raw_quote || "",
  });

  const editMutation = useMutation({
    mutationFn: (data: PredictionUpdate) =>
      api.patch<PredictionResponse>(
        `/admin/predictions/${prediction.id}`,
        data,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["review-queue"] });
      onOpenChange(false);
    },
  });

  const handleSave = () => {
    const body: PredictionUpdate = {};
    if (form.target_price !== prediction.target_price)
      body.target_price = form.target_price;
    if (form.price_at_prediction !== prediction.price_at_prediction)
      body.price_at_prediction = form.price_at_prediction;
    if (form.prediction_date !== prediction.prediction_date)
      body.prediction_date = form.prediction_date;
    if ((form.target_date || null) !== prediction.target_date)
      body.target_date = form.target_date || null;
    if (form.source_url !== prediction.source_url)
      body.source_url = form.source_url;
    if (form.source_type !== prediction.source_type)
      body.source_type = form.source_type;
    if ((form.raw_quote || null) !== prediction.raw_quote)
      body.raw_quote = form.raw_quote || null;

    if (Object.keys(body).length === 0) {
      onOpenChange(false);
      return;
    }
    editMutation.mutate(body);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Edit Prediction</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="target_price">Target Price</Label>
              <Input
                id="target_price"
                type="number"
                step="0.01"
                value={form.target_price}
                onChange={(e) =>
                  setForm({ ...form, target_price: e.target.value })
                }
              />
            </div>
            <div>
              <Label htmlFor="price_at_prediction">Price at Prediction</Label>
              <Input
                id="price_at_prediction"
                type="number"
                step="0.01"
                value={form.price_at_prediction}
                onChange={(e) =>
                  setForm({ ...form, price_at_prediction: e.target.value })
                }
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="prediction_date">Prediction Date</Label>
              <Input
                id="prediction_date"
                type="date"
                value={form.prediction_date}
                onChange={(e) =>
                  setForm({ ...form, prediction_date: e.target.value })
                }
              />
            </div>
            <div>
              <Label htmlFor="target_date">Target Date</Label>
              <Input
                id="target_date"
                type="date"
                value={form.target_date}
                onChange={(e) =>
                  setForm({ ...form, target_date: e.target.value })
                }
              />
            </div>
          </div>
          <div>
            <Label htmlFor="source_url">Source URL</Label>
            <Input
              id="source_url"
              value={form.source_url}
              onChange={(e) =>
                setForm({ ...form, source_url: e.target.value })
              }
            />
          </div>
          <div>
            <Label htmlFor="source_type">Source Type</Label>
            <Select
              value={form.source_type}
              onValueChange={(v) => setForm({ ...form, source_type: v })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {SOURCE_TYPES.map((t) => (
                  <SelectItem key={t} value={t}>
                    {t.replace(/_/g, " ")}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label htmlFor="raw_quote">Raw Quote</Label>
            <Textarea
              id="raw_quote"
              value={form.raw_quote}
              onChange={(e) =>
                setForm({ ...form, raw_quote: e.target.value })
              }
              rows={3}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={editMutation.isPending}>
            {editMutation.isPending ? "Saving..." : "Save Changes"}
          </Button>
        </DialogFooter>
        {editMutation.isError && (
          <p className="text-destructive text-sm mt-2">
            Failed to update prediction.
          </p>
        )}
      </DialogContent>
    </Dialog>
  );
}

export default function ReviewQueuePage() {
  const [cursor, setCursor] = useState<string | null>(null);
  const [editingPrediction, setEditingPrediction] =
    useState<PredictionResponse | null>(null);
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ["review-queue", cursor],
    queryFn: () => {
      const params: Record<string, string> = {};
      if (cursor) params.cursor = cursor;
      return api.get<PaginatedResponse<PredictionResponse>>(
        "/admin/review-queue",
        params,
      );
    },
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) =>
      api.post<PredictionResponse>(`/admin/predictions/${id}/approve`),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["review-queue"] }),
  });

  const rejectMutation = useMutation({
    mutationFn: (id: string) =>
      api.post<PredictionResponse>(`/admin/predictions/${id}/reject`),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["review-queue"] }),
  });

  return (
    <div className="container mx-auto max-w-4xl py-8 px-4">
      <h1 className="text-2xl font-bold mb-6">Review Queue</h1>

      {isLoading && <p className="text-muted-foreground">Loading...</p>}
      {error && (
        <p className="text-destructive">Failed to load review queue.</p>
      )}

      {data && data.items.length === 0 && (
        <p className="text-muted-foreground">No predictions pending review.</p>
      )}

      <div className="space-y-3">
        {data?.items.map((prediction) => (
          <Card key={prediction.id}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">
                  Target: &#8377;{prediction.target_price} (Upside:{" "}
                  {prediction.upside_pct}%)
                </CardTitle>
                <div className="flex gap-2">
                  <Badge variant="secondary">
                    {prediction.extraction_method}
                  </Badge>
                  {prediction.ai_confidence && (
                    <Badge variant="outline">
                      AI: {Math.round(Number(prediction.ai_confidence) * 100)}%
                    </Badge>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm text-muted-foreground mb-3">
                <span>Date: {prediction.prediction_date}</span>
                <span>
                  Source: {prediction.source_type.replace(/_/g, " ")}
                </span>
                <span className="col-span-2 truncate">
                  URL:{" "}
                  <a
                    href={prediction.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="underline"
                  >
                    {prediction.source_url}
                  </a>
                </span>
              </div>
              {prediction.raw_quote && (
                <blockquote className="border-l-2 pl-4 italic text-sm text-muted-foreground mb-3">
                  {prediction.raw_quote}
                </blockquote>
              )}
              <div className="flex gap-2">
                <Button
                  size="sm"
                  onClick={() => approveMutation.mutate(prediction.id)}
                  disabled={approveMutation.isPending}
                >
                  Approve
                </Button>
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={() => rejectMutation.mutate(prediction.id)}
                  disabled={rejectMutation.isPending}
                >
                  Reject
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setEditingPrediction(prediction)}
                >
                  Edit
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {data?.has_more && (
        <Button
          variant="outline"
          className="mt-4"
          onClick={() => setCursor(data.next_cursor)}
        >
          Load More
        </Button>
      )}

      {editingPrediction && (
        <EditPredictionDialog
          prediction={editingPrediction}
          open={!!editingPrediction}
          onOpenChange={(open) => {
            if (!open) setEditingPrediction(null);
          }}
        />
      )}
    </div>
  );
}
