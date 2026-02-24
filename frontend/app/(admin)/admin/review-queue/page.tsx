"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { PaginatedResponse, PredictionResponse } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useState } from "react";

export default function ReviewQueuePage() {
  const [cursor, setCursor] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ["review-queue", cursor],
    queryFn: () => {
      const params: Record<string, string> = {};
      if (cursor) params.cursor = cursor;
      return api.get<PaginatedResponse<PredictionResponse>>(
        "/admin/review-queue",
        params
      );
    },
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) =>
      api.post<PredictionResponse>(`/admin/predictions/${id}/approve`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["review-queue"] }),
  });

  const rejectMutation = useMutation({
    mutationFn: (id: string) =>
      api.post<PredictionResponse>(`/admin/predictions/${id}/reject`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["review-queue"] }),
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
    </div>
  );
}
