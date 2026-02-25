import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { OutcomeBadge } from "@/components/outcome-badge";
import type { PredictionResponse } from "@/lib/types";

interface PredictionCardProps {
  prediction: PredictionResponse;
  predictorName?: string;
  predictorSlug?: string;
  stockSymbol?: string;
}

export function PredictionCard({
  prediction,
  predictorName,
  predictorSlug,
  stockSymbol,
}: PredictionCardProps) {
  const upside = parseFloat(prediction.upside_pct);

  return (
    <Card>
      <CardContent className="flex flex-col gap-2 p-4">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            {predictorName && predictorSlug && (
              <Link
                href={`/predictor/${predictorSlug}`}
                className="text-sm font-medium hover:underline"
              >
                {predictorName}
              </Link>
            )}
            {stockSymbol && (
              <Link
                href={`/stock/${stockSymbol}`}
                className="ml-2 font-mono text-xs text-muted-foreground hover:underline"
              >
                {stockSymbol}
              </Link>
            )}
          </div>
          <OutcomeBadge status={prediction.status === "approved" ? "pending" : prediction.status} />
        </div>

        <div className="flex items-baseline gap-3 text-sm">
          <span className="text-muted-foreground">Target</span>
          <span className="font-semibold tabular-nums">
            {parseFloat(prediction.target_price).toLocaleString("en-IN")}
          </span>
          <span
            className={
              upside >= 0
                ? "text-green-700 dark:text-green-400"
                : "text-red-700 dark:text-red-400"
            }
          >
            {upside >= 0 ? "+" : ""}
            {upside.toFixed(1)}%
          </span>
        </div>

        <div className="flex gap-3 text-xs text-muted-foreground">
          <span>{prediction.prediction_date}</span>
          {prediction.target_date && <span>Target: {prediction.target_date}</span>}
        </div>
      </CardContent>
    </Card>
  );
}
