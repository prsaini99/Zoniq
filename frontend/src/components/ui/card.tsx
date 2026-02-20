/**
 * Card - A set of composable card sub-components for building content cards.
 *
 * Components:
 * - Card: The outer container with rounded borders, background, and shadow.
 *   Accepts an optional `hover` prop to enable lift-on-hover and gradient border effects.
 * - CardHeader: Top section with vertical spacing, typically holds title and description.
 * - CardTitle: Styled heading (h3) for the card.
 * - CardDescription: Muted paragraph text beneath the title.
 * - CardContent: Main body area with padding (no top padding to avoid double spacing).
 * - CardFooter: Bottom section with horizontal flex layout.
 *
 * All components use React.forwardRef for ref forwarding and accept standard HTML attributes.
 */
"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

// Card wrapper - the `hover` prop adds interactive lift and gradient border styles
const Card = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & {
    hover?: boolean;
  }
>(({ className, hover = false, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "rounded-xl border border-border bg-background-card text-foreground shadow-card",
      hover && "hover-lift gradient-border cursor-pointer",
      className
    )}
    {...props}
  />
));
Card.displayName = "Card";

// CardHeader - contains title and optional description with vertical spacing
const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col space-y-1.5 p-6", className)}
    {...props}
  />
));
CardHeader.displayName = "CardHeader";

// CardTitle - bold heading text for the card
const CardTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn(
      "text-xl font-semibold leading-none tracking-tight text-foreground",
      className
    )}
    {...props}
  />
));
CardTitle.displayName = "CardTitle";

// CardDescription - muted secondary text, typically used below CardTitle
const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn("text-sm text-foreground-muted", className)}
    {...props}
  />
));
CardDescription.displayName = "CardDescription";

// CardContent - main content area; uses pt-0 to avoid double padding with CardHeader
const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
));
CardContent.displayName = "CardContent";

// CardFooter - bottom area with horizontal flex layout for actions or metadata
const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex items-center p-6 pt-0", className)}
    {...props}
  />
));
CardFooter.displayName = "CardFooter";

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent };
