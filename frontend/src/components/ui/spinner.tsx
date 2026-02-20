/**
 * Spinner components - Three loading spinner variants for different use cases.
 *
 * - Spinner: An inline spinning icon (Loader2 from lucide-react) available in
 *   three sizes (sm, md, lg). Accepts optional className for custom styling.
 *
 * - PageSpinner: A vertically centered spinner intended for use as a page-level
 *   loading indicator within a container (min-height 400px).
 *
 * - FullPageSpinner: A fixed full-screen overlay spinner with a "Loading..." label,
 *   used for blocking transitions (e.g., initial app load, auth checks).
 */
"use client";

import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

interface SpinnerProps {
  size?: "sm" | "md" | "lg";
  className?: string;
}

// Size-to-class mapping for the spinner icon
const sizes = {
  sm: "h-4 w-4",
  md: "h-6 w-6",
  lg: "h-8 w-8",
};

// Inline spinner - renders a spinning Loader2 icon at the specified size
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

// Page-level spinner - centered within a flex container with a minimum height
export function PageSpinner() {
  return (
    <div className="flex min-h-[400px] items-center justify-center">
      <Spinner size="lg" />
    </div>
  );
}

// Full-screen spinner overlay - covers the entire viewport with a loading message
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
