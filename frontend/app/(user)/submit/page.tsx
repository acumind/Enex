"use client";

import { useState } from "react";
import { api, ApiClientError } from "@/lib/api-client";
import type { ExtractionResponse } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";

type Step = "url" | "edit" | "review";

const SOURCE_TYPES = [
  "tv_interview",
  "news_article",
  "research_report",
  "social_media",
  "podcast",
  "blog",
  "other",
];

interface PredictionForm {
  predictor_name: string;
  stock_symbol: string;
  target_price: string;
  price_at_prediction: string;
  prediction_date: string;
  source_type: string;
  raw_quote: string;
  confidence: number;
}

export default function SubmitPredictionPage() {
  const [step, setStep] = useState<Step>("url");
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [extraction, setExtraction] = useState<ExtractionResponse | null>(
    null
  );
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [form, setForm] = useState<PredictionForm>({
    predictor_name: "",
    stock_symbol: "",
    target_price: "",
    price_at_prediction: "",
    prediction_date: new Date().toISOString().split("T")[0],
    source_type: "news_article",
    raw_quote: "",
    confidence: 0,
  });

  const handleExtract = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.post<ExtractionResponse>("/extract", { url });
      setExtraction(result);
      if (result.predictions.length > 0) {
        const p = result.predictions[0];
        setForm({
          predictor_name: p.predictor_name,
          stock_symbol: p.stock_symbol,
          target_price: String(p.target_price),
          price_at_prediction: String(p.current_price_mentioned || ""),
          prediction_date: new Date().toISOString().split("T")[0],
          source_type: p.source_type,
          raw_quote: p.raw_quote || "",
          confidence: p.confidence,
        });
      }
      setStep("edit");
    } catch (e) {
      setError(
        e instanceof ApiClientError ? e.message : "Extraction failed"
      );
    } finally {
      setLoading(false);
    }
  };

  const handlePredictionSelect = (index: number) => {
    if (!extraction) return;
    const p = extraction.predictions[index];
    setSelectedIndex(index);
    setForm({
      predictor_name: p.predictor_name,
      stock_symbol: p.stock_symbol,
      target_price: String(p.target_price),
      price_at_prediction: String(p.current_price_mentioned || ""),
      prediction_date: new Date().toISOString().split("T")[0],
      source_type: p.source_type,
      raw_quote: p.raw_quote || "",
      confidence: p.confidence,
    });
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    try {
      // Note: predictor_id and stock_id need to be resolved from names/symbols
      // For now, this demonstrates the UI flow. Full resolution requires search endpoints.
      await api.post("/predictions", {
        predictor_id: "00000000-0000-0000-0000-000000000000", // placeholder
        stock_id: "00000000-0000-0000-0000-000000000000", // placeholder
        target_price: form.target_price,
        price_at_prediction: form.price_at_prediction,
        prediction_date: form.prediction_date,
        source_url: url,
        source_type: form.source_type,
        raw_quote: form.raw_quote || null,
        extraction_method: "ai_assisted",
        ai_confidence: String(form.confidence),
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
      <div className="container mx-auto max-w-2xl py-8 px-4">
        <Alert>
          <AlertDescription>
            Prediction submitted for moderation. You can track its status in
            your dashboard.
          </AlertDescription>
        </Alert>
        <Button className="mt-4" onClick={() => window.location.reload()}>
          Submit Another
        </Button>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-2xl py-8 px-4">
      <h1 className="text-2xl font-bold mb-6">Submit a Prediction</h1>

      {/* Step indicators */}
      <div className="flex gap-2 mb-6">
        {(["url", "edit", "review"] as Step[]).map((s, i) => (
          <Badge key={s} variant={step === s ? "default" : "secondary"}>
            {i + 1}. {s === "url" ? "Extract" : s === "edit" ? "Edit" : "Review"}
          </Badge>
        ))}
      </div>

      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Step 1: URL Input */}
      {step === "url" && (
        <Card>
          <CardHeader>
            <CardTitle>Enter Article URL</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              placeholder="https://example.com/article-with-prediction"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
            <Button onClick={handleExtract} disabled={!url || loading}>
              {loading ? "Extracting..." : "Extract Predictions"}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Step 2: Edit Extracted Data */}
      {step === "edit" && extraction && (
        <div className="space-y-4">
          {extraction.predictions.length > 1 && (
            <div className="flex gap-2 flex-wrap">
              {extraction.predictions.map((p, i) => (
                <Button
                  key={i}
                  variant={selectedIndex === i ? "default" : "outline"}
                  size="sm"
                  onClick={() => handlePredictionSelect(i)}
                >
                  {p.stock_symbol} — {p.predictor_name}
                </Button>
              ))}
            </div>
          )}

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                Edit Prediction
                <Badge variant="secondary">
                  Confidence: {Math.round(form.confidence * 100)}%
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Predictor Name</Label>
                  <Input
                    value={form.predictor_name}
                    onChange={(e) =>
                      setForm({ ...form, predictor_name: e.target.value })
                    }
                  />
                </div>
                <div>
                  <Label>Stock Symbol</Label>
                  <Input
                    value={form.stock_symbol}
                    onChange={(e) =>
                      setForm({ ...form, stock_symbol: e.target.value })
                    }
                  />
                </div>
                <div>
                  <Label>Target Price (INR)</Label>
                  <Input
                    type="number"
                    value={form.target_price}
                    onChange={(e) =>
                      setForm({ ...form, target_price: e.target.value })
                    }
                  />
                </div>
                <div>
                  <Label>Current Price (INR)</Label>
                  <Input
                    type="number"
                    value={form.price_at_prediction}
                    onChange={(e) =>
                      setForm({
                        ...form,
                        price_at_prediction: e.target.value,
                      })
                    }
                  />
                </div>
                <div>
                  <Label>Prediction Date</Label>
                  <Input
                    type="date"
                    value={form.prediction_date}
                    onChange={(e) =>
                      setForm({ ...form, prediction_date: e.target.value })
                    }
                  />
                </div>
                <div>
                  <Label>Source Type</Label>
                  <Select
                    value={form.source_type}
                    onValueChange={(v) =>
                      setForm({ ...form, source_type: v })
                    }
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
              </div>
              <div>
                <Label>Raw Quote</Label>
                <Textarea
                  value={form.raw_quote}
                  onChange={(e) =>
                    setForm({ ...form, raw_quote: e.target.value })
                  }
                  rows={3}
                />
              </div>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setStep("url")}>
                  Back
                </Button>
                <Button onClick={() => setStep("review")}>
                  Review
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Step 3: Review & Submit */}
      {step === "review" && (
        <Card>
          <CardHeader>
            <CardTitle>Review Prediction</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-2 text-sm">
              <span className="font-medium">Predictor:</span>
              <span>{form.predictor_name}</span>
              <span className="font-medium">Stock:</span>
              <span>{form.stock_symbol}</span>
              <span className="font-medium">Target Price:</span>
              <span>&#8377;{form.target_price}</span>
              <span className="font-medium">Current Price:</span>
              <span>&#8377;{form.price_at_prediction}</span>
              <span className="font-medium">Date:</span>
              <span>{form.prediction_date}</span>
              <span className="font-medium">Source:</span>
              <span>{form.source_type.replace(/_/g, " ")}</span>
              <span className="font-medium">URL:</span>
              <span className="truncate">{url}</span>
            </div>
            {form.raw_quote && (
              <blockquote className="border-l-2 pl-4 italic text-sm text-muted-foreground">
                {form.raw_quote}
              </blockquote>
            )}
            <div className="flex gap-2 pt-2">
              <Button variant="outline" onClick={() => setStep("edit")}>
                Back
              </Button>
              <Button onClick={handleSubmit} disabled={loading}>
                {loading ? "Submitting..." : "Submit for Moderation"}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
