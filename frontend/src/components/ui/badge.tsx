import { cva, type VariantProps } from "class-variance-authority";
import { type HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors",
  {
    variants: {
      variant: {
        default:
          "border-[var(--stitch-border-accent)] bg-[var(--stitch-accent-cyan-dim)] text-[var(--stitch-accent-cyan)]",
        secondary:
          "border-[var(--stitch-border)] bg-[var(--stitch-surface-active)] text-[var(--stitch-text-muted)]",
        violet:
          "border-[var(--stitch-accent-violet)]/30 bg-[var(--stitch-accent-violet-dim)] text-[var(--stitch-accent-violet)]",
        success:
          "border-[var(--stitch-success)]/30 bg-[var(--stitch-success-dim)] text-[var(--stitch-success)]",
        warning:
          "border-[var(--stitch-warning)]/30 bg-[var(--stitch-warning-dim)] text-[var(--stitch-warning)]",
        destructive:
          "border-[var(--stitch-error)]/30 bg-[var(--stitch-error-dim)] text-[var(--stitch-error)]",
        outline: "border-[var(--stitch-border-strong)] text-[var(--stitch-text-muted)]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

export interface BadgeProps
  extends HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
