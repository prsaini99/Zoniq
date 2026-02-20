/**
 * Input - A styled, accessible form input component with built-in support for:
 * - Optional label above the input.
 * - Left and right icon slots.
 * - Password visibility toggle (show/hide eye icon).
 * - Error state with red border highlight and error message text.
 * - Helper text displayed below the input when there is no error.
 *
 * Uses React.forwardRef for ref forwarding (compatible with form libraries like react-hook-form).
 * Auto-generates an id via React.useId if none is provided, ensuring label-input association.
 */
"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { Eye, EyeOff } from "lucide-react";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      type,
      label,
      error,
      helperText,
      leftIcon,
      rightIcon,
      id,
      ...props
    },
    ref
  ) => {
    // Local state for toggling password visibility
    const [showPassword, setShowPassword] = React.useState(false);
    // Generate a stable unique id if none is provided
    const inputId = id || React.useId();
    const isPassword = type === "password";

    return (
      <div className="w-full space-y-2">
        {/* Optional label, linked to the input via htmlFor */}
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-foreground-muted"
          >
            {label}
          </label>
        )}
        <div className="relative group">
          {/* Left icon slot - changes color when input is focused */}
          {leftIcon && (
            <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-foreground-subtle group-focus-within:text-foreground-muted transition-colors">
              {leftIcon}
            </div>
          )}
          <input
            type={isPassword && showPassword ? "text" : type}
            id={inputId}
            className={cn(
              "flex h-11 w-full rounded-xl border bg-background-card px-4 py-2 text-sm text-foreground placeholder:text-foreground-subtle transition-all duration-200",
              "border-border focus:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/20",
              "hover:border-border-hover",
              "disabled:cursor-not-allowed disabled:opacity-50",
              leftIcon && "pl-10",
              (rightIcon || isPassword) && "pr-10",
              error && "border-error/50 focus:border-error focus:ring-error/20",
              className
            )}
            ref={ref}
            {...props}
          />
          {/* Password toggle button - switches between Eye and EyeOff icons */}
          {isPassword && (
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3.5 top-1/2 -translate-y-1/2 text-foreground-subtle hover:text-foreground-muted transition-colors"
              tabIndex={-1}
            >
              {showPassword ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
            </button>
          )}
          {/* Right icon slot (only rendered for non-password inputs) */}
          {!isPassword && rightIcon && (
            <div className="absolute right-3.5 top-1/2 -translate-y-1/2 text-foreground-subtle">
              {rightIcon}
            </div>
          )}
        </div>
        {/* Error message (takes priority over helper text) */}
        {error && (
          <p className="text-xs text-error font-medium">{error}</p>
        )}
        {/* Helper text shown when there is no error */}
        {!error && helperText && (
          <p className="text-xs text-foreground-subtle">{helperText}</p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";

export { Input };
