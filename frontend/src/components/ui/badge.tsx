import { cn } from "@/lib/utils";
import React from "react";

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?:
    | "default"
    | "secondary"
    | "success"
    | "warning"
    | "destructive"
    | "outline";
}

const variantStyles: Record<string, string> = {
  default: "bg-[var(--primary)] text-[var(--primary-foreground)]",
  secondary: "bg-[var(--secondary)] text-[var(--secondary-foreground)]",
  success:
    "bg-[var(--success)]/15 text-[var(--success)] border-[var(--success)]/30",
  warning:
    "bg-[var(--warning)]/15 text-[var(--warning)] border-[var(--warning)]/30",
  destructive:
    "bg-[var(--destructive)]/15 text-[var(--destructive)] border-[var(--destructive)]/30",
  outline: "border border-[var(--border)] text-[var(--foreground)]",
};

const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = "default", ...props }, ref) => (
    <span
      ref={ref}
      className={cn(
        "inline-flex items-center rounded-full border border-transparent px-2.5 py-0.5 text-xs font-semibold transition-colors",
        variantStyles[variant],
        className
      )}
      {...props}
    />
  )
);
Badge.displayName = "Badge";

export { Badge };
export type { BadgeProps };
