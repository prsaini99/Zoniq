/**
 * Button - A versatile, accessible button component with multiple visual variants and sizes.
 *
 * Built with class-variance-authority (cva) for variant-based styling
 * and React.forwardRef for ref forwarding.
 *
 * Variants:
 * - default: Primary filled button with glow shadow.
 * - secondary: Elevated background with border.
 * - outline: Transparent with border only.
 * - ghost: No background, text-only with hover effect.
 * - link: Styled as an underlined text link.
 * - destructive: Red/error filled button.
 * - success: Green filled button.
 *
 * Sizes: default, sm, lg, xl, icon.
 *
 * Extra props:
 * - isLoading: shows a spinning Loader2 icon and disables the button.
 * - leftIcon / rightIcon: optional icon elements placed before/after children.
 */
"use client";

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

// Define button variant and size styles using class-variance-authority
const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm font-semibold tracking-tight transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-50 cursor-pointer active:scale-[0.97]",
  {
    variants: {
      variant: {
        default:
          "bg-primary text-white hover:bg-primary-hover shadow-glow-sm hover:shadow-glow",
        secondary:
          "bg-background-elevated text-foreground border border-border hover:border-border-hover hover:bg-background-soft",
        outline:
          "border border-border text-foreground bg-transparent hover:bg-foreground/5 hover:border-foreground/20",
        ghost:
          "text-foreground-muted hover:text-foreground hover:bg-foreground/5",
        link: "text-primary underline-offset-4 hover:underline",
        destructive:
          "bg-error text-white hover:bg-error/90 shadow-md",
        success:
          "bg-success text-white hover:bg-success/90 shadow-md",
      },
      size: {
        default: "h-10 px-5 py-2",
        sm: "h-9 px-3.5 text-xs",
        lg: "h-12 px-7 text-base",
        xl: "h-14 px-9 text-lg rounded-2xl",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
  VariantProps<typeof buttonVariants> {
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

// Button component with forwardRef for composability with external libraries
const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant,
      size,
      isLoading,
      leftIcon,
      rightIcon,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={disabled || isLoading}
        {...props}
      >
        {/* Show spinner when loading, otherwise show the optional left icon */}
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          leftIcon
        )}
        {children}
        {/* Right icon is hidden during loading state */}
        {!isLoading && rightIcon}
      </button>
    );
  }
);

Button.displayName = "Button";

export { Button, buttonVariants };
