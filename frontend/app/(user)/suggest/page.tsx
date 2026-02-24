"use client";

import { useState } from "react";
import { api, ApiClientError } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";

export default function SuggestPredictionPage() {
  const [url, setUrl] = useState("");
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    try {
      await api.post("/predictions/suggest", {
        url,
        note: note || null,
      });
      setSuccess(true);
    } catch (e) {
      setError(
        e instanceof ApiClientError ? e.message : "Submission failed"
      );
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="container mx-auto max-w-lg py-8 px-4">
        <Alert>
          <AlertDescription>
            Suggestion submitted. A moderator will review it shortly.
          </AlertDescription>
        </Alert>
        <Button className="mt-4" onClick={() => { setSuccess(false); setUrl(""); setNote(""); }}>
          Suggest Another
        </Button>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-lg py-8 px-4">
      <h1 className="text-2xl font-bold mb-6">Suggest a Prediction</h1>
      <p className="text-muted-foreground mb-4">
        Found an article with a stock prediction? Share the URL and we&apos;ll
        extract the details.
      </p>

      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Article Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>Article URL</Label>
            <Input
              placeholder="https://example.com/article-with-prediction"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
          </div>
          <div>
            <Label>Note (optional)</Label>
            <Textarea
              placeholder="Any context about the prediction..."
              value={note}
              onChange={(e) => setNote(e.target.value)}
              rows={3}
              maxLength={2000}
            />
          </div>
          <Button
            onClick={handleSubmit}
            disabled={!url || loading}
          >
            {loading ? "Submitting..." : "Submit Suggestion"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
