"use client";

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors",
  {
    variants: {
      variant: {
        default: "bg-primary-light text-primary",
        secondary: "bg-background-elevated text-foreground-muted border border-border",
        success: "bg-green-500/10 text-green-500",
        warning: "bg-yellow-500/10 text-yellow-500",
        error: "bg-red-500/10 text-red-500",
        info: "bg-blue-500/10 text-blue-500",
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

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

// Event status badge helper
export function StatusBadge({ status }: { status: string }) {
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
