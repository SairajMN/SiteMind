import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { JobStatus } from "@/lib/api-client";

const statusConfig: Record<
  JobStatus | string,
  { label: string; variant: "default" | "secondary" | "success" | "warning" | "destructive" }
> = {
  queued: { label: "Queued", variant: "secondary" },
  running: { label: "Running", variant: "default" },
  completed: { label: "Completed", variant: "success" },
  failed: { label: "Failed", variant: "destructive" },
  blocked: { label: "Blocked", variant: "warning" },
};

export type StatusChipProps = {
  status: string;
  className?: string;
  pulse?: boolean;
};

export function StatusChip({ status, className, pulse }: StatusChipProps) {
  const config = statusConfig[status] ?? {
    label: status,
    variant: "secondary" as const,
  };

  return (
    <Badge
      variant={config.variant}
      className={cn(
        pulse && status === "running" && "animate-pulse",
        className,
      )}
    >
      <span
        className={cn(
          "mr-1.5 inline-block h-1.5 w-1.5 rounded-full",
          status === "running" && "bg-[var(--stitch-accent-cyan)]",
          status === "completed" && "bg-[var(--stitch-success)]",
          status === "failed" && "bg-[var(--stitch-error)]",
          status === "queued" && "bg-[var(--stitch-text-subtle)]",
          status === "blocked" && "bg-[var(--stitch-warning)]",
        )}
      />
      {config.label}
    </Badge>
  );
}
