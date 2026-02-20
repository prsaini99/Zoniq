/**
 * Badge - A small label/tag component used to display statuses, categories, or metadata.
 *
 * Built with class-variance-authority (cva) for variant-based styling.
 *
 * Variants:
 * - default: primary-colored (used for categories).
 * - secondary: muted background.
 * - success: green for positive states (published, available).
 * - warning: amber for caution states (coming soon, locked, sold out).
 * - error: red for negative states (cancelled, blocked).
 * - info: blue for informational states (completed, booked).
 * - outline: bordered with no fill.
 *
 * Also exports StatusBadge, a convenience wrapper that maps a status string
 * (e.g. "draft", "published") to the appropriate Badge variant and label.
 */
"use client";

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

// Define badge variant styles using class-variance-authority
const badgeVariants = cva(
  "inline-flex items-center rounded-lg px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wider transition-colors",
  {
    variants: {
      variant: {
        default: "bg-primary/15 text-primary border border-primary/20",
        secondary: "bg-background-elevated text-foreground-muted border border-border",
        success: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20",
        warning: "bg-amber-500/10 text-amber-400 border border-amber-500/20",
        error: "bg-red-500/10 text-red-400 border border-red-500/20",
        info: "bg-blue-500/10 text-blue-400 border border-blue-500/20",
        outline: "border border-border text-foreground-muted",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
  VariantProps<typeof badgeVariants> { }

// Core Badge component - renders a styled div with the appropriate variant classes
function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

/**
 * StatusBadge - Convenience component that maps a status string to a
 * Badge variant and human-readable label. Useful for event/seat statuses.
 */
export function StatusBadge({ status }: { status: string }) {
  // Map status keys to Badge variant names
  const variants: Record<string, VariantProps<typeof badgeVariants>["variant"]> = {
    draft: "secondary",
    published: "success",
    cancelled: "error",
    completed: "info",
    soldout: "warning",
    available: "success",
    locked: "warning",
    booked: "info",
    blocked: "error",
  };

  // Map status keys to display labels
  const labels: Record<string, string> = {
    draft: "Draft",
    published: "Published",
    cancelled: "Cancelled",
    completed: "Completed",
    soldout: "Sold Out",
    available: "Available",
    locked: "Locked",
    booked: "Booked",
    blocked: "Blocked",
  };

  return (
    <Badge variant={variants[status] || "secondary"}>
      {labels[status] || status}
    </Badge>
  );
}

export { Badge, badgeVariants };
