import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const statusConfig: Record<string, { label: string; className: string }> = {
  hit: {
    label: "Hit",
    className: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  },
  partial_hit: {
    label: "Partial",
    className: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
  },
  miss: {
    label: "Miss",
    className: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
  },
  pending: {
    label: "Pending",
    className: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300",
  },
  expired: {
    label: "Expired",
    className: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300",
  },
};

export function OutcomeBadge({ status }: { status: string }) {
  const config = statusConfig[status] ?? statusConfig.pending;
  return (
    <Badge variant="outline" className={cn("border-transparent", config.className)}>
      {config.label}
    </Badge>
  );
}
