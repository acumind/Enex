"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { PaginatedResponse, SuggestionResponse } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useState } from "react";

export default function SuggestionsQueuePage() {
  const [cursor, setCursor] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ["admin-suggestions", cursor],
    queryFn: () => {
      const params: Record<string, string> = {};
      if (cursor) params.cursor = cursor;
      return api.get<PaginatedResponse<SuggestionResponse>>(
        "/admin/suggestions",
        params
      );
    },
  });

  const promoteMutation = useMutation({
    mutationFn: (id: string) =>
      api.post<SuggestionResponse>(`/admin/suggestions/${id}/promote`),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["admin-suggestions"] }),
  });

  const dismissMutation = useMutation({
    mutationFn: (id: string) =>
      api.post<SuggestionResponse>(`/admin/suggestions/${id}/dismiss`),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["admin-suggestions"] }),
  });

  return (
    <div className="container mx-auto max-w-4xl py-8 px-4">
      <h1 className="text-2xl font-bold mb-6">Suggestions Queue</h1>

      {isLoading && <p className="text-muted-foreground">Loading...</p>}
      {error && (
        <p className="text-destructive">Failed to load suggestions.</p>
      )}

      {data && data.items.length === 0 && (
        <p className="text-muted-foreground">No pending suggestions.</p>
      )}

      <div className="space-y-3">
        {data?.items.map((suggestion) => (
          <Card key={suggestion.id}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base truncate max-w-md">
                  <a
                    href={suggestion.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="underline"
                  >
                    {suggestion.url}
                  </a>
                </CardTitle>
                <Badge variant="secondary">{suggestion.status}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              {suggestion.note && (
                <p className="text-sm text-muted-foreground mb-3">
                  {suggestion.note}
                </p>
              )}
              <div className="text-xs text-muted-foreground mb-3">
                Submitted: {new Date(suggestion.created_at).toLocaleString()}
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  onClick={() => promoteMutation.mutate(suggestion.id)}
                  disabled={promoteMutation.isPending}
                >
                  Promote
                </Button>
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={() => dismissMutation.mutate(suggestion.id)}
                  disabled={dismissMutation.isPending}
                >
                  Dismiss
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
