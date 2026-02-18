"use client";

import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

interface SpinnerProps {
  size?: "sm" | "md" | "lg";
  className?: string;
}

const sizes = {
  sm: "h-4 w-4",
  md: "h-6 w-6",
  lg: "h-8 w-8",
};

export function Spinner({ size = "md", className }: SpinnerProps) {
  return (
    <Loader2
      className={cn(
        "animate-spin text-primary",
        sizes[size],
        className
      )}
    />
  );
}

export function PageSpinner() {
  return (
    <div className="flex min-h-[400px] items-center justify-center">
      <Spinner size="lg" />
    </div>
  );
}

export function FullPageSpinner() {
  return (
    <div className="fixed inset-0 flex items-center justify-center bg-background">
      <div className="flex flex-col items-center gap-4">
        <Spinner size="lg" />
        <p className="text-sm text-foreground-muted">Loading...</p>
      </div>
    </div>
  );
}
