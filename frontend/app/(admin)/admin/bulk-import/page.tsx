"use client";

import { useState } from "react";
import { api, ApiClientError } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface BulkExtractResponse {
  job_id: string;
  total: number;
  message: string;
}

export default function BulkImportPage() {
  const [urlText, setUrlText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<BulkExtractResponse | null>(null);

  const urls = urlText
    .split("\n")
    .map((u) => u.trim())
    .filter((u) => u.length > 0);

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await api.post<BulkExtractResponse>(
        "/admin/bulk-extract",
        { urls }
      );
      setResult(response);
    } catch (e) {
      setError(
        e instanceof ApiClientError ? e.message : "Bulk extraction failed"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto max-w-2xl py-8 px-4">
      <h1 className="text-2xl font-bold mb-6">Bulk Import</h1>
      <p className="text-muted-foreground mb-4">
        Paste up to 20 article URLs (one per line) to queue them for AI
        extraction.
      </p>

      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {result && (
        <Alert className="mb-4">
          <AlertDescription>
            {result.message} (Job ID: {result.job_id})
          </AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Article URLs</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>URLs (one per line, max 20)</Label>
            <Textarea
              placeholder={"https://example.com/article-1\nhttps://example.com/article-2"}
              value={urlText}
              onChange={(e) => setUrlText(e.target.value)}
              rows={8}
            />
            <p className="text-xs text-muted-foreground mt-1">
              {urls.length}/20 URLs
            </p>
          </div>
          <Button
            onClick={handleSubmit}
            disabled={urls.length === 0 || urls.length > 20 || loading}
          >
            {loading
              ? "Queuing..."
              : `Queue ${urls.length} URL${urls.length !== 1 ? "s" : ""} for Extraction`}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
