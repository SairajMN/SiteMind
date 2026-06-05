import { cva, type VariantProps } from "class-variance-authority";
import { forwardRef, type ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--stitch-accent-cyan)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--stitch-bg)] disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default:
          "bg-[var(--stitch-accent-cyan)] text-[var(--stitch-bg)] hover:brightness-110",
        secondary:
          "bg-[var(--stitch-surface-active)] text-[var(--stitch-text)] border border-[var(--stitch-border)] hover:bg-[var(--stitch-surface-hover)]",
        outline:
          "border border-[var(--stitch-border-strong)] bg-transparent text-[var(--stitch-text)] hover:bg-[var(--stitch-surface-hover)]",
        ghost:
          "text-[var(--stitch-text-muted)] hover:bg-[var(--stitch-surface-hover)] hover:text-[var(--stitch-text)]",
        destructive:
          "bg-[var(--stitch-error-dim)] text-[var(--stitch-error)] border border-[var(--stitch-error)]/30 hover:bg-[var(--stitch-error)]/20",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-11 rounded-md px-6",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button
      className={cn(buttonVariants({ variant, size, className }))}
      ref={ref}
      {...props}
    />
  ),
);
Button.displayName = "Button";

export { Button, buttonVariants };
