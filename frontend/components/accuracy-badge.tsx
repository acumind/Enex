import { cn } from "@/lib/utils";

export function AccuracyBadge({ value }: { value: string | null }) {
  if (value === null) return <span className="text-muted-foreground">N/A</span>;

  const pct = parseFloat(value);
  const color =
    pct >= 70
      ? "text-green-700 dark:text-green-400"
      : pct >= 40
        ? "text-yellow-700 dark:text-yellow-400"
        : "text-red-700 dark:text-red-400";

  return <span className={cn("font-semibold tabular-nums", color)}>{pct.toFixed(1)}%</span>;
}
