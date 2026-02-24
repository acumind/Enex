"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { PaginatedResponse, PredictionResponse } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useState } from "react";

const STATUS_COLORS: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  pending_review: "secondary",
  approved: "default",
  rejected: "destructive",
  duplicate: "outline",
};

export default function SubmissionsPage() {
  const [cursor, setCursor] = useState<string | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["my-predictions", cursor],
    queryFn: () => {
      const params: Record<string, string> = {};
      if (cursor) params.cursor = cursor;
      return api.get<PaginatedResponse<PredictionResponse>>(
        "/predictions/mine",
        params
      );
    },
  });

  return (
    <div className="container mx-auto max-w-4xl py-8 px-4">
      <h1 className="text-2xl font-bold mb-6">My Submissions</h1>

      {isLoading && <p className="text-muted-foreground">Loading...</p>}
      {error && (
        <p className="text-destructive">
          Failed to load submissions. Please try again.
        </p>
      )}

      {data && data.items.length === 0 && (
        <p className="text-muted-foreground">No submissions yet.</p>
      )}

      <div className="space-y-3">
        {data?.items.map((prediction) => (
          <Card key={prediction.id}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">
                  Target: &#8377;{prediction.target_price}
                </CardTitle>
                <div className="flex gap-2">
                  <Badge variant={STATUS_COLORS[prediction.status] || "secondary"}>
                    {prediction.status.replace(/_/g, " ")}
                  </Badge>
                  {prediction.extraction_method !== "manual" && (
                    <Badge variant="outline">{prediction.extraction_method}</Badge>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm text-muted-foreground">
                <span>Date: {prediction.prediction_date}</span>
                <span>Upside: {prediction.upside_pct}%</span>
                <span>Source: {prediction.source_type.replace(/_/g, " ")}</span>
                <span>
                  Submitted:{" "}
                  {new Date(prediction.created_at).toLocaleDateString()}
                </span>
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
