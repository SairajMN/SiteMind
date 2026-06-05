import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export type ConfidenceBadgeProps = {
  value: number;
  className?: string;
  showPercent?: boolean;
  size?: "sm" | "md";
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
  size = "md",
}: ConfidenceBadgeProps) {
  const t = tier(value);
  const variant =
    t === "high" ? "success" : t === "medium" ? "warning" : "destructive";
  const label = showPercent
    ? `${Math.round(value * 100)}%`
    : value.toFixed(2);

  return (
    <Badge
      variant={variant}
      className={cn(
        "tabular-nums",
        size === "sm" && "text-[10px] px-1.5 py-0",
        className,
      )}
    >
      {label} confidence
    </Badge>
  );
}
