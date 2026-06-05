import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export type ConfidenceBadgeProps = {
  value: number;
  className?: string;
  showPercent?: boolean;
};

function tier(value: number): "high" | "medium" | "low" {
  if (value >= 0.8) return "high";
  if (value >= 0.5) return "medium";
  return "low";
}

export function ConfidenceBadge({
  value,
  className,
  showPercent = true,
}: ConfidenceBadgeProps) {
  const t = tier(value);
  const variant =
    t === "high" ? "success" : t === "medium" ? "warning" : "destructive";
  const label = showPercent
    ? `${Math.round(value * 100)}%`
    : value.toFixed(2);

  return (
    <Badge variant={variant} className={cn("tabular-nums", className)}>
      {label} confidence
    </Badge>
  );
}
